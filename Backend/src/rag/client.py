# src/rag/client.py

import httpx

from src.config import RAG_SERVER_URL
import json

class RAGClient:
    """
    Client responsible for communicating with the RAG Server.
    """

    def __init__(self):
        self.base_url = RAG_SERVER_URL.rstrip("/")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(120.0),
        )

    async def health(self):
        """
        Check whether the RAG Server is running.
        """

        try:
            response = await self.client.get("/health")
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            raise RuntimeError(
                f"Unable to connect to RAG Server: {e}"
            ) from e

    async def chat(self, query: str):
        """
        Send a user query to the RAG Server.
        """

        try:
            response = await self.client.post(
                "/chat/",
                json={
                    "query": query,
                },
            )

            response.raise_for_status()

            return response.json()

        # except httpx.HTTPError as e:
        #     raise RuntimeError(
        #         f"RAG chat request failed: {e}"
        #     ) from e
        except httpx.HTTPStatusError as e:
            print("Status:", e.response.status_code)
            print("Body:", e.response.text)
            raise RuntimeError(
                f"RAG chat request failed: {e}"
            ) from e

        except Exception as e:
            print(type(e))
            print(repr(e))
            raise RuntimeError(
                f"Unexpected RAG client error: {e}"
            ) from e

    async def upload_document(
        self,
        file,
        document_id: int,
    ):
        """
        Upload a document to the RAG Server for indexing.
        """

        try:

            file.file.seek(0)
            print("RAG URL:", self.base_url)
            response = await self.client.post(
                "/documents/upload",
                data={
                    "document_id": str(document_id),
                },
                files={
                    "file": (
                        file.filename,
                        file.file,
                        file.content_type,
                    )
                },
            )
            print("Uploading document:", document_id)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:

            raise RuntimeError(
                f"RAG document upload failed: {e}"
            ) from e

    async def delete_document(
        self,
        stored_filename: str,
    ):
        """
        Delete a document from the RAG Server.
        """

        try:

            response = await self.client.delete(
                f"/documents/{stored_filename}",
            )

            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:

            raise RuntimeError(
                f"RAG document deletion failed: {e}"
            ) from e


    async def reindex_document(
        self,
        stored_filename: str,
    ):
        """
        Reindex an existing document.
        """

        try:

            response = await self.client.post(
                f"/documents/{stored_filename}/reindex",
            )

            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:

            raise RuntimeError(
                f"RAG document reindex failed: {e}"
            ) from e
            
            
    async def stream_chat(
        self,
        query: str,
    ):
        """
        Stream RAG events from the RAG Server.
        """

        try:

            async with self.client.stream(
                "POST",
                "/chat/stream",
                json={
                    "query": query,
                },
            ) as response:

                response.raise_for_status()

                async for line in response.aiter_lines():

                    if not line:
                        continue

                    yield json.loads(line)

        except httpx.HTTPStatusError as e:

            print("Status:", e.response.status_code)
            print("Body:", await e.response.aread())

            raise RuntimeError(
                f"RAG stream failed: {e}"
            ) from e

        except Exception as e:

            raise RuntimeError(
                f"Unexpected streaming error: {e}"
            ) from e
        
    async def close(self):
        """
        Close the underlying HTTP client.
        """

        await self.client.aclose()