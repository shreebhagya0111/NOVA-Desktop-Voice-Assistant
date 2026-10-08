from app.database import get_db_connection


# Retrieve conversation history
def get_history(conversation_id: str):

    connection = get_db_connection()

    cursor = connection.execute(
        """
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
        """,
        (conversation_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "role": row["role"],
            "content": row["content"]
        }
        for row in rows
    ]


# Save a message
def add_message(conversation_id: str, role: str, content: str):

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO messages (conversation_id, role, content)
        VALUES (?, ?, ?)
        """,
        (conversation_id, role, content)
    )

    connection.commit()
    connection.close()
    
# Retrieve only recent conversation messages
def get_recent_history(conversation_id: str, limit: int = 10):

    connection = get_db_connection()

    cursor = connection.execute(
        """
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (conversation_id, limit)
    )

    rows = cursor.fetchall()
    connection.close()

    # Reverse to maintain chronological order
    return [
        {
            "role": row["role"],
            "content": row["content"]
        }
        for row in reversed(rows)
    ]
def create_conversation(conversation_id: str, title: str = "New Chat"):

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO conversations (conversation_id, title)
        VALUES (?, ?)
        """,
        (conversation_id, title)
    )

    connection.commit()
    connection.close()
def get_conversations():

    connection = get_db_connection()

    cursor = connection.execute(
        """
        SELECT conversation_id, title, created_at, updated_at
        FROM conversations
        ORDER BY updated_at DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        dict(row)
        for row in rows
    ]
def update_conversation_title(conversation_id: str, title: str):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE conversations
        SET title = ?, updated_at = CURRENT_TIMESTAMP
        WHERE conversation_id = ?
        """,
        (title, conversation_id)
    )

    connection.commit()
    connection.close()  

# Retrieve messages from previous conversations
def get_previous_conversation_messages(current_conversation_id: str, limit: int = 20):

    connection = get_db_connection()

    cursor = connection.execute(
        """
        SELECT
            m.conversation_id,
            c.title,
            m.role,
            m.content
        FROM messages m
        LEFT JOIN conversations c
        ON m.conversation_id = c.conversation_id
        WHERE m.conversation_id != ?
        ORDER BY m.id DESC
        LIMIT ?
        """,
        (current_conversation_id, limit)
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        dict(row)
        for row in reversed(rows)
    ]  