"""
Test script for RetrievalService.
Runs a few sample queries against the indexed ChromaDB.
Run this AFTER indexer.py has populated the vector store.

Update QUERIES below with your own based on what was actually indexed.
"""
import sys
import json
import logging
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.services import RetrievalService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

# ------------------------------------------------------------------
# Add / modify queries here based on documents you actually downloaded.
# These are generic starting points that should match common MNIT PDFs.
# ------------------------------------------------------------------
QUERIES = [
    "latest notices from MNIT",
    "CSE syllabus",
    "examination schedule 2024",
    "what is eResource budget of library for Computer Science & Engineering department",
    "What is Third Party Information",
    "how do I log in Turnitin"
]


def run_query(service: RetrievalService, query: str, top_n: int = 3):
    print(f"\n{'─'*60}")
    print(f"  Query: {query}")
    print(f"{'─'*60}")

    result = service.retrieve(query, k_fetch=10, top_n=top_n)

    print(f"  Filters applied   : {result['filters_applied']}")
    print(f"  Generated queries : {result['generated_queries']}")
    print(f"  Results returned  : {len(result['results'])}")
    print()

    for i, pdf in enumerate(result["results"], 1):
        print(f"  [{i}] {pdf['filename']}")
        print(f"      Title    : {pdf['title']}")
        print(f"      Dept     : {pdf['dept']}")
        print(f"      Year     : {pdf['year']}")
        print(f"      Type     : {pdf['doc_type']}")
        print(f"      Semester : {pdf['semester']}")
        print(f"      Audience : {pdf['audience']}")
        print(f"      Summary  : {pdf['summary'][:120]}...")
        print(f"      Path     : {pdf['filepath']}")
        print()


def main():
    DB_DIR = str(PROJECT_ROOT / "storage" / "chroma_db")

    print(f"\n{'='*60}")
    print(f"  RetrievalService Test")
    print(f"  DB dir  : {DB_DIR}")
    print(f"  Queries : {len(QUERIES)}")
    print(f"{'='*60}")

    service = RetrievalService(db_dir=DB_DIR)

    for q in QUERIES:
        run_query(service, q)

    print(f"\n{'='*60}")
    print(f"  All queries complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
