from fastapi import APIRouter, Depends

from app.chat.services import (
    create_chat,
    send_message,
    get_user_chats,
    delete_chat,
    temp_chat
)
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


# ─────────────────────────────────────────────
# Create new chat
# ─────────────────────────────────────────────
@router.post("/create")
async def create_new_chat(user=Depends(get_current_user)):
    chat_id = await create_chat(user["user_id"])
    return {"chat_id": chat_id}


# ─────────────────────────────────────────────
# Send message
# ─────────────────────────────────────────────
@router.post("/message")
async def chat_message(
    chat_id: str,
    message: str,
    user=Depends(get_current_user)
):
    return await send_message(user["user_id"], chat_id, message)


# ─────────────────────────────────────────────
# Get chat list (sidebar)
# ─────────────────────────────────────────────
@router.get("/list")
async def list_chats(user=Depends(get_current_user)):
    return await get_user_chats(user["user_id"])


# ─────────────────────────────────────────────
# Delete chat
# ─────────────────────────────────────────────
@router.delete("/delete/{chat_id}")
async def remove_chat(chat_id: str, user=Depends(get_current_user)):
    success = await delete_chat(chat_id, user["user_id"])
    return {"deleted": success}


from app.chat.services import get_chat_by_id


# ─────────────────────────────────────────────
# Get full chat
# ─────────────────────────────────────────────
@router.get("/{chat_id}")
async def get_chat(chat_id: str, user=Depends(get_current_user)):
    return await get_chat_by_id(chat_id, user["user_id"])


from fastapi.responses import StreamingResponse
import asyncio


@router.post("/stream")
async def stream_chat(
    chat_id: str,
    message: str,
    user=Depends(get_current_user)
):
    async def generate():
        response = await send_message(user["user_id"], chat_id, message)
        answer = response["answer"]

        # simulate streaming
        for word in answer.split():
            yield word + " "
            await asyncio.sleep(0.05)

    return StreamingResponse(generate(), media_type="text/plain")

# ------------------------------
# Temporary route for testing RAG without auth
# ------------------------------
@router.post("/temp")
async def temporary_chat(message: str):
    return temp_chat(message)


# from fastapi import APIRouter, Depends
# from app.chat.schemas import ChatRequest
# from app.chat.services import ask_question, get_chat_history
# from app.utils.dependencies import get_current_user


# from app.chat.services import (
#     ask_question,
#     get_chat_history,
#     get_chat_list,
#     delete_chat
# )

# router = APIRouter(prefix="/chat", tags=["Chat"])


# @router.post("/ask")
# async def chat_endpoint(
#     request: ChatRequest,
#     user=Depends(get_current_user)
# ):
#     response = await ask_question(
#         user_id=user["user_id"],
#         query=request.query,
#         chat_id=request.chat_id
#     )
#     return response


# @router.get("/history")
# async def history_endpoint(user=Depends(get_current_user)):
#     return await get_chat_history(user["user_id"])




# #-------------------------------------------
# # chat list and delete endpoints 
# # ------------------------------------------

# from fastapi import HTTPException

# # 👇 ADD BELOW EXISTING ROUTES

# @router.get("/list")
# async def chat_list(user=Depends(get_current_user)):
#     return await get_chat_list(user["user_id"])


# @router.delete("/{chat_id}")
# async def delete_chat_route(chat_id: str, user=Depends(get_current_user)):
#     result = await delete_chat(user["user_id"], chat_id)

#     if result["message"] == "Chat not found":
#         raise HTTPException(status_code=404, detail="Chat not found")

#     return result