from fastapi import UploadFile

from src.storage.service import storage_service
from src.indexing.services import IndexingService


class DocumentService:

    def __init__(self):

        self.indexing_service = IndexingService()


    async def upload_document(
        self,
        file: UploadFile,
        document_id: int,
    ):

        try:
            saved_file = await storage_service.save_document(
                file=file,
                document_id=document_id,
            )

            print("Saved file:", saved_file)

            self.indexing_service.index_document(
                saved_file["path"],
            )

            print("Indexing completed")

            return {
                "document_id": document_id,
                "stored_filename": saved_file["stored_filename"],
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
        

    async def delete_document(
        self,
        stored_filename: str,
    ):

        await storage_service.delete_document(
            stored_filename,
        )


        self.indexing_service.delete_document(
            stored_filename,
        )


        return {
            "message": "Document deleted",
        }



    async def reindex_document(
        self,
        stored_filename: str,
    ):

        path = storage_service.get_path(
            stored_filename,
        )


        self.indexing_service.delete_document(
            stored_filename,
        )


        self.indexing_service.index_document(
            path,
        )


        return {
            "message": "Document reindexed",
        }



document_service = DocumentService()