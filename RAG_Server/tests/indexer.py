"""
Test script for IndexingService.
Indexes PDFs from storage/pdfs into ChromaDB.
Run this AFTER scrapper.py has downloaded some PDFs.
"""
import sys
import logging
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.indexing.services import IndexingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

def main():
    PDF_DIR = PROJECT_ROOT / "storage" / "pdfs"
    DB_DIR = str(PROJECT_ROOT / "storage" / "chroma_db")

    print(f"\n{'='*60}")
    print(f"  IndexingService Test")
    print(f"  PDF dir : {PDF_DIR}")
    print(f"  DB dir  : {DB_DIR}")
    print(f"{'='*60}\n")

    service = IndexingService(
        pdf_dir=PDF_DIR,
        db_dir=DB_DIR,
        chunk_size=1000,
        chunk_overlap=200,
    )

    result = service.index_all()

    print(f"\n{'='*60}")
    print(f"  Indexing Results")
    print(f"{'='*60}")
    if "error" in result:
        print(f"  ERROR: {result['error']}")
    else:
        print(f"  Total PDFs found     : {result['total_pdfs']}")
        print(f"  Indexed (new/changed): {result['indexed']}")
        print(f"  Skipped (unchanged)  : {result['skipped_unchanged']}")
        print(f"  Chunks added         : {result['chunks_added']}")
    print()

    # Quick sanity check — read back from the vector store
    from langchain_chroma import Chroma
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    import os

    emb_key = os.getenv("GEMINI1")
    if emb_key:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", google_api_key=emb_key,
        )
        vs = Chroma(
            persist_directory=DB_DIR,
            embedding_function=embeddings,
            collection_name="mnit_docs",
        )
        total = vs._collection.count()
        print(f"  Verification: {total} total chunks in ChromaDB")

        # Show a sample of indexed metadata
        sample = vs.get(limit=5, include=["metadatas"])
        if sample and sample["metadatas"]:
            print(f"\n  Sample metadata from first 5 chunks:")
            for i, meta in enumerate(sample["metadatas"]):
                print(f"    [{i}] title={meta.get('title', '?')} | dept={meta.get('dept', '?')} | year={meta.get('year', '?')}")
    print()


if __name__ == "__main__":
    main()
