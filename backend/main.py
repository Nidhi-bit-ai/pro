from fastapi import FastAPI
# This is the main entry point for the FastAPI application. It sets up the app, includes routers, and defines any global dependencies or middleware.
# The app is structured in a modular way, with separate routers for authentication and chat functionality. The main.py file serves as the central hub for the application, orchestrating the different components and ensuring they work together seamlessly.
# The app includes a protected route to demonstrate how to use the authentication dependencies, and it also includes the chat routes for handling user interactions with the RAG system. The root endpoint provides a simple message to confirm that the backend is running.
# The app is designed to be scalable and maintainable, allowing for easy addition of new features and routes as needed. The use of FastAPI's dependency injection system ensures that authentication and other common functionality can be easily reused across different routes and modules.
# The app also includes error handling for the RAG client, ensuring that any issues with the RAG server are gracefully handled and communicated back to the user. Overall, this structure provides a solid foundation for building a robust backend for a RAG-based application.
#-------authentication --------
from app.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])


@app.get("/")
async def root():
    return {"message": "Backend is running"}

#------protected route --------
from fastapi import Depends
from app.utils.dependencies import get_current_user

@app.get("/protected")
def protected_route(user=Depends(get_current_user)):
    return {"message": "You are authorized", "user": user}

#------chat --------
from app.chat import router as chat_router

app.include_router(chat_router)

#------custom documents --------
from app.documents.routes import router as docs_router

app.include_router(docs_router)



#------profile --------
from app.profile.routes import router as profile_router

app.include_router(profile_router)



#------------------------------ 
#          scrapping 
#------------------------------
from app.scraping.routes import router as scraping_router

app.include_router(scraping_router)