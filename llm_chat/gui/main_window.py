"""Main window for the LLM Chat application."""

import asyncio
import sys
from typing import Optional, Dict, Any, List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMenuBar, QMenu,
    QAction, QStatusBar, QSplitter, QListWidget, QListWidgetItem,
    QLabel, QMessageBox, QInputDialog, QFileDialog, QDialog,
    QApplication, QStyle
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QKeySequence

from llm_chat.gui.chat_widget import ChatWidget
from llm_chat.gui.dialogs.settings_dialog import SettingsDialog
from llm_chat.gui.dialogs.model_dialog import ModelDialog
from llm_chat.gui.dialogs.about_dialog import AboutDialog
from llm_chat.gui.system_tray import SystemTrayManager
from llm_chat.core.chat_client import ChatClient
from llm_chat.core.model_manager import ModelManager
from llm_chat.core.history_manager import HistoryManager
from llm_chat.services.tts_service import TTSService
from llm_chat.services.mcp_connector import MCPConnector
from llm_chat.utils.config_manager import ConfigManager
from llm_chat.config.settings import Settings
from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    status_update = pyqtSignal(str)
    model_changed = pyqtSignal(str, str)  # provider, model
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the main window.
        
        Args:
            config_manager: Optional configuration manager.
        """
        super().__init__()
        
        # Configuration
        self.config_manager = config_manager or ConfigManager()
        self.settings = self.config_manager.load()
        
        # Initialize services
        self._init_services()
        
        # Set up UI
        self._init_ui()
        self._init_menus()
        self._init_system_tray()
        self._init_status_bar()
        
        # Load window state
        self._load_window_state()
        
        # Set up async event loop integration
        self._setup_async()
        
        # Initial health check
        QTimer.singleShot(1000, self._check_services_health)
    
    def _init_services(self) -> None:
        """Initialize backend services."""
        # Chat client
        self.chat_client = ChatClient(
            ollama_port=self.settings.ports.ollama,
            lm_studio_port=self.settings.ports.lm_studio,
        )
        
        # Model manager
        self.model_manager = ModelManager(
            ollama_port=self.settings.ports.ollama,
            lm_studio_port=self.settings.ports.lm_studio,
        )
        
        # History manager
        self.history_manager = HistoryManager(self.settings.history_file)
        
        # TTS service
        self.tts_service = TTSService(
            api_url=self.settings.tts.api_url,
            model=self.settings.tts.model,
            voice=self.settings.tts.voice,
            speed=self.settings.tts.speed,
        )
        self.tts_service.enabled = self.settings.tts.enabled
        
        # MCP connector
        self.mcp_connector = MCPConnector(
            host=self.settings.mcp.host,
            port=self.settings.mcp.port,
            memory_file=self.settings.mcp.memory_file,
        )
        self.mcp_connector.enabled = self.settings.mcp.enabled
        
        # Set initial model
        self.chat_client.set_provider(self.settings.model.default_provider)
        self.chat_client.set_model(self.settings.model.default_model)
        self.chat_client.temperature = self.settings.model.temperature
        self.chat_client.max_tokens = self.settings.model.max_tokens
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("LLM Chat")
        self.setMinimumSize(600, 400)
        self.resize(
            self.settings.ui.window_width,
            self.settings.ui.window_height
        )
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout with splitter
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)
        
        # History sidebar
        self.history_list = QListWidget()
        self.history_list.setMaximumWidth(250)
        self.history_list.setMinimumWidth(150)
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        self.splitter.addWidget(self.history_list)
        
        # Chat widget
        self.chat_widget = ChatWidget(
            chat_client=self.chat_client,
            tts_service=self.tts_service,
        )
        self.splitter.addWidget(self.chat_widget)
        
        # Set splitter sizes
        self.splitter.setSizes([200, 600])
        
        # Apply theme
        self._apply_theme()
        
        # Load history
        self._load_history_list()
    
    def _init_menus(self) -> None:
        """Initialize the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Chat", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_chat)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("&Export Chat...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._export_chat)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self._exit_app)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        clear_action = QAction("&Clear Chat", self)
        clear_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_action.triggered.connect(self._clear_chat)
        edit_menu.addAction(clear_action)
        
        edit_menu.addSeparator()
        
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut(QKeySequence.Preferences)
        settings_action.triggered.connect(self._show_settings)
        edit_menu.addAction(settings_action)
        
        # Model menu
        model_menu = menubar.addMenu("&Model")
        
        select_model_action = QAction("&Select Model...", self)
        select_model_action.setShortcut(QKeySequence("Ctrl+M"))
        select_model_action.triggered.connect(self._show_model_dialog)
        model_menu.addAction(select_model_action)
        
        refresh_models_action = QAction("&Refresh Models", self)
        refresh_models_action.setShortcut(QKeySequence.Refresh)
        refresh_models_action.triggered.connect(self._refresh_models)
        model_menu.addAction(refresh_models_action)
        
        model_menu.addSeparator()
        
        # Provider submenu
        provider_menu = model_menu.addMenu("&Provider")
        
        self.ollama_action = QAction("Ollama", self, checkable=True)
        self.ollama_action.triggered.connect(lambda: self._switch_provider("ollama"))
        provider_menu.addAction(self.ollama_action)
        
        self.lm_studio_action = QAction("LM Studio", self, checkable=True)
        self.lm_studio_action.triggered.connect(lambda: self._switch_provider("lm_studio"))
        provider_menu.addAction(self.lm_studio_action)
        
        self._update_provider_menu()
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        toggle_history_action = QAction("Toggle &History Panel", self)
        toggle_history_action.setShortcut(QKeySequence("Ctrl+H"))
        toggle_history_action.triggered.connect(self._toggle_history_panel)
        view_menu.addAction(toggle_history_action)
        
        # TTS menu
        tts_menu = menubar.addMenu("&TTS")
        
        self.tts_enabled_action = QAction("&Enable TTS", self, checkable=True)
        self.tts_enabled_action.setChecked(self.tts_service.enabled)
        self.tts_enabled_action.triggered.connect(self._toggle_tts)
        tts_menu.addAction(self.tts_enabled_action)
        
        tts_menu.addSeparator()
        
        # Voice submenu
        voice_menu = tts_menu.addMenu("&Voice")
        self.voice_actions = []
        for voice in self.tts_service.list_voices():
            action = QAction(voice.capitalize(), self, checkable=True)
            action.triggered.connect(lambda checked, v=voice: self._set_voice(v))
            voice_menu.addAction(action)
            self.voice_actions.append((voice, action))
        
        self._update_voice_menu()
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_system_tray(self) -> None:
        """Initialize system tray icon."""
        if self.settings.ui.show_system_tray:
            self.tray_manager = SystemTrayManager(self)
            self.tray_manager.show_window_requested.connect(self.show)
            self.tray_manager.hide_window_requested.connect(self.hide)
            self.tray_manager.exit_requested.connect(self._exit_app)
    
    def _init_status_bar(self) -> None:
        """Initialize the status bar."""
        self.status_bar = self.statusBar()
        
        # Model label
        self.model_label = QLabel()
        self.status_bar.addPermanentWidget(self.model_label)
        self._update_model_label()
        
        # Status message
        self.status_update.connect(self.status_bar.showMessage)
    
    def _setup_async(self) -> None:
        """Set up async event loop integration."""
        # Timer to process async events
        self.async_timer = QTimer()
        self.async_timer.timeout.connect(self._process_async)
        self.async_timer.start(100)
    
    def _process_async(self) -> None:
        """Process pending async events."""
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.sleep(0))
        except RuntimeError:
            pass
    
    def _apply_theme(self) -> None:
        """Apply the current theme."""
        if self.settings.ui.theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QListWidget {
                    background-color: #252526;
                    color: #ffffff;
                    border: none;
                }
                QListWidget::item:selected {
                    background-color: #094771;
                }
                QMenuBar {
                    background-color: #252526;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #094771;
                }
                QMenu {
                    background-color: #252526;
                    color: #ffffff;
                }
                QMenu::item:selected {
                    background-color: #094771;
                }
                QStatusBar {
                    background-color: #007acc;
                    color: #ffffff;
                }
            """)
    
    def _load_window_state(self) -> None:
        """Load saved window state."""
        settings = QSettings("SSMIS", "LLMChat")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def _save_window_state(self) -> None:
        """Save window state."""
        settings = QSettings("SSMIS", "LLMChat")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
    
    def _load_history_list(self) -> None:
        """Load conversations into history list."""
        self.history_list.clear()
        for conv in self.history_manager.list_conversations(limit=50):
            item = QListWidgetItem(conv.title)
            item.setData(Qt.UserRole, conv.id)
            self.history_list.addItem(item)
    
    def _on_history_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle history item click."""
        conv_id = item.data(Qt.UserRole)
        conv = self.history_manager.get_conversation(conv_id)
        if conv:
            self.chat_widget.load_conversation(conv)
            self.status_update.emit(f"Loaded: {conv.title}")
    
    def _update_model_label(self) -> None:
        """Update the model label in status bar."""
        provider = self.chat_client.current_provider
        model = self.chat_client.current_model
        self.model_label.setText(f"{provider}: {model}")
    
    def _update_provider_menu(self) -> None:
        """Update provider menu checkmarks."""
        provider = self.chat_client.current_provider
        self.ollama_action.setChecked(provider == "ollama")
        self.lm_studio_action.setChecked(provider == "lm_studio")
    
    def _update_voice_menu(self) -> None:
        """Update voice menu checkmarks."""
        current_voice = self.tts_service.voice
        for voice, action in self.voice_actions:
            action.setChecked(voice == current_voice)
    
    def _check_services_health(self) -> None:
        """Check health of backend services."""
        async def check():
            health = await self.chat_client.check_health()
            
            status_parts = []
            if health.get("ollama"):
                status_parts.append("Ollama: ✓")
            else:
                status_parts.append("Ollama: ✗")
            
            if health.get("lm_studio"):
                status_parts.append("LM Studio: ✓")
            else:
                status_parts.append("LM Studio: ✗")
            
            self.status_update.emit(" | ".join(status_parts))
        
        try:
            asyncio.get_event_loop().run_until_complete(check())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(check())
    
    # Menu actions
    def _new_chat(self) -> None:
        """Start a new chat."""
        self.chat_client.clear_conversation()
        self.chat_widget.clear()
        self.status_update.emit("New chat started")
    
    def _clear_chat(self) -> None:
        """Clear current chat."""
        self.chat_client.clear_conversation()
        self.chat_widget.clear()
        self.status_update.emit("Chat cleared")
    
    def _export_chat(self) -> None:
        """Export current chat."""
        if not self.chat_client.get_conversation():
            QMessageBox.information(self, "Export", "No messages to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Chat", "", "Text Files (*.txt);;JSON Files (*.json)"
        )
        if file_path:
            # Create conversation from current messages
            from llm_chat.core.chat_client import Conversation
            import uuid
            conv = Conversation(
                id=str(uuid.uuid4()),
                title="Exported Chat",
                messages=self.chat_client.get_conversation(),
            )
            
            format = "json" if file_path.endswith(".json") else "text"
            content = self.history_manager.export_conversation(conv.id, format)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.status_update.emit(f"Exported to {file_path}")
    
    def _show_settings(self) -> None:
        """Show settings dialog."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            self.config_manager.save(self.settings)
            self._apply_settings()
            self.status_update.emit("Settings saved")
    
    def _show_model_dialog(self) -> None:
        """Show model selection dialog."""
        dialog = ModelDialog(self.model_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            provider, model = dialog.get_selection()
            self.chat_client.set_provider(provider)
            self.chat_client.set_model(model)
            self._update_model_label()
            self._update_provider_menu()
            self.status_update.emit(f"Switched to {model}")
    
    def _refresh_models(self) -> None:
        """Refresh available models."""
        async def refresh():
            await self.model_manager.refresh_models()
            self.status_update.emit("Models refreshed")
        
        try:
            asyncio.get_event_loop().run_until_complete(refresh())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(refresh())
    
    def _switch_provider(self, provider: str) -> None:
        """Switch to a different provider."""
        self.chat_client.set_provider(provider)
        self._update_model_label()
        self._update_provider_menu()
        self.status_update.emit(f"Switched to {provider}")
    
    def _toggle_history_panel(self) -> None:
        """Toggle history panel visibility."""
        if self.history_list.isVisible():
            self.history_list.hide()
        else:
            self.history_list.show()
    
    def _toggle_tts(self, enabled: bool) -> None:
        """Toggle TTS on/off."""
        self.tts_service.enabled = enabled
        self.chat_widget.set_tts_enabled(enabled)
        self.status_update.emit(f"TTS {'enabled' if enabled else 'disabled'}")
    
    def _set_voice(self, voice: str) -> None:
        """Set TTS voice."""
        self.tts_service.set_voice(voice)
        self._update_voice_menu()
        self.status_update.emit(f"Voice set to {voice}")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def _apply_settings(self) -> None:
        """Apply updated settings."""
        # Update services
        self.chat_client.temperature = self.settings.model.temperature
        self.chat_client.max_tokens = self.settings.model.max_tokens
        
        self.tts_service.enabled = self.settings.tts.enabled
        self.tts_service.set_voice(self.settings.tts.voice)
        self.tts_service.set_speed(self.settings.tts.speed)
        
        self.mcp_connector.enabled = self.settings.mcp.enabled
        
        # Update UI
        self._apply_theme()
        self.tts_enabled_action.setChecked(self.settings.tts.enabled)
    
    def _exit_app(self) -> None:
        """Exit the application."""
        self._save_window_state()
        QApplication.quit()
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.settings.ui.minimize_to_tray and hasattr(self, 'tray_manager'):
            event.ignore()
            self.hide()
            self.tray_manager.show_notification("LLM Chat", "Minimized to system tray")
        else:
            self._save_window_state()
            event.accept()
