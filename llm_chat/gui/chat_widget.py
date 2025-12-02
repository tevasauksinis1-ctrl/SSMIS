"""Chat widget for displaying and sending messages."""

import asyncio
from typing import Optional, List
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QScrollArea, QLabel, QFrame, QSizePolicy,
    QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QKeyEvent

from llm_chat.core.chat_client import ChatClient, Message, Conversation
from llm_chat.services.tts_service import TTSService
from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


class MessageBubble(QFrame):
    """A message bubble widget for displaying chat messages."""
    
    def __init__(self, message: Message, parent=None):
        """Initialize the message bubble.
        
        Args:
            message: The message to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.message = message
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Role label
        role_label = QLabel(self.message.role.capitalize())
        role_label.setStyleSheet("font-weight: bold; font-size: 10px; color: #888;")
        layout.addWidget(role_label)
        
        # Content
        content = QLabel(self.message.content)
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(content)
        
        # Timestamp
        time_str = self.message.timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("font-size: 9px; color: #666;")
        time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(time_label)
        
        # Style based on role
        if self.message.role == "user":
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #094771;
                    border-radius: 10px;
                    margin-left: 50px;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #2d2d2d;
                    border-radius: 10px;
                    margin-right: 50px;
                }
                QLabel {
                    color: #ffffff;
                }
            """)


class ChatInput(QLineEdit):
    """Custom line edit for chat input with key handling."""
    
    submit_requested = pyqtSignal()
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
            self.submit_requested.emit()
        else:
            super().keyPressEvent(event)


class ChatWidget(QWidget):
    """Widget for chat display and input."""
    
    message_sent = pyqtSignal(str)
    response_received = pyqtSignal(str)
    
    def __init__(
        self,
        chat_client: ChatClient,
        tts_service: Optional[TTSService] = None,
        parent=None
    ):
        """Initialize the chat widget.
        
        Args:
            chat_client: Chat client for sending messages.
            tts_service: Optional TTS service for voice output.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.chat_client = chat_client
        self.tts_service = tts_service
        self._tts_enabled = tts_service is not None and tts_service.enabled
        self._is_processing = False
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Messages area
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(10)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.messages_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
        """)
        layout.addWidget(self.scroll_area, 1)
        
        # Streaming response area
        self.streaming_label = QLabel()
        self.streaming_label.setWordWrap(True)
        self.streaming_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 10px;
                border-radius: 10px;
                margin: 5px 50px 5px 10px;
            }
        """)
        self.streaming_label.hide()
        layout.addWidget(self.streaming_label)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = ChatInput()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """)
        self.input_field.submit_requested.connect(self._send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QPushButton:disabled {
                background-color: #555;
            }
        """)
        self.send_button.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_button)
        
        # TTS button
        self.tts_button = QPushButton("🔊")
        self.tts_button.setToolTip("Read last response")
        self.tts_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
        """)
        self.tts_button.clicked.connect(self._speak_last_response)
        self.tts_button.setEnabled(self._tts_enabled)
        input_layout.addWidget(self.tts_button)
        
        layout.addLayout(input_layout)
    
    def _add_message_bubble(self, message: Message) -> None:
        """Add a message bubble to the chat.
        
        Args:
            message: Message to display.
        """
        bubble = MessageBubble(message)
        self.messages_layout.addWidget(bubble)
        
        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self) -> None:
        """Scroll the messages area to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _send_message(self) -> None:
        """Send the current message."""
        message = self.input_field.text().strip()
        if not message or self._is_processing:
            return
        
        self.input_field.clear()
        self._is_processing = True
        self.send_button.setEnabled(False)
        
        # Add user message bubble
        user_msg = Message(role="user", content=message)
        self._add_message_bubble(user_msg)
        
        self.message_sent.emit(message)
        
        # Show streaming area
        self.streaming_label.setText("")
        self.streaming_label.show()
        
        # Send message asynchronously
        def on_token(token: str):
            current = self.streaming_label.text()
            self.streaming_label.setText(current + token)
            QApplication.processEvents()
        
        async def send():
            try:
                response = await self.chat_client.send_message(
                    message,
                    stream=True,
                    on_token=on_token,
                )
                
                # Hide streaming area and add final message
                self.streaming_label.hide()
                
                assistant_msg = Message(
                    role="assistant",
                    content=response,
                    model=self.chat_client.current_model,
                    provider=self.chat_client.current_provider,
                )
                self._add_message_bubble(assistant_msg)
                
                self.response_received.emit(response)
                
                # Auto TTS if enabled
                if self._tts_enabled and self.tts_service:
                    await self._speak_text(response)
                    
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                self.streaming_label.setText(f"Error: {str(e)}")
            finally:
                self._is_processing = False
                self.send_button.setEnabled(True)
        
        # Run async
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(send())
    
    def _speak_last_response(self) -> None:
        """Speak the last assistant response."""
        conversation = self.chat_client.get_conversation()
        for msg in reversed(conversation):
            if msg.role == "assistant":
                async def speak():
                    await self._speak_text(msg.content)
                
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(speak())
                break
    
    async def _speak_text(self, text: str) -> None:
        """Speak text using TTS.
        
        Args:
            text: Text to speak.
        """
        if not self.tts_service or not self._tts_enabled:
            return
        
        try:
            # Generate audio file
            audio_file = await self.tts_service.synthesize_to_temp(text)
            
            # Play audio (platform-specific)
            import subprocess
            import sys
            
            if sys.platform == "darwin":
                subprocess.Popen(["afplay", audio_file])
            elif sys.platform == "win32":
                import winsound
                winsound.PlaySound(audio_file, winsound.SND_FILENAME)
            else:
                # Linux - try various players
                for player in ["mpv", "aplay", "paplay", "ffplay"]:
                    try:
                        subprocess.Popen([player, audio_file])
                        break
                    except FileNotFoundError:
                        continue
                        
        except Exception as e:
            logger.error(f"Error playing TTS audio: {e}")
    
    def set_tts_enabled(self, enabled: bool) -> None:
        """Set TTS enabled state.
        
        Args:
            enabled: Whether TTS is enabled.
        """
        self._tts_enabled = enabled
        self.tts_button.setEnabled(enabled)
    
    def clear(self) -> None:
        """Clear all messages from the chat."""
        # Remove all message bubbles
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.streaming_label.hide()
    
    def load_conversation(self, conversation: Conversation) -> None:
        """Load a conversation into the chat.
        
        Args:
            conversation: Conversation to load.
        """
        self.clear()
        
        # Clear client conversation and reload
        self.chat_client.clear_conversation()
        
        for msg in conversation.messages:
            self._add_message_bubble(msg)
