from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException

# 🔐 CONFIG
SECRET_KEY = "THIS_SECRET_KEY"   # change later
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ─────────────────────────────────────────────
# Password hashing
# ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─────────────────────────────────────────────
# JWT
# ─────────────────────────────────────────────
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_token(token: str = Depends(oauth2_scheme)):
    return token
# ─────────────────────────────────────────────
# 🔥 THIS IS WHAT YOU WERE MISSING
# ─────────────────────────────────────────────
# def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
# ):
#     token = credentials.credentials

#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("user_id")

#         if user_id is None:
#             raise HTTPException(status_code=401, detail="Invalid token")

#         return {"user_id": user_id}

#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")

from app.database.mongodb import blacklist_collection

async def get_current_user(token: str = Depends(oauth2_scheme)):
    blacklisted = await blacklist_collection.find_one({"token": token})
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token revoked")

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload
    



# from datetime import datetime, timedelta
# from jose import jwt
# from passlib.context import CryptContext

# # JWT configuration
# SECRET_KEY = "THIS_SECRET_KEY"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# # Password hashing setup
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)


# def create_access_token(data: dict) -> str:
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

#     to_encode.update({"exp": expire})

#     encoded_jwt = jwt.encode(
#         to_encode,
#         SECRET_KEY,
#         algorithm=ALGORITHM
#     )

#     return encoded_jwt