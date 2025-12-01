"""Settings dialog for the LLM Chat application."""

from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QPushButton, QLabel, QGroupBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt

from llm_chat.config.settings import Settings


class SettingsDialog(QDialog):
    """Dialog for editing application settings."""
    
    def __init__(self, settings: Settings, parent=None):
        """Initialize the settings dialog.
        
        Args:
            settings: Current settings.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self.settings = settings
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self) -> None:
        """Initialize the UI."""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # General tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        general_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        general_layout.addRow("Font Size:", self.font_size_spin)
        
        self.start_minimized_check = QCheckBox()
        general_layout.addRow("Start Minimized:", self.start_minimized_check)
        
        self.minimize_to_tray_check = QCheckBox()
        general_layout.addRow("Minimize to Tray:", self.minimize_to_tray_check)
        
        self.show_tray_check = QCheckBox()
        general_layout.addRow("Show System Tray:", self.show_tray_check)
        
        self.tabs.addTab(general_tab, "General")
        
        # Model tab
        model_tab = QWidget()
        model_layout = QFormLayout(model_tab)
        
        self.default_provider_combo = QComboBox()
        self.default_provider_combo.addItems(["ollama", "lm_studio"])
        model_layout.addRow("Default Provider:", self.default_provider_combo)
        
        self.default_model_edit = QLineEdit()
        model_layout.addRow("Default Model:", self.default_model_edit)
        
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        model_layout.addRow("Temperature:", self.temperature_spin)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 32000)
        self.max_tokens_spin.setSingleStep(256)
        model_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        self.context_length_spin = QSpinBox()
        self.context_length_spin.setRange(1, 128000)
        self.context_length_spin.setSingleStep(1024)
        model_layout.addRow("Context Length:", self.context_length_spin)
        
        self.tabs.addTab(model_tab, "Model")
        
        # Ports tab
        ports_tab = QWidget()
        ports_layout = QFormLayout(ports_tab)
        
        self.ollama_port_spin = QSpinBox()
        self.ollama_port_spin.setRange(1, 65535)
        ports_layout.addRow("Ollama Port:", self.ollama_port_spin)
        
        self.lm_studio_port_spin = QSpinBox()
        self.lm_studio_port_spin.setRange(1, 65535)
        ports_layout.addRow("LM Studio Port:", self.lm_studio_port_spin)
        
        self.tts_port_spin = QSpinBox()
        self.tts_port_spin.setRange(1, 65535)
        ports_layout.addRow("TTS Port:", self.tts_port_spin)
        
        self.mcp_port_spin = QSpinBox()
        self.mcp_port_spin.setRange(1, 65535)
        ports_layout.addRow("MCP Memory Port:", self.mcp_port_spin)
        
        self.tabs.addTab(ports_tab, "Ports")
        
        # TTS tab
        tts_tab = QWidget()
        tts_layout = QFormLayout(tts_tab)
        
        self.tts_enabled_check = QCheckBox()
        tts_layout.addRow("Enable TTS:", self.tts_enabled_check)
        
        self.tts_api_edit = QLineEdit()
        tts_layout.addRow("API URL:", self.tts_api_edit)
        
        self.tts_model_edit = QLineEdit()
        tts_layout.addRow("Model:", self.tts_model_edit)
        
        self.tts_voice_combo = QComboBox()
        self.tts_voice_combo.addItems(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
        tts_layout.addRow("Voice:", self.tts_voice_combo)
        
        self.tts_speed_spin = QDoubleSpinBox()
        self.tts_speed_spin.setRange(0.25, 4.0)
        self.tts_speed_spin.setSingleStep(0.1)
        tts_layout.addRow("Speed:", self.tts_speed_spin)
        
        self.tabs.addTab(tts_tab, "TTS")
        
        # MCP tab
        mcp_tab = QWidget()
        mcp_layout = QFormLayout(mcp_tab)
        
        self.mcp_enabled_check = QCheckBox()
        mcp_layout.addRow("Enable MCP:", self.mcp_enabled_check)
        
        self.mcp_host_edit = QLineEdit()
        mcp_layout.addRow("Host:", self.mcp_host_edit)
        
        self.mcp_memory_file_edit = QLineEdit()
        mcp_layout.addRow("Memory File:", self.mcp_memory_file_edit)
        
        self.tabs.addTab(mcp_tab, "MCP")
        
        # CUDA tab
        cuda_tab = QWidget()
        cuda_layout = QFormLayout(cuda_tab)
        
        self.cuda_enabled_check = QCheckBox()
        cuda_layout.addRow("Enable CUDA:", self.cuda_enabled_check)
        
        self.cuda_version_combo = QComboBox()
        self.cuda_version_combo.addItems(["12.1", "12.8", "11.8", "11.7"])
        cuda_layout.addRow("CUDA Version:", self.cuda_version_combo)
        
        self.cuda_device_spin = QSpinBox()
        self.cuda_device_spin.setRange(0, 7)
        cuda_layout.addRow("Device ID:", self.cuda_device_spin)
        
        self.tabs.addTab(cuda_tab, "CUDA")
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._restore_defaults)
        layout.addWidget(button_box)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabWidget::pane {
                background-color: #252526;
                border: 1px solid #3c3c3c;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #094771;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                padding: 4px;
            }
            QCheckBox {
                color: #ffffff;
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
    
    def _load_settings(self) -> None:
        """Load current settings into UI."""
        # General
        self.theme_combo.setCurrentText(self.settings.ui.theme)
        self.font_size_spin.setValue(self.settings.ui.font_size)
        self.start_minimized_check.setChecked(self.settings.ui.start_minimized)
        self.minimize_to_tray_check.setChecked(self.settings.ui.minimize_to_tray)
        self.show_tray_check.setChecked(self.settings.ui.show_system_tray)
        
        # Model
        self.default_provider_combo.setCurrentText(self.settings.model.default_provider)
        self.default_model_edit.setText(self.settings.model.default_model)
        self.temperature_spin.setValue(self.settings.model.temperature)
        self.max_tokens_spin.setValue(self.settings.model.max_tokens)
        self.context_length_spin.setValue(self.settings.model.context_length)
        
        # Ports
        self.ollama_port_spin.setValue(self.settings.ports.ollama)
        self.lm_studio_port_spin.setValue(self.settings.ports.lm_studio)
        self.tts_port_spin.setValue(self.settings.ports.tts)
        self.mcp_port_spin.setValue(self.settings.ports.mcp_memory)
        
        # TTS
        self.tts_enabled_check.setChecked(self.settings.tts.enabled)
        self.tts_api_edit.setText(self.settings.tts.api_url)
        self.tts_model_edit.setText(self.settings.tts.model)
        self.tts_voice_combo.setCurrentText(self.settings.tts.voice)
        self.tts_speed_spin.setValue(self.settings.tts.speed)
        
        # MCP
        self.mcp_enabled_check.setChecked(self.settings.mcp.enabled)
        self.mcp_host_edit.setText(self.settings.mcp.host)
        self.mcp_memory_file_edit.setText(self.settings.mcp.memory_file)
        
        # CUDA
        self.cuda_enabled_check.setChecked(self.settings.cuda.enabled)
        self.cuda_version_combo.setCurrentText(self.settings.cuda.cuda_version)
        self.cuda_device_spin.setValue(self.settings.cuda.device_id)
    
    def _restore_defaults(self) -> None:
        """Restore default settings."""
        self.settings = Settings()
        self._load_settings()
    
    def get_settings(self) -> Settings:
        """Get the edited settings.
        
        Returns:
            Updated Settings object.
        """
        from llm_chat.config.settings import (
            Settings, ServicePorts, TTSSettings, ModelSettings,
            MCPSettings, UISettings, CUDASettings
        )
        
        return Settings(
            ports=ServicePorts(
                ollama=self.ollama_port_spin.value(),
                lm_studio=self.lm_studio_port_spin.value(),
                tts=self.tts_port_spin.value(),
                mcp_memory=self.mcp_port_spin.value(),
            ),
            tts=TTSSettings(
                enabled=self.tts_enabled_check.isChecked(),
                api_url=self.tts_api_edit.text(),
                model=self.tts_model_edit.text(),
                voice=self.tts_voice_combo.currentText(),
                speed=self.tts_speed_spin.value(),
            ),
            model=ModelSettings(
                default_provider=self.default_provider_combo.currentText(),
                default_model=self.default_model_edit.text(),
                temperature=self.temperature_spin.value(),
                max_tokens=self.max_tokens_spin.value(),
                context_length=self.context_length_spin.value(),
            ),
            mcp=MCPSettings(
                enabled=self.mcp_enabled_check.isChecked(),
                host=self.mcp_host_edit.text(),
                port=self.mcp_port_spin.value(),
                memory_file=self.mcp_memory_file_edit.text(),
            ),
            ui=UISettings(
                theme=self.theme_combo.currentText(),
                font_size=self.font_size_spin.value(),
                start_minimized=self.start_minimized_check.isChecked(),
                minimize_to_tray=self.minimize_to_tray_check.isChecked(),
                show_system_tray=self.show_tray_check.isChecked(),
            ),
            cuda=CUDASettings(
                enabled=self.cuda_enabled_check.isChecked(),
                cuda_version=self.cuda_version_combo.currentText(),
                device_id=self.cuda_device_spin.value(),
            ),
        )
