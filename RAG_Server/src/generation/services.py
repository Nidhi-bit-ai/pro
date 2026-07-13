import os
from typing import Callable, List, Optional

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import (
    MODEL_NAME,
    TEMPERATURE,
    API_KEY_ENV,
    MAX_OUTPUT_TOKENS,
)
from .models import AnswerResponse, Source
from .prompt import build_prompt

load_dotenv()


class QAService:

    def __init__(self):

        api_key = os.getenv(API_KEY_ENV)

        if not api_key:
            raise ValueError(f"{API_KEY_ENV} not found in environment variables.")

        self.llm = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            google_api_key=api_key,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )

    def _extract_sources(self, documents: List[Document]) -> List[Source]:

        seen = set()
        sources = []

        for doc in documents:

            metadata = doc.metadata

            source_path = metadata.get("source", "")
            filename = os.path.basename(source_path)

            if filename in seen:
                continue

            seen.add(filename)

            sources.append(
                Source(
                    title=metadata.get("title", "Unknown"),
                    department=metadata.get("Dept", "Unknown"),
                    source=filename,
                    page=metadata.get("page", 1),
                )
            )

        return sources

    def generate(
        self,
        query: str,
        documents: List[Document],
        on_progress: Optional[Callable[[str, str], None]] = None,
    ) -> AnswerResponse:

        def emit(stage: str, message: str = ""):
            if on_progress:
                try:
                    on_progress(stage, message)
                except Exception:
                    pass

        if not documents:

            emit(
                "generation_completed",
                "No relevant documents found.",
            )

            return AnswerResponse(
                answer="I couldn't find any relevant information in the available MNIT documents.",
                sources=[],
            )

        # ----------------------------------------
        # Prompt Building
        # ----------------------------------------

        emit(
            "generation_started",
            "Preparing answer...",
        )

        emit(
            "prompt_building_started",
            "Building prompt...",
        )

        prompt = build_prompt(
            query,
            documents,
        )

        emit(
            "prompt_building_completed",
            "Prompt ready.",
        )

        # ----------------------------------------
        # LLM Generation
        # ----------------------------------------

        emit(
            "llm_generation_started",
            "Generating answer...",
        )

        try:

            response = self.llm.invoke(
                prompt,
            )

            emit(
                "llm_generation_completed",
                "Answer generated.",
            )

            answer = response.content.strip()

            if answer.startswith("```"):
                answer = answer.replace(
                    "```",
                    "",
                ).strip()

            emit(
                "generation_completed",
                "Response ready.",
            )

            return AnswerResponse(
                answer=answer,
                sources=self._extract_sources(
                    documents,
                ),
            )

        except Exception as e:

            print("========== LLM ERROR ==========")
            print(type(e))
            print(repr(e))
            print("===============================")

            error_message = str(e)

            # ----------------------------------------
            # Gemini Rate Limit
            # ----------------------------------------

            if (
                "RESOURCE_EXHAUSTED" in error_message.upper()
                or "RESOURCE EXHAUSTED" in error_message.upper()
                or "quota" in error_message.lower()
                or "rate limit" in error_message.lower()
                or "429" in error_message
            ):

                emit(
                    "rate_limit",
                    "AI usage limit reached.",
                )

                return AnswerResponse(
                    answer=(
                        "The AI service has temporarily reached its usage limit. "
                        "Please try again after some time."
                    ),
                    sources=self._extract_sources(
                        documents,
                    ),
                )

            # ----------------------------------------
            # Other Errors
            # ----------------------------------------

            emit(
                "generation_error",
                error_message,
            )

            return AnswerResponse(
                answer=(
                    "I am unable to generate a response right now. "
                    "Please try again later."
                ),
                sources=[],
            )       
        
                
                
                
                