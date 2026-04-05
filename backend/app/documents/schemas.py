from pydantic import BaseModel


class DocumentQuery(BaseModel):
    query: str