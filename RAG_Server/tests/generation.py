from src.retrieval.services import RetrievalService
from src.generation.services import QAService


def main():
    retriever = RetrievalService()
    qa = QAService()

    query = input("Enter your question: ")

    retrieval = retriever.retrieve(query)

    documents = retrieval["documents"]

    print(f"\nRetrieved {len(documents)} chunks\n")

    response = qa.generate(
        query=query,
        documents=documents
    )

    print("\n========== ANSWER ==========\n")
    print(response.answer)

    print("\n========== SOURCES ==========\n")

    for source in response.sources:
        print(source)


if __name__ == "__main__":
    main()