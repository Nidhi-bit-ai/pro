from pydantic import BaseModel, EmailStr


class ProfileResponse(BaseModel):
    id: str
    name: str
    email: EmailStr