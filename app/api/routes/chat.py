
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest
from app.services.ai_service import generate_response

from app.services.memory_service import (
    get_history,
    get_recent_history,
    get_previous_conversation_messages,
    add_message,
    update_conversation_title
)

import requests

router = APIRouter()


# Send a message to NOVA
@router.post("/chat")
def chat(request: ChatRequest):

    # Identify the conversation
    conversation_id = request.conversation_id or str(uuid4())

    user_message = request.message.strip()

    try:
        # Check whether this is the first message
        previous_history = get_history(conversation_id)

        if not previous_history:

            # Generate conversation title from first message
            title = user_message[:35]

            if len(user_message) > 35:
                title += "..."

            # Save title in SQLite
            update_conversation_title(conversation_id, title)

        # Save user's message in SQLite
        add_message(conversation_id, "user", user_message)

        # Retrieve latest 10 messages from current conversation
        history = get_recent_history(
            conversation_id,
            limit=10
        )

        # Retrieve messages from previous conversations
        previous_messages = get_previous_conversation_messages(
            conversation_id,
            limit=50
        )

        # Prepare historical memory context
        if previous_messages:

            memory_context = (
                "The following information comes from the user's "
                "previous conversations with NOVA.\n\n"
            )

            for item in previous_messages:

                memory_context += (
                    f"Conversation: {item['title']}\n"
                    f"{item['role']}: {item['content']}\n\n"
                )

            memory_context += (
                "Use these previous conversations when relevant. "
                "If the user asks about a previous topic, answer "
                "using the retrieved information. "
                "Do not invent memories. If the information is "
                "not available, say so honestly."
            )

            # Add memory context to AI input
            history.insert(
                0,
                {
                    "role": "system",
                    "content": memory_context
                }
            )

        # Generate AI response
        ai_reply = generate_response(history)

        # Save NOVA's response in SQLite
        add_message(conversation_id, "assistant", ai_reply)

        # Return response to GUI or API
        return {
            "conversation_id": conversation_id,
            "user_message": user_message,
            "reply": ai_reply,
            "model": "qwen2.5:3b"
        }

    except requests.exceptions.RequestException as e:

        print(f"Ollama Error: {type(e).__name__}: {e}")

        raise HTTPException(
            status_code=503,
            detail="NOVA AI is currently unavailable."
        )


# Retrieve complete conversation history
@router.get("/history/{conversation_id}")
def chat_history(conversation_id: str):

    history = get_history(conversation_id)

    return {
        "conversation_id": conversation_id,
        "total_messages": len(history),
        "messages": history
    }
