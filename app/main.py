
from fastapi import FastAPI

from app.database import init_db

from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router


# Create the FastAPI application
app = FastAPI(
    title="NOVA",
    description="Personal AI Desktop Assistant",
    version="1.0.0"
)


# Register API routers
app.include_router(chat_router)
app.include_router(conversations_router)


# Initialize database
@app.on_event("startup")
def startup_event():
    init_db()
    print("NOVA database initialized successfully!")


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Hello Shrey! NOVA is running successfully!",
        "status": "online"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
