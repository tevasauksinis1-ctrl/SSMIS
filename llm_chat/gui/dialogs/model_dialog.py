"""Model selection dialog for the LLM Chat application."""

import asyncio
from typing import Tuple, Optional, List

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QComboBox, QDialogButtonBox,
    QGroupBox, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer

from llm_chat.core.model_manager import ModelManager, ModelInfo
from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


class ModelDialog(QDialog):
    """Dialog for selecting LLM models."""
    
    def __init__(self, model_manager: ModelManager, parent=None):
        """Initialize the model dialog.
        
        Args:
            model_manager: Model manager instance.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.model_manager = model_manager
        self._selected_provider: str = model_manager.current_provider
        self._selected_model: str = model_manager.current_model
        
        self._init_ui()
        self._load_models()
    
    def _init_ui(self) -> None:
        """Initialize the UI."""
        self.setWindowTitle("Select Model")
        self.setMinimumSize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # Provider selection
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Provider:")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["ollama", "lm_studio"])
        self.provider_combo.setCurrentText(self._selected_provider)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        layout.addLayout(provider_layout)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Models")
        refresh_btn.clicked.connect(self._refresh_models)
        provider_layout.addWidget(refresh_btn)
        
        # Model list
        models_group = QGroupBox("Available Models")
        models_layout = QVBoxLayout(models_group)
        
        self.model_list = QListWidget()
        self.model_list.itemClicked.connect(self._on_model_clicked)
        self.model_list.itemDoubleClicked.connect(self._on_model_double_clicked)
        models_layout.addWidget(self.model_list)
        
        # Progress bar for loading
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.hide()
        models_layout.addWidget(self.progress_bar)
        
        layout.addWidget(models_group)
        
        # Model info
        info_group = QGroupBox("Model Information")
        info_layout = QVBoxLayout(info_group)
        
        self.info_label = QLabel("Select a model to view details")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                left: 10px;
            }
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                padding: 4px;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #094771;
                color: #ffffff;
                border: none;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
    
    def _load_models(self) -> None:
        """Load models from cache or refresh."""
        cached = self.model_manager.get_cached_models()
        if cached:
            self._update_model_list()
        else:
            self._refresh_models()
    
    def _refresh_models(self) -> None:
        """Refresh the model list from providers."""
        self.progress_bar.show()
        self.model_list.clear()
        
        async def refresh():
            try:
                await self.model_manager.refresh_models()
            except Exception as e:
                logger.error(f"Failed to refresh models: {e}")
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(refresh())
        
        self.progress_bar.hide()
        self._update_model_list()
    
    def _update_model_list(self) -> None:
        """Update the model list widget."""
        self.model_list.clear()
        
        provider = self.provider_combo.currentText()
        models = self.model_manager.get_cached_models(provider)
        
        for model in models.get(provider, []):
            item = QListWidgetItem(model.name)
            item.setData(Qt.UserRole, model)
            
            if model.name == self._selected_model and provider == self._selected_provider:
                item.setSelected(True)
            
            self.model_list.addItem(item)
        
        if self.model_list.count() == 0:
            item = QListWidgetItem("No models available")
            item.setFlags(Qt.NoItemFlags)
            self.model_list.addItem(item)
    
    def _on_provider_changed(self, provider: str) -> None:
        """Handle provider selection change.
        
        Args:
            provider: Selected provider.
        """
        self._selected_provider = provider
        self._update_model_list()
    
    def _on_model_clicked(self, item: QListWidgetItem) -> None:
        """Handle model item click.
        
        Args:
            item: Clicked item.
        """
        model_info = item.data(Qt.UserRole)
        if model_info:
            self._selected_model = model_info.name
            self._update_info(model_info)
    
    def _on_model_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle model item double click.
        
        Args:
            item: Clicked item.
        """
        model_info = item.data(Qt.UserRole)
        if model_info:
            self._selected_model = model_info.name
            self.accept()
    
    def _update_info(self, model_info: ModelInfo) -> None:
        """Update the model info display.
        
        Args:
            model_info: Model information.
        """
        info_parts = [f"<b>Name:</b> {model_info.name}"]
        
        if model_info.family:
            info_parts.append(f"<b>Family:</b> {model_info.family}")
        
        if model_info.parameters:
            info_parts.append(f"<b>Parameters:</b> {model_info.parameters}")
        
        if model_info.quantization:
            info_parts.append(f"<b>Quantization:</b> {model_info.quantization}")
        
        if model_info.size:
            # Format size nicely
            try:
                size_mb = int(model_info.size) / (1024 * 1024)
                if size_mb > 1024:
                    size_str = f"{size_mb / 1024:.1f} GB"
                else:
                    size_str = f"{size_mb:.0f} MB"
                info_parts.append(f"<b>Size:</b> {size_str}")
            except (ValueError, TypeError):
                info_parts.append(f"<b>Size:</b> {model_info.size}")
        
        if model_info.modified:
            info_parts.append(f"<b>Modified:</b> {model_info.modified.strftime('%Y-%m-%d %H:%M')}")
        
        self.info_label.setText("<br>".join(info_parts))
    
    def get_selection(self) -> Tuple[str, str]:
        """Get the selected provider and model.
        
        Returns:
            Tuple of (provider, model).
        """
        return (self._selected_provider, self._selected_model)
