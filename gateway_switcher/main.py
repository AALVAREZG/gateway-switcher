"""Main entry point for Gateway Switcher application."""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from .services import ProfileManager
from .ui import MainWindow, SystemTrayIcon
from .ui.styles import STYLESHEET
from .utils import is_admin, run_as_admin


class GatewaySwitcherApp:
    """Main application class."""

    def __init__(self, app: QApplication):
        self._app = app

        # Apply stylesheet
        self._app.setStyleSheet(STYLESHEET)

        # Initialize services
        self._profile_manager = ProfileManager()
        self._profile_manager.load()

        # Create UI components
        self._main_window = MainWindow(self._profile_manager)
        self._system_tray = SystemTrayIcon(self._profile_manager)

        # Connect signals
        self._main_window.minimize_to_tray.connect(self._on_minimize_to_tray)
        self._main_window.profile_applied.connect(self._on_profile_applied)
        self._system_tray.show_window.connect(self._show_main_window)
        self._system_tray.exit_app.connect(self._exit)
        self._system_tray.profile_applied.connect(self._on_tray_profile_applied)

    def run(self, minimized: bool = False) -> int:
        """Run the application."""
        # Handle first run
        if self._profile_manager.is_first_run:
            self._handle_first_run()

        # Show UI
        self._system_tray.show()

        if not minimized:
            self._main_window.show()
        else:
            self._system_tray.show_message(
                "Gateway Switcher",
                "Running in system tray. Double-click to open."
            )

        return self._app.exec()

    def _handle_first_run(self) -> None:
        """Handle first run initialization."""
        from .services import NetworkService

        network_service = NetworkService()
        adapters = network_service.get_network_adapters()

        if adapters:
            # Use first connected adapter or first adapter
            adapter = next(
                (a for a in adapters if a.is_connected),
                adapters[0]
            )
            self._profile_manager.initialize_first_run(adapter.name)

    def _show_main_window(self) -> None:
        """Show the main window."""
        self._main_window.show()
        self._main_window.activateWindow()
        self._main_window.raise_()

    def _on_minimize_to_tray(self) -> None:
        """Handle minimize to tray."""
        self._system_tray.show_message(
            "Gateway Switcher",
            "Running in system tray. Double-click to open."
        )

    def _on_profile_applied(self, profile) -> None:
        """Handle profile applied from main window."""
        pass  # Could update tray icon here

    def _on_tray_profile_applied(self, profile_id: str) -> None:
        """Handle profile applied from system tray."""
        self._main_window.refresh()

    def _exit(self) -> None:
        """Exit the application."""
        self._system_tray.hide()
        self._app.quit()


def main():
    """Main entry point."""
    # Must create QApplication FIRST before any widgets
    app = QApplication(sys.argv)
    app.setApplicationName("Gateway Switcher")
    app.setApplicationVersion("1.0.0")
    app.setQuitOnLastWindowClosed(False)

    # Check for admin privileges
    if not is_admin():
        reply = QMessageBox.question(
            None,
            "Administrator Required",
            "Gateway Switcher requires administrator privileges to change "
            "network settings.\n\nDo you want to restart with elevated privileges?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if run_as_admin():
                sys.exit(0)
            else:
                QMessageBox.warning(
                    None,
                    "Error",
                    "Failed to obtain administrator privileges."
                )
                sys.exit(1)
        # else: Continue without admin - some features won't work

    # Check for --minimized flag
    minimized = "--minimized" in sys.argv

    # Create and run application (pass existing app)
    gateway_app = GatewaySwitcherApp(app)
    sys.exit(gateway_app.run(minimized=minimized))


if __name__ == "__main__":
    main()
