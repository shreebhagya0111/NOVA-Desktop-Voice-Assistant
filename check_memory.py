import sqlite3

connection = sqlite3.connect("nova_memory.db")

cursor = connection.cursor()

cursor.execute("""
    SELECT id, conversation_id, role, content
    FROM messages
    ORDER BY id ASC
""")

messages = cursor.fetchall()

for message in messages:
    print(message)

connection.close()