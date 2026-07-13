from .client import RAGClient


class RAGService:
    """
    Business layer for interacting with the RAG Server.
    """

    def __init__(self):
        self.client = RAGClient()

    async def health(self):

        return await self.client.health()

    async def chat(
        self,
        message: str,
    ):

        try:

            return await self.client.chat(
                query=message,
            )

        except Exception as e:

            error_message = str(e)

            if "RESOURCE_EXHAUSTED" in error_message:

                return {
                    "answer": (
                        "The AI service has reached its temporary usage limit. "
                        "Please try again after some time."
                    ),
                    "sources": [],
                }

            raise
        
        
    async def upload_document(
        self,
        file,
        document_id: int,
    ):

        return await self.client.upload_document(
            file=file,
            document_id=document_id,
        )

    # async def delete_document(
    #     self,
    #     document_id: int,
    # ):

    #     return await self.client.delete_document(
    #         document_id=document_id,
    #     )

    # async def reindex_document(
    #     self,
    #     document_id: int,
    # ):

    #     return await self.client.reindex_document(
    #         document_id=document_id,
    #     )
    
    async def delete_document(
        self,
        stored_filename: str,
    ):
        return await self.client.delete_document(
            stored_filename,
        )


    async def reindex_document(
        self,
        stored_filename: str,
    ):
        return await self.client.reindex_document(
            stored_filename,
        )

    async def close(self):

        await self.client.close()