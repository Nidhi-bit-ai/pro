from datetime import datetime
from pyexpat.errors import messages
from bson import ObjectId

from app.database.mongodb import chats_collection
from app.utils.rag_client import query_rag


MAX_CONTEXT_MESSAGES = 6   # 👈 limit memory

# ─────────────────────────────────────────────
# Create new chat
# ─────────────────────────────────────────────
async def create_chat(user_id: str):
    chat = {
        "user_id": user_id,
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await chats_collection.insert_one(chat)
    return str(result.inserted_id)


# ─────────────────────────────────────────────
# Get chats list (sidebar)
# ─────────────────────────────────────────────
async def get_user_chats(user_id: str):
    chats = []
    cursor = chats_collection.find({"user_id": user_id}).sort("updated_at", -1)

    async for chat in cursor:
        chats.append({
            "chat_id": str(chat["_id"]),
            "title": chat.get("title", "Chat"),
            "updated_at": chat["updated_at"].isoformat() if chat.get("updated_at") else None,
        })

    return chats
# async def get_user_chats(user_id: str):
#     chats = []
#     cursor = chats_collection.find({"user_id": user_id}).sort("updated_at", -1)

#     async for chat in cursor:
#         chats.append({
#             "chat_id": str(chat["_id"]),
#             "title": chat.get("title", "Chat"),
#             "updated_at": chat["updated_at"],
#         })

#     return chats


# ─────────────────────────────────────────────
# Delete chat
# ─────────────────────────────────────────────
async def delete_chat(chat_id: str, user_id: str):
    result = await chats_collection.delete_one({
        "_id": ObjectId(chat_id),
        "user_id": user_id
    })

    return result.deleted_count == 1


# ─────────────────────────────────────────────
# Send message (OPTIMIZED MEMORY)
# ─────────────────────────────────────────────
async def send_message(user_id: str, chat_id: str, message: str):
    chat = await chats_collection.find_one({
        "_id": ObjectId(chat_id),
        "user_id": user_id
    })

    if not chat:
        raise Exception("Chat not found")

    messages = chat.get("messages", [])
    # Auto title if first message
    if len(messages) == 0:
        title = message[:40]   # first 40 chars
        await chats_collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": {"title": title}}
        )
    # ✅ MEMORY OPTIMIZATION (last N messages only)
    context_messages = messages[-MAX_CONTEXT_MESSAGES:]

    # Build context
    context = ""
    for msg in context_messages:
        context += f"{msg['role']}: {msg['content']}\n"

    try:
        answer =  query_rag(message, context)    #await before if query_rag becomes async
    except Exception as e:
        answer = f"RAG connection error: {str(e)}"

    # Save messages
    new_messages = messages + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]

    await chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {
            "$set": {
                "messages": new_messages,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {
        "answer": answer,
        "chat_id": chat_id
    }


from bson import ObjectId


# ─────────────────────────────────────────────
# Get full chat history
# ─────────────────────────────────────────────
async def get_chat_by_id(chat_id: str, user_id: str):
    chat = await chats_collection.find_one({
        "_id": ObjectId(chat_id),
        "user_id": user_id
    })

    if not chat:
        return {"error": "Chat not found"}

    messages = chat.get("messages", [])

    # Convert if needed (safe response)
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    return {
        "chat_id": str(chat["_id"]),
        "title": chat.get("title", "Chat"),
        "messages": formatted_messages,
        "created_at": chat["created_at"].isoformat() if chat.get("created_at") else None,
        "updated_at": chat["updated_at"].isoformat() if chat.get("updated_at") else None,
    }
    
#-----------------------------
# TEMP: test RAG without DB
#-----------------------------

 
def temp_chat(message: str):
    try:
        answer = query_rag(message, "")
    except Exception as e:
        answer = f"RAG error: {str(e)}"

    return {"answer": answer}
   
# from datetime import datetime
# from bson import ObjectId

# from app.database.mongodb import db
# from app.utils.rag_client import query_rag

# chat_collection = db["chats"]


# async def ask_question(user_id: str, query: str, chat_id: str = None):
    # If new chat → create
    # if not chat_id:
        # chat_doc = {
            # "user_id": user_id,
#             "messages": [],
#             # "created_at": datetime.utcnow()
#         }
#         result = await chat_collection.insert_one(chat_doc)
#         chat_id = str(result.inserted_id)

#     # Call RAG
#     rag_response = query_rag(query)
#     answer = rag_response.get("answer", "No response")

#     # Store messages
#     await chat_collection.update_one(
#         {"_id": ObjectId(chat_id)},
#         {
#             "$push": {
#                 "messages": {
#                     "$each": [
#                         {
#                             "role": "user",
#                             "content": query,
#                             "timestamp": datetime.utcnow()
#                         },
#                         {
#                             "role": "assistant",
#                             "content": answer,
#                             "timestamp": datetime.utcnow()
#                         }
#                     ]
#                 }
#             }
#         }
#     )

#     return {
#         "answer": answer,
#         "chat_id": chat_id
#     }


# async def get_chat_history(user_id: str):
#     chats = []

#     async for chat in chat_collection.find({"user_id": user_id}):
#         chats.append({
#             "chat_id": str(chat["_id"]),
#             "messages": chat["messages"]
#         })

#     return chats



# # ---------------------------
# # chat list and delete
# # --------------------

# async def get_chat_list(user_id: str):
#     chats = []

#     async for chat in chat_collection.find({"user_id": user_id}):
#         chats.append({
#             "chat_id": str(chat["_id"]),
#             "created_at": chat.get("created_at"),
#             "last_message": chat.get("messages", [])[-1]["content"] if chat.get("messages") else ""
#         })

#     return chats


# async def delete_chat(user_id: str, chat_id: str):
#     result = await chat_collection.delete_one({
#         "_id": ObjectId(chat_id),
#         "user_id": user_id
#     })

#     if result.deleted_count == 0:
#         return {"message": "Chat not found"}

#     return {"message": "Chat deleted successfully"}