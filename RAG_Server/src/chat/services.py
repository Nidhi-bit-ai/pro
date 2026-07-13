from src.retrieval.services import RetrievalService
from src.generation.services import QAService

from .models import ChatResponse
from typing import Callable, Optional
import json
from queue import Queue

class ChatService:

    def __init__(self):

        self.retriever = RetrievalService()
        self.qa = QAService()

    def chat(
        self,
        query: str,
        on_progress: Optional[
            Callable[[str, str], None]
        ] = None,
    ) -> ChatResponse:
        """
        End-to-end RAG pipeline.

        Query
            ↓
        Retrieval
            ↓
        Generation
            ↓
        Final Response
        """

        retrieval_result = self.retriever.retrieve(
            query=query,
            on_progress=on_progress,
        )

        documents = retrieval_result["documents"]

        answer = self.qa.generate(
            query=query,
            documents=documents,
            on_progress=on_progress,
        )

        return ChatResponse(
            query=query,
            answer=answer.answer,
            sources=answer.sources,

            retrieval_results=retrieval_result["results"],

            retrieved_chunks=len(documents),
            filters_applied=retrieval_result["filters_applied"],

            model="gemini-2.5-flash",
        )
        
    def chat_stream(
        self,
        query: str,
    ):
        """
        Streaming version of the RAG pipeline.
        Emits NDJSON events.
        """

        progress_queue = Queue()

        def on_progress(
            stage: str,
            message: str,
        ):
            progress_queue.put(
                {
                    "type": "status",
                    "stage": stage,
                    "message": message,
                }
            )

        retrieval_result = self.retriever.retrieve(
            query=query,
            on_progress=on_progress,
        )

        documents = retrieval_result["documents"]

        answer = self.qa.generate(
            query=query,
            documents=documents,
            on_progress=on_progress,
        )

        while not progress_queue.empty():

            yield (
                json.dumps(
                    progress_queue.get()
                )
                + "\n"
            )

        yield (
            json.dumps(
                {
                    "type": "final",
                    "data": ChatResponse(
                        query=query,
                        answer=answer.answer,
                        sources=answer.sources,
                        retrieval_results=retrieval_result["results"],
                        retrieved_chunks=len(documents),
                        filters_applied=retrieval_result["filters_applied"],
                        model="gemini-2.5-flash",
                    ).model_dump(),
                }
            )
            + "\n"
        )