from uuid import uuid4

from fastapi import APIRouter

from app.services.memory_service import (
    create_conversation,
    get_conversations
)

router = APIRouter()


# Create a new conversation
@router.post("/conversations")
def new_conversation():

    conversation_id = str(uuid4())

    create_conversation(conversation_id)

    return {
        "conversation_id": conversation_id,
        "title": "New Chat",
        "message": "Conversation created successfully"
    }


# Retrieve all conversations
@router.get("/conversations")
def list_conversations():

    conversations = get_conversations()

    return {
        "total": len(conversations),
        "conversations": conversations
    }