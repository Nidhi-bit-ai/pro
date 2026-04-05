from app.utils.rag_client import query_rag


def query_custom_docs(query: str, docs: str):
    try:
        # Directly send docs as context
        answer = query_rag(query, docs)
    except Exception as e:
        answer = f"Error: {str(e)}"

    return {"answer": answer}