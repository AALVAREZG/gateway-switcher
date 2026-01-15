"""System tray icon and menu."""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtCore import pyqtSignal, QObject

from ..services import ProfileManager
from ..models import NetworkProfile


def create_icon(text: str = "GS", bg_color: str = "#2196F3", size: int = 64) -> QIcon:
    """Create an icon with text on colored background."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw circle background
    painter.setBrush(QColor(bg_color))
    painter.setPen(QColor(bg_color))
    painter.drawEllipse(2, 2, size - 4, size - 4)

    # Draw text
    painter.setPen(QColor("white"))
    font = QFont("Segoe UI", int(size * 0.35))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x84, text)  # AlignCenter

    painter.end()
    return QIcon(pixmap)


class SystemTrayIcon(QObject):
    """System tray icon with context menu for quick profile switching."""

    show_window = pyqtSignal()
    exit_app = pyqtSignal()
    profile_applied = pyqtSignal(str)  # profile_id

    def __init__(self, profile_manager: ProfileManager, parent=None):
        super().__init__(parent)
        self._profile_manager = profile_manager

        # Create tray icon
        self._tray = QSystemTrayIcon()
        self._tray.setIcon(create_icon("GS", "#2196F3"))
        self._tray.setToolTip("Gateway Switcher")

        # Create context menu
        self._menu = QMenu()
        self._setup_menu()
        self._tray.setContextMenu(self._menu)

        # Connect signals
        self._tray.activated.connect(self._on_activated)

        # Register for profile changes
        profile_manager.on_profiles_changed(self._update_profiles_menu)

    def _setup_menu(self) -> None:
        """Set up the context menu."""
        # Open action
        open_action = self._menu.addAction("Open Gateway Switcher")
        open_action.setFont(open_action.font())
        font = open_action.font()
        font.setBold(True)
        open_action.setFont(font)
        open_action.triggered.connect(self.show_window.emit)

        self._menu.addSeparator()

        # Profiles submenu
        self._profiles_menu = self._menu.addMenu("Switch Profile")
        self._update_profiles_menu()

        self._menu.addSeparator()

        # Exit action
        exit_action = self._menu.addAction("Exit")
        exit_action.triggered.connect(self.exit_app.emit)

    def _update_profiles_menu(self) -> None:
        """Update the profiles submenu."""
        self._profiles_menu.clear()

        profiles = self._profile_manager.collection.profiles
        active_id = self._profile_manager.collection.active_profile_id

        if not profiles:
            no_profiles = self._profiles_menu.addAction("(No profiles)")
            no_profiles.setEnabled(False)
            return

        for profile in profiles:
            action = self._profiles_menu.addAction(profile.name)
            action.setCheckable(True)
            action.setChecked(profile.id == active_id)
            action.setData(profile.id)
            action.triggered.connect(
                lambda checked, pid=profile.id: self._apply_profile(pid)
            )

    def _apply_profile(self, profile_id: str) -> None:
        """Apply a profile from the tray menu."""
        result = self._profile_manager.apply_profile(profile_id)

        # Show notification
        profile = self._profile_manager.get_profile(profile_id)
        title = "Gateway Switcher"

        if result.success:
            self._tray.showMessage(
                title,
                result.message,
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
            self.profile_applied.emit(profile_id)
        else:
            self._tray.showMessage(
                title,
                result.message,
                QSystemTrayIcon.MessageIcon.Warning,
                5000
            )

        self._update_profiles_menu()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window.emit()

    def show(self) -> None:
        """Show the tray icon."""
        self._tray.show()

    def hide(self) -> None:
        """Hide the tray icon."""
        self._tray.hide()

    def show_message(self, title: str, message: str, is_error: bool = False) -> None:
        """Show a balloon notification."""
        icon = (
            QSystemTrayIcon.MessageIcon.Critical if is_error
            else QSystemTrayIcon.MessageIcon.Information
        )
        self._tray.showMessage(title, message, icon, 3000)

    def update_icon(self, connected: bool = True) -> None:
        """Update the tray icon based on connection status."""
        color = "#4CAF50" if connected else "#F44336"
        self._tray.setIcon(create_icon("GS", color))
