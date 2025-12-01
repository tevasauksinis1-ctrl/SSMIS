"""About dialog for the LLM Chat application."""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from llm_chat import __version__


class AboutDialog(QDialog):
    """About dialog showing application information."""
    
    def __init__(self, parent=None):
        """Initialize the about dialog.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the UI."""
        self.setWindowTitle("About LLM Chat")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("LLM Chat")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Version
        version = QLabel(f"Version {__version__}")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        # Description
        desc = QLabel(
            "A local LLM chat interface supporting Ollama and LM Studio models.\n\n"
            "Features:\n"
            "• Multi-model support with hot-switching\n"
            "• OpenAI-compatible TTS integration\n"
            "• MCP memory server for persistent context\n"
            "• System tray operation\n"
            "• CUDA GPU acceleration support"
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Copyright
        copyright_label = QLabel("© 2024 SSMIS")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #094771;
                color: #ffffff;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
