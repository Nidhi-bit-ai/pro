import os
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import time
import urllib3
import threading
from queue import Queue, Empty
import concurrent.futures
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

IGNORE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
    '.zip', '.rar', '.tar', '.gz', '.7z',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.mp3', '.mp4', '.avi', '.mov',
    '.css', '.js', '.json', '.xml',
}

DOWNLOAD_DIR = str(BASE_DIR / "storage" / "pdfs")


class CrawlService:
    """
    Web crawling service that discovers and downloads PDF files
    from a given domain. Designed to be invoked from an API endpoint.
    """

    def __init__(
        self,
        allowed_domain: str,
        download_dir: str = DOWNLOAD_DIR,
        max_downloads: int = 100,
        num_threads: int = 5,
    ):
        self.allowed_domain = allowed_domain
        self.download_dir = download_dir
        self.max_downloads = max_downloads
        self.num_threads = num_threads

        os.makedirs(self.download_dir, exist_ok=True)

        # Per-crawl mutable state
        self._visited_pages: set[str] = set()
        self._pdf_links: set[str] = set()
        self._downloaded_files: list[dict] = []  # {url, source_url, filepath}

        # Synchronisation primitives
        self._visited_lock = threading.Lock()
        self._pdf_lock = threading.Lock()
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _is_valid_url(self, url: str) -> bool:
        """Check if the URL belongs to the allowed domain."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.endswith(self.allowed_domain)
        except Exception:
            return False

    @staticmethod
    def _is_pdf(url: str) -> bool:
        """Check if the URL points to a PDF file."""
        return urlparse(url).path.lower().endswith('.pdf')

    def _should_crawl(self, url: str) -> bool:
        """Determine if we should crawl this URL for more links."""
        if not self._is_valid_url(url):
            return False
        path = urlparse(url).path.lower()
        return not any(path.endswith(ext) for ext in IGNORE_EXTENSIONS)

    # ------------------------------------------------------------------
    # PDF download
    # ------------------------------------------------------------------

    def _download_pdf(self, url: str, source_url: str | None = None) -> None:
        """Download a single PDF, overwriting any existing file with the same name."""
        if self._stop_event.is_set():
            return

        try:
            with self._pdf_lock:
                if url in self._pdf_links:
                    return
                if len(self._pdf_links) >= self.max_downloads:
                    self._stop_event.set()
                    return
                self._pdf_links.add(url)

            # Build a clean filename from the URL
            filename = unquote(os.path.basename(urlparse(url).path))
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            filename = "".join(
                c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')
            ).strip() or "document.pdf"

            filepath = os.path.join(self.download_dir, filename)

            logger.info("Downloading PDF: %s", url)

            response = requests.get(url, stream=True, timeout=30, verify=False)

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                    # Overwrite if file already exists
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logger.info("Saved: %s", filepath)

                    with self._pdf_lock:
                        self._downloaded_files.append({
                            "url": url,
                            "source_url": source_url,
                            "filepath": filepath,
                        })
                else:
                    logger.warning("Skipping %s — Content-Type: %s", url, content_type)
            else:
                logger.warning("Failed to download %s — Status %s", url, response.status_code)

        except Exception as e:
            logger.error("Error downloading %s: %s", url, e)

    # ------------------------------------------------------------------
    # Link extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _get_links_from_page(url: str, session: requests.Session) -> set[str]:
        """Extract all links from a webpage."""
        try:
            response = session.get(url, timeout=15, verify=False)
            if response.status_code != 200:
                logger.warning("Failed to retrieve %s — Status %s", url, response.status_code)
                return set()

            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return set()

            soup = BeautifulSoup(response.content, "html.parser")
            links: set[str] = set()
            for a_tag in soup.find_all("a", href=True):
                full_url = urljoin(url, a_tag["href"]).split("#")[0]
                if full_url:
                    links.add(full_url)
            return links

        except Exception as e:
            logger.error("Error processing page %s: %s", url, e)
            return set()

    # ------------------------------------------------------------------
    # Worker & orchestration
    # ------------------------------------------------------------------

    def _crawl_worker(self, queue: Queue, session: requests.Session) -> None:
        while not self._stop_event.is_set():
            try:
                current_url = queue.get(timeout=1)
            except Empty:
                continue

            try:
                if self._stop_event.is_set():
                    return

                with self._visited_lock:
                    if current_url in self._visited_pages:
                        continue
                    self._visited_pages.add(current_url)

                if self._is_pdf(current_url):
                    self._download_pdf(current_url, source_url=current_url)
                    continue

                if not self._should_crawl(current_url):
                    continue

                with self._pdf_lock:
                    pdf_count = len(self._pdf_links)
                logger.info("Scanning: %s | PDFs found: %d", current_url, pdf_count)

                new_links = self._get_links_from_page(current_url, session)
                for link in new_links:
                    if self._stop_event.is_set():
                        break
                    if self._is_pdf(link):
                        self._download_pdf(link, source_url=current_url)
                    else:
                        with self._visited_lock:
                            if link not in self._visited_pages:
                                queue.put(link)

            except Exception as e:
                logger.error("Error in worker for %s: %s", current_url, e)
            finally:
                queue.task_done()

    def start(self, start_url: str) -> dict:
        """
        Begin crawling from *start_url*.

        Returns a summary dict:
            {
                "pages_visited": int,
                "pdfs_found": int,
                "downloaded_files": [{"url", "source_url", "filepath"}, ...]
            }
        """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self._stop_event.clear()

        queue: Queue[str] = Queue()
        queue.put(start_url)

        logger.info(
            "Starting crawl from %s with %d threads (max %d downloads)",
            start_url, self.num_threads, self.max_downloads,
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            for _ in range(self.num_threads):
                session = requests.Session()
                session.headers.update({
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/91.0.4472.124 Safari/537.36'
                    ),
                })
                futures.append(
                    executor.submit(self._crawl_worker, queue, session)
                )

            try:
                while any(f.running() for f in futures):
                    if len(self._pdf_links) >= self.max_downloads:
                        logger.info("Reached download limit (%d). Stopping.", self.max_downloads)
                        self._stop_event.set()
                        break
                    if queue.unfinished_tasks == 0:
                        logger.info("Queue empty — crawl complete.")
                        self._stop_event.set()
                        break
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.warning("Crawl interrupted by user.")
                self._stop_event.set()

            concurrent.futures.wait(futures)

        logger.info("All threads stopped.")

        return {
            "pages_visited": len(self._visited_pages),
            "pdfs_found": len(self._pdf_links),
            "downloaded_files": list(self._downloaded_files),
        }