
import sys
import requests

from uuid import uuid4

from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem
)

BACKEND_URL = "http://127.0.0.1:8001"


# Background worker for AI requests
class ChatWorker(QThread):

    response_received = Signal(str, str)
    error_occurred = Signal(str)

    def __init__(self, message, conversation_id):
        super().__init__()

        self.message = message
        self.conversation_id = conversation_id

    def run(self):
        try:
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={
                    "message": self.message,
                    "conversation_id": self.conversation_id
                },
                timeout=300
            )

            response.raise_for_status()
            data = response.json()

            self.response_received.emit(
                data["reply"],
                data["conversation_id"]
            )

        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(str(e))

        except (ValueError, KeyError) as e:
            self.error_occurred.emit(
                f"Invalid response from NOVA backend: {e}"
            )


# Main NOVA desktop window
class NovaWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("NOVA - Personal AI Assistant")
        self.resize(1000, 650)

        self.settings = QSettings(
            "NOVA",
            "PersonalAssistant"
        )

        self.conversation_id = self.settings.value(
            "conversation_id",
            "shrey_gui_test"
        )

        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # LEFT SIDEBAR
        sidebar_layout = QVBoxLayout()

        sidebar_title = QLabel("NOVA CHATS")

        self.new_chat_button = QPushButton("＋ New Chat")
        self.new_chat_button.clicked.connect(self.new_chat)

        self.conversation_list = QListWidget()
        self.conversation_list.itemClicked.connect(
            self.open_conversation
        )

        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(self.new_chat_button)
        sidebar_layout.addWidget(self.conversation_list)

        # RIGHT CHAT AREA
        chat_layout = QVBoxLayout()

        title = QLabel("NOVA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText(
            "Type your message here..."
        )

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        self.message_input.returnPressed.connect(
            self.send_message
        )

        chat_layout.addWidget(title)
        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(self.message_input)
        chat_layout.addWidget(self.send_button)

        # Combine sidebar and chat area
        main_layout.addLayout(sidebar_layout, 1)
        main_layout.addLayout(chat_layout, 3)

        # Load saved conversations
        self.initialize_conversations()
    # Render Markdown in the chat display
    def append_markdown(self, content):
        current_content = self.chat_display.toMarkdown()
        
        updated_content = current_content + "\n\n" + content
        
        self.chat_display.setMarkdown(updated_content)
        
        self.chat_display.moveCursor(
            QTextCursor.MoveOperation.End
        )

    # Create a conversation through backend
    def create_conversation(self):

        response = requests.post(
            f"{BACKEND_URL}/conversations",
            timeout=10
        )

        response.raise_for_status()

        return response.json()["conversation_id"]

    # Load conversation list from database
    def refresh_conversations(self):

        self.conversation_list.clear()

        try:
            response = requests.get(
                f"{BACKEND_URL}/conversations",
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            for conversation in data.get("conversations", []):

                item = QListWidgetItem(
                    conversation["title"]
                )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    conversation["conversation_id"]
                )

                self.conversation_list.addItem(item)

                if conversation["conversation_id"] == self.conversation_id:
                    self.conversation_list.setCurrentItem(item)

        except requests.exceptions.RequestException as e:
            self.chat_display.append(
                f"NOVA: Could not load conversations. {e}"
            )

    # Initialize active conversation
    def initialize_conversations(self):

        try:
            response = requests.get(
                f"{BACKEND_URL}/conversations",
                timeout=10
            )

            response.raise_for_status()

            conversations = response.json().get(
                "conversations", []
            )

            existing_ids = [
                item["conversation_id"]
                for item in conversations
            ]

            # Create a database record if saved ID is not registered
            if self.conversation_id not in existing_ids:
                self.conversation_id = self.create_conversation()

                self.settings.setValue(
                    "conversation_id",
                    self.conversation_id
                )

            self.refresh_conversations()
            self.load_history()

        except requests.exceptions.RequestException as e:
            self.chat_display.append(
                f"NOVA: Backend connection error. {e}"
            )

    # Open selected conversation
    def open_conversation(self, item):

        conversation_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not conversation_id:
            return

        self.conversation_id = conversation_id

        self.settings.setValue(
            "conversation_id",
            self.conversation_id
        )

        self.load_history()

    # Load saved messages
    def load_history(self):

        self.chat_display.clear()

        try:
            response = requests.get(
                f"{BACKEND_URL}/history/{self.conversation_id}",
                timeout=10
            )

            response.raise_for_status()

            data = response.json()
            messages = data.get("messages", [])

            if not messages:
                self.chat_display.append(
                    "NOVA: Hello Shrey! I'm ready to help. 😊"
                )
                return

            for message in messages:

                role = message["role"]
                content = message["content"]

                if role == "user":
                    self.append_markdown(f"**You:** {content}")
                elif role == "assistant":
                    self.append_markdown(f"**NOVA:** {content}")

        except requests.exceptions.RequestException as e:
            self.chat_display.append(
                f"NOVA: Could not load previous chat. {e}"
            )

    # Start new conversation
    def new_chat(self):

        try:
            self.conversation_id = self.create_conversation()

            self.settings.setValue(
                "conversation_id",
                self.conversation_id
            )

            self.refresh_conversations()

            self.chat_display.clear()

            self.chat_display.append(
                "NOVA: Hello Shrey! Welcome to a new conversation. 😊"
            )

            self.message_input.clear()
            self.message_input.setFocus()

        except requests.exceptions.RequestException as e:
            self.chat_display.append(
                f"NOVA: Could not create new chat. {e}"
            )

    # Send message
    def send_message(self):

        user_message = self.message_input.text().strip()

        if not user_message:
            return

        self.chat_display.append(
            f"\nYou: {user_message}"
        )

        self.message_input.clear()

        self.send_button.setEnabled(False)
        self.new_chat_button.setEnabled(False)
        self.message_input.setEnabled(False)

        self.send_button.setText("Thinking...")

        self.worker = ChatWorker(
            user_message,
            self.conversation_id
        )

        self.worker.response_received.connect(
            self.show_response
        )

        self.worker.error_occurred.connect(
            self.show_error
        )

        self.worker.start()

    # Display AI response
    def show_response(self, reply, conversation_id):

        self.conversation_id = conversation_id

        self.settings.setValue(
            "conversation_id",
            self.conversation_id
        )

        self.append_markdown(f"\n\n**NOVA:** {reply}")

        self.send_button.setText("Send")
        self.send_button.setEnabled(True)
        self.new_chat_button.setEnabled(True)
        self.message_input.setEnabled(True)
        self.message_input.setFocus()

        self.refresh_conversations()

    # Display errors
    def show_error(self, error):

        self.chat_display.append(
            f"\nNOVA Error: {error}"
        )

        self.send_button.setText("Send")
        self.send_button.setEnabled(True)
        self.new_chat_button.setEnabled(True)
        self.message_input.setEnabled(True)
        self.message_input.setFocus()


# Start application
app = QApplication(sys.argv)

window = NovaWindow()
window.show()

sys.exit(app.exec())
