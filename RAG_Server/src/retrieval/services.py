import os
import json
import logging
import time
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths & env
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DB_DIR = str(BASE_DIR / "storage" / "chroma_db")

# ---------------------------------------------------------------------------
# API key helpers (mirrors indexing/services.py)
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

# ---------------------------------------------------------------------------
# Valid metadata values (shared with indexing)
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

VALID_DOC_TYPES = [
    "Syllabus", "Notice", "Circular", "Examination Schedule",
    "Result", "Tender", "Minutes", "Report", "Form", "Regulation",
    "Calendar", "Admission", "Placement", "Newsletter", "Other",
]

# All known dept-like values (departments + centres + special)
ALL_DEPT_VALUES = VALID_DEPARTMENTS + VALID_CENTRES + ["Institute", "Hostel", "Mess"]


# ---------------------------------------------------------------------------
# LLM factory — Groq first, Gemini 2.5 flash fallback 
# ---------------------------------------------------------------------------

def _get_llm(provider: str = "groq", api_key: str | None = None):
    """Return a ChatModel instance for the given provider."""
    if provider == "groq":
        key = api_key or (GROQ_API_KEYS[0] if GROQ_API_KEYS else None)
        if not key:
            raise ValueError("No GROQ API key available")
        return ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=key)
    else:
        key = api_key or (GOOGLE_API_KEYS[0] if GOOGLE_API_KEYS else None)
        if not key:
            raise ValueError("No GEMINI API key available")
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", temperature=0, google_api_key=key,
        )


def _invoke_with_fallback(chain_builder, invoke_input: dict, retries: int = 2):
    """
    Try invoking a chain built with Groq; on failure fall back to Gemini 2.5 flash.
    *chain_builder* is a callable(llm) -> chain.
    """
    for provider, keys in [("groq", GROQ_API_KEYS), ("gemini", GOOGLE_API_KEYS)]:
        if not keys:
            continue
        for attempt in range(retries):
            try:
                llm = _get_llm(provider, keys[attempt % len(keys)])
                chain = chain_builder(llm)
                return chain.invoke(invoke_input)
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    logger.warning("[%s] Rate-limited, retry %d/%d", provider, attempt + 1, retries)
                    time.sleep(2)
                elif "503" in err:
                    logger.warning("[%s] Unavailable, retry %d/%d", provider, attempt + 1, retries)
                    time.sleep(3)
                else:
                    logger.error("[%s] %s", provider, e)
                    break  # non-transient → try next provider
    return None


# ===================================================================
# Retrieval Service
# ===================================================================

class RetrievalService:
    """
    RAG retrieval service for MNIT documents.

    Pipeline:
        1. Query analysis  → extract metadata filters (dept, year, doc_type)
        2. Multi-query gen → 3 query variants for vocabulary coverage
        3. Metadata-filtered vector search + BM25 keyword search
        4. Reciprocal Rank Fusion (merge all result lists)
        5. LLM reranking   → score each candidate 0–1
        6. Deduplicate by source PDF and return file-level results
    """

    def __init__(
        self,
        db_dir: str = DB_DIR,
        embedding_google_api_key: str | None = None,
    ):
        # Embeddings — always Google
        emb_key = embedding_google_api_key or (GOOGLE_API_KEYS[0] if GOOGLE_API_KEYS else None)
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=emb_key,
        )

        # Vector store (must match indexing service's collection)
        self._vectorstore = Chroma(
            persist_directory=db_dir,
            embedding_function=self._embeddings,
            collection_name="mnit_docs",
        )
        doc_count = self._vectorstore._collection.count()
        logger.info("Vector store loaded: %d chunks", doc_count)

        # BM25 in-memory index
        self._bm25: BM25Retriever | None = None
        self._build_bm25_index()

        # Pre-build prompt templates (stateless — LLM instance injected at call time)
        self._query_analysis_prompt = self._make_query_analysis_prompt()
        self._multi_query_prompt = self._make_multi_query_prompt()
        self._rerank_prompt = self._make_rerank_prompt()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _build_bm25_index(self) -> None:
        """Fetch all docs from ChromaDB into an in-memory BM25 index."""
        try:
            data = self._vectorstore.get()
            if not data or not data["documents"]:
                logger.warning("No documents in vector store — BM25 disabled")
                return
            docs = [
                Document(page_content=text, metadata=meta)
                for text, meta in zip(data["documents"], data["metadatas"] or [{}] * len(data["documents"]))
            ]
            self._bm25 = BM25Retriever.from_documents(docs)
            logger.info("BM25 index built: %d documents", len(docs))
        except Exception as e:
            logger.error("Failed to build BM25 index: %s", e)

    # ------------------------------------------------------------------
    # Prompt factories
    # ------------------------------------------------------------------

    @staticmethod
    def _make_query_analysis_prompt() -> PromptTemplate:
        """
        Analyses the user query to extract structured metadata filters.
        This is the key stage that enables metadata pre-filtering.
        """

        class QueryFilters(BaseModel):
            dept: Optional[str] = Field(
                default=None,
                description=(
                    "Department or centre mentioned in the query, mapped to the EXACT "
                    "official name. null if none mentioned."
                ),
            )
            year: Optional[str] = Field(
                default=None,
                description="Academic year (e.g. '2024', '2024-25'). null if not mentioned.",
            )
            doc_type: Optional[str] = Field(
                default=None,
                description=(
                    "Document type. Must be one of: " + ", ".join(VALID_DOC_TYPES) + ". null if not mentioned."
                ),
            )
            semester: Optional[str] = Field(
                default=None,
                description="Semester if mentioned (e.g. 'Odd Semester', '5th Semester'). null if not mentioned.",
            )

        parser = JsonOutputParser(pydantic_object=QueryFilters)

        template = """You are a query analysis assistant for MNIT Jaipur's document search system.
Given the user's query, extract any metadata filters that can narrow down the search.

DEPARTMENT MAPPING (use exact names):
- 'CS' / 'CSE' / 'Comp Sc'  → 'COMPUTER SCIENCE AND ENGINEERING'
- 'AIDE' / 'AI'              → 'ARTIFICIAL INTELLIGENCE AND DATA ENGINEERING'
- 'EE'                       → 'ELECTRICAL ENGINEERING'
- 'ECE'                      → 'ELECTRONICS AND COMMUNICATION ENGINEERING'
- 'ME' / 'Mech'              → 'MECHANICAL ENGINEERING'
- 'CE'                       → 'CIVIL ENGINEERING'
- 'ChE'                      → 'CHEMICAL ENGINEERING'
- 'Meta' / 'MME'             → 'METALLURGICAL AND MATERIALS ENGINEERING'
- 'Arch'                     → 'ARCHITECTURE AND PLANNING'
- Institute-level            → 'Institute'
- Hostel-related             → 'Hostel'
- Mess/food-related          → 'Mess'

DOC TYPE must be one of: {valid_doc_types}

Only set a field if the query CLEARLY specifies it. Do NOT guess.
If unsure, leave the field as null.

{format_instructions}

Query: {query}
"""
        return PromptTemplate(
            template=template,
            input_variables=["query"],
            partial_variables={
                "format_instructions": parser.get_format_instructions(),
                "valid_doc_types": json.dumps(VALID_DOC_TYPES),
            },
        )

    @staticmethod
    def _make_multi_query_prompt() -> PromptTemplate:
        class MultiQuery(BaseModel):
            queries: List[str] = Field(description="List of 3 alternative versions of the user query")

        parser = JsonOutputParser(pydantic_object=MultiQuery)

        template = """You are an AI assistant optimizing queries for an academic document retrieval system at MNIT (Malaviya National Institute of Technology).

Generate 3 different versions of the user's question to improve retrieval.

TERMINOLOGY RULES:
1. Replace generic terms with formal academic terminology:
   - 'Teachers' / 'Professors' → 'Faculty'
   - 'College' / 'University' / 'NIT' → 'Institute' or 'MNIT'
   - 'Classes' → 'Lectures'
   - 'Exams' → 'Examinations'
2. STRICTLY standardize Department names using the EXACT full name:
{valid_departments}
3. Centre names must use the EXACT full name:
{valid_centres}
4. If no specific department is mentioned, use 'Institute' context.
5. Include at least one query that uses different synonyms or related terms
   (e.g. if user asks for 'syllabus', also try 'curriculum' or 'course structure').

Original Question: {question}

{format_instructions}
"""
        return PromptTemplate(
            template=template,
            input_variables=["question"],
            partial_variables={
                "format_instructions": parser.get_format_instructions(),
                "valid_departments": json.dumps(VALID_DEPARTMENTS),
                "valid_centres": json.dumps(VALID_CENTRES),
            },
        )

    @staticmethod
    def _make_rerank_prompt() -> PromptTemplate:
        class RelevanceScore(BaseModel):
            index: int = Field(description="The index of the document in the provided list")
            relevance_score: float = Field(description="A score from 0.0 to 1.0 indicating relevance")
            reasoning: str = Field(description="Brief reason for the score")

        class RankedDocuments(BaseModel):
            ranked_results: List[RelevanceScore]

        parser = JsonOutputParser(pydantic_object=RankedDocuments)

        template = """You are an expert relevance ranker for an academic document search system.

The user asked: "{query}"

Below is a list of document snippets retrieved from a database.
Evaluate each snippet against the user's SPECIFIC constraints (year, department, document type, semester, etc.).

Scoring:
- 0.8 – 1.0 : Directly answers the query with matching constraints
- 0.5 – 0.8 : Related but may not match all constraints
- 0.0 – 0.5 : Off-topic or wrong constraints (e.g. wrong year / department)

Pay special attention to:
- Year mismatches (e.g. user asks for 2024 but doc is from 2023)
- Department mismatches
- Document type mismatches (e.g. user asks for syllabus but doc is a notice)

Documents:
{doc_list}

{format_instructions}
"""
        return PromptTemplate(
            template=template,
            input_variables=["query", "doc_list"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

    # ------------------------------------------------------------------
    # Pipeline stages
    # ------------------------------------------------------------------

    def _analyze_query(self, query: str) -> dict:
        """
        Stage 1 — Extract metadata filters from the user query.
        Returns a dict like {"dept": "...", "year": "...", ...} with None for unmentioned fields.
        """
        parser = JsonOutputParser(pydantic_object=type(
            "QF", (BaseModel,), {
                "__annotations__": {
                    "dept": Optional[str], "year": Optional[str],
                    "doc_type": Optional[str], "semester": Optional[str],
                },
            }
        ))

        def _chain(llm):
            return self._query_analysis_prompt | llm | parser

        result = _invoke_with_fallback(_chain, {"query": query})
        if result is None:
            logger.warning("Query analysis failed — proceeding without filters")
            return {}

        # Strip None values
        return {k: v for k, v in result.items() if v is not None}

    def _generate_queries(self, query: str) -> list[str]:
        """Stage 2 — Generate multi-query variants."""

        class MQ(BaseModel):
            queries: List[str] = Field(description="List of 3 alternative versions")

        parser = JsonOutputParser(pydantic_object=MQ)

        def _chain(llm):
            return self._multi_query_prompt | llm | parser

        result = _invoke_with_fallback(_chain, {"question": query})
        queries: list[str] = []
        if result and "queries" in result:
            queries = result["queries"]
        if query not in queries:
            queries.insert(0, query)
        return queries[:4]

    def _build_chroma_filter(self, filters: dict) -> dict | None:
        """
        Convert the extracted filters into a ChromaDB `where` clause.
        Only includes filters whose values are in the known valid sets.
        """
        conditions: list[dict] = []

        dept = filters.get("dept")
        if dept and dept in ALL_DEPT_VALUES:
            conditions.append({"dept": dept})

        year = filters.get("year")
        if year:
            conditions.append({"year": year})

        doc_type = filters.get("doc_type")
        if doc_type and doc_type in VALID_DOC_TYPES:
            conditions.append({"doc_type": doc_type})

        semester = filters.get("semester")
        if semester:
            conditions.append({"semester": semester})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def _hybrid_search(
        self,
        queries: list[str],
        k: int,
        chroma_filter: dict | None,
    ) -> list[list[Document]]:
        """
        Stage 3 — For each query, run vector search (with optional metadata filter)
        and BM25 keyword search. Returns a list of result lists for RRF.
        """
        all_lists: list[list[Document]] = []

        for q in queries:
            # --- Vector search (metadata-filtered) ---
            try:
                if chroma_filter:
                    vec_docs = self._vectorstore.similarity_search(q, k=k, filter=chroma_filter)
                    # If filter is too restrictive and returns nothing, fall back to unfiltered
                    if not vec_docs:
                        logger.info("Filtered vector search empty — falling back to unfiltered for '%s'", q[:60])
                        vec_docs = self._vectorstore.similarity_search(q, k=k)
                else:
                    vec_docs = self._vectorstore.similarity_search(q, k=k)
                all_lists.append(vec_docs)
            except Exception as e:
                logger.error("Vector search failed for '%s': %s", q[:60], e)

            # --- BM25 keyword search (no metadata filter — BM25 is in-memory) ---
            if self._bm25:
                try:
                    self._bm25.k = k
                    kw_docs = self._bm25.invoke(q)
                    all_lists.append(kw_docs)
                except Exception as e:
                    logger.error("BM25 search failed for '%s': %s", q[:60], e)

        return all_lists

    @staticmethod
    def _reciprocal_rank_fusion(result_lists: list[list[Document]], k: int = 60) -> list[Document]:
        """Stage 4 — Merge multiple ranked lists via RRF."""
        fused_scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}

        for rank_list in result_lists:
            for rank, doc in enumerate(rank_list):
                key = doc.page_content
                if key not in fused_scores:
                    fused_scores[key] = 0.0
                    doc_map[key] = doc
                fused_scores[key] += 1.0 / (rank + k)

        ranked = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_map[k] for k, _ in ranked]

    def _rerank(self, query: str, docs: list[Document], top_n: int) -> list[Document]:
        """Stage 5 — LLM reranking of candidate documents."""

        class RS(BaseModel):
            index: int = Field(description="Document index")
            relevance_score: float = Field(description="0.0 to 1.0")
            reasoning: str = Field(description="Brief reason")

        class RD(BaseModel):
            ranked_results: List[RS]

        parser = JsonOutputParser(pydantic_object=RD)

        # Format docs for the LLM
        snippets = []
        for i, doc in enumerate(docs):
            meta_str = json.dumps({
                k: v for k, v in doc.metadata.items()
                if k in ("title", "dept", "year", "doc_type", "semester", "audience", "filename", "keywords")
            }, ensure_ascii=False)
            snippets.append(f"Doc {i}:\nMetadata: {meta_str}\nContent: {doc.page_content[:500]}")

        combined = "\n\n".join(snippets)

        def _chain(llm):
            return self._rerank_prompt | llm | parser

        result = _invoke_with_fallback(_chain, {"query": query, "doc_list": combined})

        if result is None or "ranked_results" not in result:
            logger.warning("Reranking failed — returning top RRF results")
            return docs[:top_n]

        sorted_ranks = sorted(result["ranked_results"], key=lambda x: x["relevance_score"], reverse=True)

        final: list[Document] = []
        for item in sorted_ranks:
            if item["relevance_score"] < 0.5:
                continue
            idx = item["index"]
            if 0 <= idx < len(docs):
                logger.info(
                    "  Score %.2f | %s | %s",
                    item["relevance_score"],
                    docs[idx].metadata.get("title", "?"),
                    item["reasoning"],
                )
                final.append(docs[idx])
            if len(final) >= top_n:
                break

        return final

    @staticmethod
    def _deduplicate_by_source(docs: list[Document]) -> list[dict]:
        """
        Deduplicate results by source PDF and return file-level results.
        Returns a list of dicts with PDF info, ordered by first appearance (= best rank).
        """
        seen_sources: set[str] = set()
        results: list[dict] = []

        for doc in docs:
            source = doc.metadata.get("source", "")
            if source in seen_sources:
                continue
            seen_sources.add(source)

            results.append({
                "filepath": source,
                "filename": doc.metadata.get("filename", os.path.basename(source)),
                "title": doc.metadata.get("title", "Unknown"),
                "dept": doc.metadata.get("dept", "Unknown"),
                "year": doc.metadata.get("year", "Unknown"),
                "doc_type": doc.metadata.get("doc_type", "Unknown"),
                "semester": doc.metadata.get("semester", "Unknown"),
                "audience": doc.metadata.get("audience", "Unknown"),
                "summary": doc.metadata.get("summary", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "total_pages": doc.metadata.get("total_pages", None),
            })

        return results

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        k_fetch: int = 10,
        top_n: int = 5,
        on_progress=None,
    ) -> dict:
        """
        Full retrieval pipeline.

        Returns:
            {
                "query": ...,
                "filters_applied": ...,
                "generated_queries": ...,
                "documents": ...,
                "results": ...
            }

        on_progress(stage, message) is an optional callback used to
        stream progress updates to the caller.
        """

        def emit(stage: str, message: str = ""):
            if on_progress:
                try:
                    on_progress(stage, message)
                except Exception:
                    pass

        logger.info("=== Retrieval for: '%s' ===", query)

        emit(
            "retrieval_started",
            "Starting document retrieval...",
        )

        # --------------------------------------------------
        # 1. Query Analysis
        # --------------------------------------------------

        emit(
            "query_analysis_started",
            "Understanding your question...",
        )

        logger.info("Stage 1: Query analysis")

        filters = self._analyze_query(query)

        chroma_filter = self._build_chroma_filter(
            filters,
        )

        logger.info(
            "Extracted filters: %s",
            filters,
        )

        emit(
            "query_analysis_completed",
            "Query analysis complete.",
        )

        # --------------------------------------------------
        # 2. Multi Query Generation
        # --------------------------------------------------

        emit(
            "multi_query_started",
            "Expanding your search query...",
        )

        logger.info("Stage 2: Multi-query generation")

        queries = self._generate_queries(
            query,
        )

        logger.info(
            "Queries: %s",
            queries,
        )

        emit(
            "multi_query_completed",
            f"Generated {len(queries)} search queries.",
        )

        # --------------------------------------------------
        # 3. Hybrid Search
        # --------------------------------------------------

        emit(
            "hybrid_search_started",
            "Searching relevant documents...",
        )

        logger.info(
            "Stage 3: Hybrid search (%d queries, k=%d)",
            len(queries),
            k_fetch,
        )

        result_lists = self._hybrid_search(
            queries,
            k_fetch,
            chroma_filter,
        )

        emit(
            "hybrid_search_completed",
            "Relevant documents found.",
        )

        # --------------------------------------------------
        # 4. Reciprocal Rank Fusion
        # --------------------------------------------------

        emit(
            "fusion_started",
            "Combining search results...",
        )

        logger.info(
            "Stage 4: RRF fusion over %d result lists",
            len(result_lists),
        )

        fused = self._reciprocal_rank_fusion(
            result_lists,
        )

        candidates = fused[: k_fetch * 2]

        logger.info(
            "Candidates after fusion: %d",
            len(candidates),
        )

        emit(
            "fusion_completed",
            f"{len(candidates)} candidate chunks selected.",
        )

        # --------------------------------------------------
        # 5. LLM Reranking
        # --------------------------------------------------

        emit(
            "reranking_started",
            "Ranking the most relevant information...",
        )

        logger.info(
            "Stage 5: LLM reranking (%d candidates)",
            len(candidates),
        )

        reranked = self._rerank(
            query,
            candidates,
            top_n=top_n,
        )

        emit(
            "reranking_completed",
            f"Selected top {len(reranked)} chunks.",
        )

        # --------------------------------------------------
        # 6. Deduplication
        # --------------------------------------------------

        emit(
            "deduplication_started",
            "Preparing references...",
        )

        pdf_results = self._deduplicate_by_source(
            reranked,
        )

        logger.info(
            "Final results: %d unique PDFs",
            len(pdf_results),
        )

        emit(
            "deduplication_completed",
            f"{len(pdf_results)} source documents prepared.",
        )

        emit(
            "retrieval_completed",
            f"Retrieved {len(reranked)} relevant chunks.",
        )

        return {
            "query": query,
            "filters_applied": filters,
            "generated_queries": queries,
            "documents": reranked,
            "results": pdf_results,
        }



