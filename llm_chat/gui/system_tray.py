"""System tray manager for background operation."""

from typing import Optional

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QObject


class SystemTrayManager(QObject):
    """Manages the system tray icon and menu."""
    
    show_window_requested = pyqtSignal()
    hide_window_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the system tray manager.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._init_tray()
    
    def _init_tray(self) -> None:
        """Initialize the system tray icon."""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self.parent())
        
        # Use default application icon or create a simple one
        app = QApplication.instance()
        if app:
            self.tray_icon.setIcon(app.style().standardIcon(
                QApplication.style().SP_ComputerIcon
            ))
        
        self.tray_icon.setToolTip("LLM Chat")
        
        # Create context menu
        self.menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window_requested.emit)
        self.menu.addAction(show_action)
        
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide_window_requested.emit)
        self.menu.addAction(hide_action)
        
        self.menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_requested.emit)
        self.menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.menu)
        
        # Handle double click
        self.tray_icon.activated.connect(self._on_activated)
        
        # Show the tray icon
        self.tray_icon.show()
    
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation.
        
        Args:
            reason: Activation reason.
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window_requested.emit()
    
    def show_notification(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information,
        duration: int = 3000
    ) -> None:
        """Show a system notification.
        
        Args:
            title: Notification title.
            message: Notification message.
            icon: Notification icon type.
            duration: Duration in milliseconds.
        """
        if self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(title, message, icon, duration)
    
    def set_icon(self, icon: QIcon) -> None:
        """Set the tray icon.
        
        Args:
            icon: Icon to set.
        """
        self.tray_icon.setIcon(icon)
    
    def set_tooltip(self, tooltip: str) -> None:
        """Set the tray icon tooltip.
        
        Args:
            tooltip: Tooltip text.
        """
        self.tray_icon.setToolTip(tooltip)
    
    def hide(self) -> None:
        """Hide the tray icon."""
        self.tray_icon.hide()
    
    def show(self) -> None:
        """Show the tray icon."""
        self.tray_icon.show()
