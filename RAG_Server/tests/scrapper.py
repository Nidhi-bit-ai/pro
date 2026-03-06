"""
Test script for CrawlService.
Crawls mnit.ac.in and downloads up to 20 PDFs.
"""
import sys
import logging
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.scrapping.services import CrawlService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

def main():
    START_URL = "https://www.mnit.ac.in"
    MAX_DOWNLOADS = 20
    NUM_THREADS = 4

    print(f"\n{'='*60}")
    print(f"  CrawlService Test")
    print(f"  URL        : {START_URL}")
    print(f"  Max PDFs   : {MAX_DOWNLOADS}")
    print(f"  Threads    : {NUM_THREADS}")
    print(f"{'='*60}\n")

    crawler = CrawlService(
        allowed_domain="mnit.ac.in",
        max_downloads=MAX_DOWNLOADS,
        num_threads=NUM_THREADS,
    )

    result = crawler.start(START_URL)

    print(f"\n{'='*60}")
    print(f"  Crawl Results")
    print(f"{'='*60}")
    print(f"  Pages visited    : {result['pages_visited']}")
    print(f"  PDFs discovered  : {result['pdfs_found']}")
    print(f"  Files downloaded : {len(result['downloaded_files'])}")
    print()

    for i, f in enumerate(result["downloaded_files"], 1):
        print(f"  [{i:2d}] {Path(f['filepath']).name}")
        print(f"       URL: {f['url']}")
        print(f"       From: {f['source_url']}")
        print()


if __name__ == "__main__":
    main()
