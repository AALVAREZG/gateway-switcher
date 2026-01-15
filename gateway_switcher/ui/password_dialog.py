"""Password dialog for updating default profile."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton
)
from PyQt6.QtCore import Qt

from .styles import COLORS


class PasswordDialog(QDialog):
    """Dialog for entering password to update default profile."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.password = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Update Default Profile")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QHBoxLayout()

        icon_label = QLabel("🔒")
        icon_label.setStyleSheet(f"""
            font-size: 32px;
            background-color: {COLORS["accent"]};
            border-radius: 20px;
            padding: 8px;
        """)
        header.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title = QLabel("Password Required")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title)

        subtitle = QLabel("Enter password to update default profile")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        title_layout.addWidget(subtitle)

        header.addLayout(title_layout, 1)
        layout.addLayout(header)

        # Description
        desc = QLabel(
            "This will overwrite the default profile with your current "
            "system network settings."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(desc)

        # Password input
        pass_layout = QVBoxLayout()
        pass_label = QLabel("Password")
        pass_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        pass_layout.addWidget(pass_label)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_edit.returnPressed.connect(self._confirm)
        pass_layout.addWidget(self._password_edit)

        self._error_label = QLabel("Invalid password")
        self._error_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 12px;")
        self._error_label.hide()
        pass_layout.addWidget(self._error_label)

        layout.addLayout(pass_layout)

        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.clicked.connect(self._confirm)
        buttons.addWidget(confirm_btn)

        layout.addLayout(buttons)

        # Focus password field
        self._password_edit.setFocus()

    def _confirm(self) -> None:
        """Confirm the password."""
        password = self._password_edit.text()

        if not password:
            self._error_label.setText("Please enter a password")
            self._error_label.show()
            self._password_edit.setFocus()
            return

        self.password = password
        self.accept()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
