from langchain_core.documents import Document

from .config import (
    SYSTEM_PROMPT,
    MAX_CONTEXT_DOCUMENTS,
    MAX_CHARS_PER_DOCUMENT,
)


def build_context(documents: list[Document]) -> str:
    """
    Converts retrieved documents into a structured context block.
    """

    sections = []

    for idx, doc in enumerate(documents[:MAX_CONTEXT_DOCUMENTS], start=1):

        metadata = doc.metadata

        title = metadata.get("title", "Unknown")
        department = metadata.get("Dept", "Unknown")
        audience = metadata.get("audience", "Unknown")
        summary = metadata.get("summary", "Not available")
        source = metadata.get("source", "Unknown")
        page = metadata.get("page", "Unknown")

        content = doc.page_content[:MAX_CHARS_PER_DOCUMENT]

        sections.append(
            f"""
==========================
Document {idx}

Source:
{source}

Page:
{page}

Title:
{title}

Department:
{department}

Audience:
{audience}

Summary:
{summary}

Content:
{content}
""".strip()
        )

    return "\n\n".join(sections)


def build_prompt(query: str, documents: list[Document]) -> str:

    context = build_context(documents)

    return f"""
{SYSTEM_PROMPT}

----------------------------------------

Context

{context}

----------------------------------------

Question

{query}

Answer:
""".strip()