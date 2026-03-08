import os
import glob
import json
import time
import logging
import concurrent.futures
import threading
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

logging.getLogger("pypdf").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

PDF_DIR = BASE_DIR / "storage" / "pdfs"
DB_DIR = str(BASE_DIR / "storage" / "chroma_db")

# ---------------------------------------------------------------------------
# API key loading
# ---------------------------------------------------------------------------

def _load_keys(prefix: str, limit: int = 10) -> list[str]:
    keys = []
    for i in range(1, limit):
        val = os.getenv(f"{prefix}{i}")
        if val:
            keys.append(val)
    return keys


GOOGLE_API_KEYS = _load_keys("GEMINI")
GROQ_API_KEYS = _load_keys("GROQ")

logger.info("Loaded %d GEMINI keys, %d GROQ keys", len(GOOGLE_API_KEYS), len(GROQ_API_KEYS))

# ---------------------------------------------------------------------------
# Rate-limiting key manager
# ---------------------------------------------------------------------------

class KeyManager:
    """Round-robin key dispenser with per-key cooldown."""

    def __init__(self, keys: list[str], min_interval: float = 4.0):
        self.keys = keys
        self.min_interval = min_interval
        self._last_used: dict[str, float] = {k: 0.0 for k in keys}
        self._lock = threading.Lock()
        self._index = 0

    def get_key(self) -> str:
        with self._lock:
            key = self.keys[self._index]
            self._index = (self._index + 1) % len(self.keys)
            now = time.time()
            wait = max(0.0, self.min_interval - (now - self._last_used[key]))
            self._last_used[key] = now + wait

        if wait > 0:
            time.sleep(wait)
        return key


google_key_manager = KeyManager(GOOGLE_API_KEYS, min_interval=4.0) if GOOGLE_API_KEYS else None
groq_key_manager = KeyManager(GROQ_API_KEYS, min_interval=2.0) if GROQ_API_KEYS else None

# ---------------------------------------------------------------------------
# Valid departments / centres (used in the prompt)
# ---------------------------------------------------------------------------

VALID_DEPARTMENTS = [
    "ARTIFICIAL INTELLIGENCE AND DATA ENGINEERING",
    "ARCHITECTURE AND PLANNING",
    "CHEMICAL ENGINEERING",
    "CIVIL ENGINEERING",
    "COMPUTER SCIENCE AND ENGINEERING",
    "ELECTRICAL ENGINEERING",
    "ELECTRONICS AND COMMUNICATION ENGINEERING",
    "MECHANICAL ENGINEERING",
    "METALLURGICAL AND MATERIALS ENGINEERING",
    "CHEMISTRY",
    "MATHEMATICS",
    "PHYSICS",
    "MANAGEMENT STUDIES",
]

VALID_CENTRES = [
    "CENTRE FOR ENERGY AND ENVIRONMENT",
    "NATIONAL CENTRE FOR DISASTER MITIGATION AND MANAGEMENT",
    "MATERIALS RESEARCH CENTRE",
]

# ---------------------------------------------------------------------------
# Pydantic schema & prompt
# ---------------------------------------------------------------------------

class DocumentMetadata(BaseModel):
    year: str = Field(
        description=(
            "Academic or calendar year the document pertains to (e.g. '2024', '2024-25'). "
            "Use 'Unknown' only if no year can be reasonably inferred."
        )
    )
    dept: str = Field(
        description=(
            "The department or centre this document belongs to, "
            "mapped EXACTLY to one of the allowed names. "
            "Use 'Institute' for institute-wide docs, 'Hostel' for hostel-related, "
            "'Mess' for mess-related, or 'Unknown' if truly unidentifiable."
        )
    )
    doc_type: str = Field(
        description=(
            "Document category. Must be one of: "
            "'Syllabus', 'Notice', 'Circular', 'Examination Schedule', "
            "'Result', 'Tender', 'Minutes', 'Report', 'Form', 'Regulation', "
            "'Calendar', 'Admission', 'Placement', 'Newsletter', 'Other'."
        )
    )
    audience: str = Field(
        description=(
            "Primary target audience. E.g. 'B.Tech Students', 'M.Tech Students', "
            "'PhD Scholars', 'Faculty', 'Staff', 'All Students', 'General Public'. "
            "Be as specific as the text allows."
        )
    )
    semester: str = Field(
        description=(
            "Semester or term if mentioned (e.g. 'Odd Semester', 'Even Semester', "
            "'1st Semester', '5th Semester'). Use 'Unknown' if not mentioned."
        )
    )
    title: str = Field(
        description=(
            "A concise, descriptive title for the document (max 15 words). "
            "Include the subject, department, and year if available. "
            "E.g. 'CSE B.Tech 5th Semester Syllabus 2024-25'."
        )
    )
    summary: str = Field(
        description=(
            "A 2-4 sentence summary of the document's content and purpose. "
            "Mention the department, the type of information, key dates if any, "
            "and who it is relevant to. This will be used for search, so include "
            "the most important terms and context a student or faculty member "
            "would search for."
        )
    )
    keywords: str = Field(
        description=(
            "Comma-separated list of 5-15 important search keywords and phrases from "
            "the document. Include: subject names, course codes, professor names, "
            "specific dates, regulation numbers, or any other distinctive terms. "
            "E.g. 'CS101, Data Structures, mid-semester, Prof. Sharma, 2024-25'."
        )
    )


_parser = JsonOutputParser(pydantic_object=DocumentMetadata)

_PROMPT_TEMPLATE = """You are a metadata extraction assistant for MNIT Jaipur's document management system.
Carefully read the provided text extracted from a PDF document and produce structured metadata.

RULES:
1. **dept** must be mapped to one of the EXACT names below, even if the document uses
   abbreviations or informal names:
   - 'CS' / 'CSE' / 'Comp Sc'  → 'COMPUTER SCIENCE AND ENGINEERING'
   - 'AIDE' / 'AI'              → 'ARTIFICIAL INTELLIGENCE AND DATA ENGINEERING'
   - 'EE'                       → 'ELECTRICAL ENGINEERING'
   - 'ECE'                      → 'ELECTRONICS AND COMMUNICATION ENGINEERING'
   - 'ME'                       → 'MECHANICAL ENGINEERING'
   - 'CE'                       → 'CIVIL ENGINEERING'
   - 'ChE'                      → 'CHEMICAL ENGINEERING'
   - 'Meta' / 'MME'             → 'METALLURGICAL AND MATERIALS ENGINEERING'
   - 'Arch'                     → 'ARCHITECTURE AND PLANNING'
   Use 'Institute' for campus-wide documents, 'Hostel' for hostel notices,
   'Mess' for mess/food notices, or 'Unknown' only if truly unidentifiable.

2. **doc_type** must be one of the allowed categories listed in the schema.

3. **summary** should be search-friendly — include the most important nouns, names,
   dates, and context so that someone searching for this document can find it.

4. **keywords** should cover terms that don't already appear in the title or summary
   but are still important for search (course codes, regulation numbers, names, etc.).

Valid Departments:
{valid_departments}

Valid Centres:
{valid_centres}

{format_instructions}

--- TEXT START ---
{text}
--- TEXT END ---
"""

_prompt = PromptTemplate(
    template=_PROMPT_TEMPLATE,
    input_variables=["text"],
    partial_variables={
        "format_instructions": _parser.get_format_instructions(),
        "valid_departments": json.dumps(VALID_DEPARTMENTS, indent=2),
        "valid_centres": json.dumps(VALID_CENTRES, indent=2),
    },
)

# ---------------------------------------------------------------------------
# LLM chain helpers
# ---------------------------------------------------------------------------

def _build_chain(api_key: str, provider: str):
    """Build a prompt | llm | parser chain for the given provider."""
    if provider == "groq":
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=api_key)
    else:
        llm = ChatGoogleGenerativeAI(
            model="gemma-3-27b-it", temperature=0, google_api_key=api_key,
        )
    return _prompt | llm | _parser


_FALLBACK_METADATA: dict = {
    "year": "Unknown",
    "dept": "Unknown",
    "doc_type": "Unknown",
    "audience": "Unknown",
    "semester": "Unknown",
    "title": "Unknown",
    "summary": "Metadata extraction failed.",
    "keywords": "",
}


def _try_provider(text: str, key_mgr: KeyManager, provider: str, retries: int = 3) -> dict | None:
    """Attempt extraction with a given provider. Returns dict on success, None on failure."""
    if key_mgr is None:
        return None

    for attempt in range(retries):
        key = key_mgr.get_key()
        chain = _build_chain(key, provider)
        try:
            return chain.invoke({"text": text})
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                logger.warning("[%s] Rate-limited (key …%s). Retry %d/%d", provider, key[-4:], attempt + 1, retries)
                time.sleep(3)
            elif "503" in err:
                logger.warning("[%s] Service unavailable. Retry %d/%d", provider, attempt + 1, retries)
                time.sleep(5)
            else:
                logger.error("[%s] %s", provider, e)
                break  # non-transient error — stop retrying this provider
    return None


def extract_metadata(text: str) -> dict:
    """
    Extract metadata from document text.
    Strategy: try Groq first (fast + generous limits), fall back to Gemma via Google.
    Uses the first ~5000 chars (roughly first 3 pages) for better context.
    """
    excerpt = text[:5000]

    # 1) Try Groq
    result = _try_provider(excerpt, groq_key_manager, "groq")
    if result is not None:
        return result

    # 2) Fallback to Google / Gemma
    logger.info("Groq failed — falling back to Gemma.")
    result = _try_provider(excerpt, google_key_manager, "gemini")
    if result is not None:
        return result

    logger.error("All providers failed for metadata extraction.")
    return dict(_FALLBACK_METADATA)


# ---------------------------------------------------------------------------
# Indexing Service
# ---------------------------------------------------------------------------

class IndexingService:
    """
    Processes PDFs from *pdf_dir*, extracts metadata via LLM, chunks the text,
    and upserts into a ChromaDB vector store.

    Tracks each document's `last_modified` timestamp so unchanged files are
    skipped on subsequent runs and changed files are re-indexed.
    """

    def __init__(
        self,
        pdf_dir: str | Path = PDF_DIR,
        db_dir: str = DB_DIR,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_workers: int | None = None,
        embedding_google_api_key: str | None = None,
    ):
        self.pdf_dir = Path(pdf_dir)
        self.db_dir = db_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Workers default to number of available API keys (Groq keys drive throughput)
        self.max_workers = max_workers or max(len(GROQ_API_KEYS), len(GOOGLE_API_KEYS), 1)

        # Embedding model — always Google
        emb_key = embedding_google_api_key or (GOOGLE_API_KEYS[0] if GOOGLE_API_KEYS else None)
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=emb_key,
        )

        # Persistent vector store
        self._vectorstore = Chroma(
            persist_directory=self.db_dir,
            embedding_function=self._embeddings,
            collection_name="mnit_docs",
        )

        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        # ---- progress tracking state ----
        self._status: str = "idle"           # idle | running | completed | error
        self._total_pdfs: int = 0
        self._pdfs_processed: int = 0
        self._pdfs_indexed: int = 0          # actually produced new chunks
        self._pdfs_skipped: int = 0          # unchanged, skipped
        self._chunks_total: int = 0          # chunks waiting to be embedded
        self._chunks_embedded: int = 0       # chunks sent to vector store so far
        self._current_pdf: str = ""          # filename currently being processed
        self._current_phase: str = ""        # "processing" | "embedding" | ""
        self._recent_files: list[str] = []   # last 5 indexed filenames
        self._progress_lock = threading.Lock()

    # ---- progress & status helpers ----

    def get_progress(self) -> dict:
        """Return a thread-safe snapshot of current indexing progress."""
        with self._progress_lock:
            return {
                "status": self._status,
                "phase": self._current_phase,
                "total_pdfs": self._total_pdfs,
                "pdfs_processed": self._pdfs_processed,
                "pdfs_indexed": self._pdfs_indexed,
                "pdfs_skipped": self._pdfs_skipped,
                "chunks_total": self._chunks_total,
                "chunks_embedded": self._chunks_embedded,
                "current_pdf": self._current_pdf,
                "recent_files": list(self._recent_files[-5:]),
            }

    def get_db_status(self) -> dict:
        """Return info about the current state of the ChromaDB collection."""
        try:
            collection = self._vectorstore._collection
            count = collection.count()

            # Get unique source files
            all_meta = collection.get(include=["metadatas"])
            metadatas = all_meta.get("metadatas", []) if all_meta else []
            sources = set()
            departments = set()
            doc_types = set()
            for m in metadatas:
                if m.get("source"):
                    sources.add(m["source"])
                if m.get("dept") and m["dept"] != "Unknown":
                    departments.add(m["dept"])
                if m.get("doc_type") and m["doc_type"] != "Unknown":
                    doc_types.add(m["doc_type"])

            # DB file size on disk
            db_path = Path(self.db_dir)
            size_bytes = sum(f.stat().st_size for f in db_path.rglob("*") if f.is_file()) if db_path.exists() else 0

            return {
                "collection_name": "mnit_docs",
                "total_chunks": count,
                "total_documents": len(sources),
                "departments": sorted(departments),
                "doc_types": sorted(doc_types),
                "db_size_mb": round(size_bytes / (1024 * 1024), 2),
                "db_path": self.db_dir,
            }
        except Exception as e:
            logger.error("Failed to get DB status: %s", e)
            return {"error": str(e)}

    # ---- last-modified helpers ----

    def _get_indexed_mtime(self, source_path: str) -> float | None:
        """
        Query ChromaDB for any chunk whose metadata['source'] matches *source_path*.
        Return its stored `last_modified` timestamp, or None if not indexed.
        """
        results = self._vectorstore.get(
            where={"source": source_path},
            limit=1,
            include=["metadatas"],
        )
        if results and results["metadatas"]:
            return results["metadatas"][0].get("last_modified")
        return None

    def _delete_by_source(self, source_path: str) -> int:
        """Delete all chunks for a given source file. Returns count deleted."""
        existing = self._vectorstore.get(where={"source": source_path}, include=[])
        ids = existing.get("ids", [])
        if ids:
            self._vectorstore.delete(ids=ids)
        return len(ids)

    # ---- single-PDF processing ----

    def _process_pdf(self, pdf_path: str) -> list[Document]:
        """
        Load a PDF, extract metadata, and return chunked Documents ready for
        indexing. Returns an empty list if the file is unchanged or on error.
        """
        filename = os.path.basename(pdf_path)
        file_mtime = os.path.getmtime(pdf_path)

        with self._progress_lock:
            self._current_pdf = filename

        # Check if already indexed with the same mtime
        indexed_mtime = self._get_indexed_mtime(pdf_path)
        if indexed_mtime is not None and float(indexed_mtime) == file_mtime:
            logger.info("Skipping (unchanged): %s", filename)
            return []

        # If previously indexed with a different mtime, delete old chunks
        if indexed_mtime is not None:
            deleted = self._delete_by_source(pdf_path)
            logger.info("Re-indexing (changed): %s — removed %d old chunks", filename, deleted)

        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            if not pages:
                return []

            # Use text from first 3 pages for metadata extraction (more context)
            meta_text = "\n\n".join(p.page_content for p in pages[:3])
            metadata = extract_metadata(meta_text)

            # Ensure metadata values are flat (str/int/float/bool only)
            flat_metadata: dict = {}
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    flat_metadata[k] = v
                elif v is None:
                    flat_metadata[k] = "Unknown"
                else:
                    flat_metadata[k] = str(v)

            flat_metadata["source"] = pdf_path
            flat_metadata["filename"] = filename
            flat_metadata["last_modified"] = file_mtime
            flat_metadata["total_pages"] = len(pages)

            # Tag every page with the document-level metadata + page number
            for i, page in enumerate(pages):
                # Replace metadata entirely to avoid nested dicts from PyPDFLoader
                page.metadata = {**flat_metadata, "page": i + 1}

            # Chunk the pages
            chunks = self._text_splitter.split_documents(pages)

            # Prepend contextual header to each chunk so the embedding captures
            # document-level info even in the middle of a long PDF.
            context_header = (
                f"[Title: {flat_metadata.get('title', '')} | "
                f"Dept: {flat_metadata.get('dept', '')} | "
                f"Type: {flat_metadata.get('doc_type', '')} | "
                f"Year: {flat_metadata.get('year', '')}]\n"
            )
            for chunk in chunks:
                chunk.page_content = context_header + chunk.page_content

            # Final safety net: strip any remaining complex metadata types
            chunks = filter_complex_metadata(chunks)

            logger.info("Processed %s → %d chunks", filename, len(chunks))
            return chunks

        except Exception as e:
            logger.error("Failed to process %s: %s", filename, e)
            return []

    # ---- public entry point ----

    def index_all(self) -> dict:
        """
        Scan *pdf_dir*, process new/changed PDFs, and upsert into ChromaDB.

        Returns a summary dict:
            {
                "total_pdfs": int,
                "indexed": int,
                "skipped_unchanged": int,
                "chunks_added": int,
            }
        """
        if not self.pdf_dir.exists():
            logger.error("PDF directory does not exist: %s", self.pdf_dir)
            return {"error": f"Directory not found: {self.pdf_dir}"}

        pdf_files = glob.glob(str(self.pdf_dir / "*.pdf"))
        total = len(pdf_files)
        logger.info("Found %d PDFs in %s — processing with %d workers", total, self.pdf_dir, self.max_workers)

        with self._progress_lock:
            self._status = "running"
            self._total_pdfs = total
            self._pdfs_processed = 0
            self._pdfs_indexed = 0
            self._pdfs_skipped = 0
            self._chunks_total = 0
            self._chunks_embedded = 0
            self._current_phase = "processing"
            self._recent_files = []

        all_chunks: list[Document] = []
        indexed_count = 0
        lock = threading.Lock()

        def _worker(path: str):
            nonlocal indexed_count
            chunks = self._process_pdf(path)
            fname = os.path.basename(path)
            with lock:
                if chunks:
                    all_chunks.extend(chunks)
                    indexed_count += 1
                    with self._progress_lock:
                        self._pdfs_indexed += 1
                        self._recent_files.append(fname)
                else:
                    with self._progress_lock:
                        self._pdfs_skipped += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(_worker, p): p for p in pdf_files}
            done = 0
            for fut in concurrent.futures.as_completed(futures):
                done += 1
                exc = fut.exception()
                if exc:
                    logger.error("%s raised: %s", os.path.basename(futures[fut]), exc)
                with self._progress_lock:
                    self._pdfs_processed = done
                if done % 5 == 0 or done == total:
                    logger.info("Progress: %d / %d PDFs processed", done, total)

        skipped = total - indexed_count
        logger.info("Indexing %d new chunks from %d PDFs (%d unchanged, skipped)", len(all_chunks), indexed_count, skipped)

        if all_chunks:
            with self._progress_lock:
                self._current_phase = "embedding"
                self._chunks_total = len(all_chunks)
                self._chunks_embedded = 0
            self._add_documents_batched(all_chunks, batch_size=50)
            logger.info("Successfully saved %d chunks to %s", len(all_chunks), self.db_dir)

        with self._progress_lock:
            self._status = "completed"
            self._current_phase = ""
            self._current_pdf = ""

        return {
            "total_pdfs": total,
            "indexed": indexed_count,
            "skipped_unchanged": skipped,
            "chunks_added": len(all_chunks),
        }

    def _add_documents_batched(self, docs: list[Document], batch_size: int = 50, retries: int = 3):
        """Add documents to the vector store in small batches with retry logic."""
        total = len(docs)
        for i in range(0, total, batch_size):
            batch = docs[i : i + batch_size]
            for attempt in range(1, retries + 1):
                try:
                    self._vectorstore.add_documents(batch)
                    with self._progress_lock:
                        self._chunks_embedded = min(i + batch_size, total)
                    logger.info("Embedded batch %d–%d / %d", i + 1, min(i + batch_size, total), total)
                    break
                except Exception as e:
                    logger.warning("Batch %d–%d failed (attempt %d/%d): %s", i + 1, min(i + batch_size, total), attempt, retries, e)
                    if attempt < retries:
                        time.sleep(5 * attempt)  # back off: 5s, 10s, 15s
                    else:
                        raise
            # Small delay between batches to stay within rate limits
            time.sleep(2)