"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent

from ..services import ProfileManager, NetworkService, NetworkAdapterInfo
from ..models import NetworkProfile
from .styles import COLORS
from .profile_editor import ProfileEditorDialog
from .password_dialog import PasswordDialog


class ProfileListItem(QWidget):
    """Custom widget for displaying a profile in the list."""

    edit_clicked = pyqtSignal(str)

    def __init__(self, profile: NetworkProfile, is_active: bool = False):
        super().__init__()
        self.profile = profile
        self._setup_ui(is_active)

    def _setup_ui(self, is_active: bool) -> None:
        """Set up the UI."""
        # Use transparent background - let QListWidget handle selection styling
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumHeight(90)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Profile info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Name row with badges
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)

        name_label = QLabel(self.profile.name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #1a1a1a; background: transparent;")
        name_layout.addWidget(name_label)

        if self.profile.is_default:
            default_badge = QLabel("DEFAULT")
            default_badge.setStyleSheet("""
                background-color: #FF9800;
                color: white;
                font-size: 9px;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 3px;
            """)
            name_layout.addWidget(default_badge)

        if is_active:
            active_badge = QLabel("ACTIVE")
            active_badge.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                font-size: 9px;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 3px;
            """)
            name_layout.addWidget(active_badge)

        name_layout.addStretch()
        info_layout.addLayout(name_layout)

        # Network info - show IP and Gateway
        ns = self.profile.network_settings
        if ns.use_dhcp:
            ip_text = "DHCP"
            gw_text = "Auto"
        else:
            ip_text = ns.ip_address or "Not set"
            gw_text = ns.gateway or "Not set"

        network_label = QLabel(f"IP: {ip_text}  |  Gateway: {gw_text}")
        network_label.setStyleSheet("font-size: 12px; color: #333333; background: transparent;")
        info_layout.addWidget(network_label)

        # DNS info
        dns_text = "Auto" if ns.use_dhcp_dns else (ns.primary_dns or "Not set")
        dns_label = QLabel(f"DNS: {dns_text}")
        dns_label.setStyleSheet("font-size: 11px; color: #555555; background: transparent;")
        info_layout.addWidget(dns_label)

        # Proxy info
        ps = self.profile.proxy_settings
        proxy_text = ps.full_proxy_address if ps.enabled else "Disabled"
        proxy_color = "#2196F3" if ps.enabled else "#666666"
        proxy_label = QLabel(f"Proxy: {proxy_text}")
        proxy_label.setStyleSheet(f"font-size: 11px; color: {proxy_color}; background: transparent;")
        info_layout.addWidget(proxy_label)

        # Route rules count if any
        if hasattr(self.profile, 'route_rules') and self.profile.route_rules:
            rules_label = QLabel(f"Routes: {len(self.profile.route_rules)} custom rule(s)")
            rules_label.setStyleSheet("font-size: 10px; color: #9C27B0; background: transparent;")
            info_layout.addWidget(rules_label)

        layout.addLayout(info_layout, 1)

        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2196F3;
                border: 1px solid #2196F3;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
            }
        """)
        edit_btn.setFixedWidth(60)
        edit_btn.setFixedHeight(28)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.profile.id))
        layout.addWidget(edit_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    def sizeHint(self):
        """Return size hint for the widget."""
        from PyQt6.QtCore import QSize
        return QSize(400, 100)


class MainWindow(QMainWindow):
    """Main application window."""

    minimize_to_tray = pyqtSignal()
    profile_applied = pyqtSignal(NetworkProfile)

    def __init__(self, profile_manager: ProfileManager):
        super().__init__()
        self._profile_manager = profile_manager
        self._network_service = NetworkService()
        self._adapters: list[NetworkAdapterInfo] = []
        self._selected_profile_id: str | None = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        """Set up the main window UI."""
        self.setWindowTitle("Gateway Switcher")
        self.setMinimumSize(500, 600)
        self.resize(500, 650)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Adapter selection
        adapter_card = self._create_adapter_section()
        layout.addWidget(adapter_card)

        # Profiles list
        profiles_card = self._create_profiles_section()
        layout.addWidget(profiles_card, 1)

        # Action buttons
        actions = self._create_action_buttons()
        layout.addLayout(actions)

        # Status bar
        status = self._create_status_bar()
        layout.addWidget(status)

    def _create_header(self) -> QWidget:
        """Create the header section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Gateway Switcher")
        title.setProperty("class", "title")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Manage your network profiles")
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']};")
        layout.addWidget(subtitle)

        return widget

    def _create_adapter_section(self) -> QFrame:
        """Create the network adapter selection section."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["surface"]};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(card)

        # Title
        title = QLabel("Network Adapter")
        title.setStyleSheet("font-weight: 600;")
        layout.addWidget(title)

        # Combo and refresh button
        combo_layout = QHBoxLayout()
        self._adapter_combo = QComboBox()
        self._adapter_combo.currentIndexChanged.connect(self._on_adapter_changed)
        combo_layout.addWidget(self._adapter_combo, 1)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.setFixedWidth(80)
        refresh_btn.clicked.connect(self._refresh_adapters)
        combo_layout.addWidget(refresh_btn)
        layout.addLayout(combo_layout)

        # Status indicator
        status_layout = QHBoxLayout()
        self._status_indicator = QLabel("●")
        self._status_indicator.setStyleSheet(f"color: {COLORS['error']};")
        status_layout.addWidget(self._status_indicator)

        self._status_label = QLabel("Not Connected")
        self._status_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        status_layout.addWidget(self._status_label)

        status_layout.addWidget(QLabel(" | "))

        self._ip_label = QLabel("No IP")
        self._ip_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        status_layout.addWidget(self._ip_label)

        status_layout.addStretch()
        layout.addLayout(status_layout)

        return card

    def _create_profiles_section(self) -> QFrame:
        """Create the profiles list section."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["surface"]};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(card)

        # Header with add button
        header = QHBoxLayout()
        title = QLabel("Network Profiles")
        title.setStyleSheet("font-weight: 600; font-size: 16px;")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+ Add")
        add_btn.setFixedWidth(80)
        add_btn.clicked.connect(self._add_profile)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # Profile list
        self._profile_list = QListWidget()
        self._profile_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._profile_list.itemClicked.connect(self._on_profile_selected)
        self._profile_list.itemDoubleClicked.connect(self._apply_selected_profile)
        layout.addWidget(self._profile_list, 1)

        # Empty state
        self._empty_label = QLabel("No profiles yet\nClick '+ Add' to create your first profile")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._empty_label)

        return card

    def _create_action_buttons(self) -> QHBoxLayout:
        """Create the action buttons."""
        layout = QHBoxLayout()

        self._apply_btn = QPushButton("Apply Selected Profile")
        self._apply_btn.clicked.connect(self._apply_selected_profile)
        self._apply_btn.setEnabled(False)
        layout.addWidget(self._apply_btn)

        layout.addStretch()

        self._duplicate_btn = QPushButton("Duplicate")
        self._duplicate_btn.setProperty("class", "secondary")
        self._duplicate_btn.clicked.connect(self._duplicate_profile)
        self._duplicate_btn.setEnabled(False)
        layout.addWidget(self._duplicate_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setProperty("class", "danger")
        self._delete_btn.clicked.connect(self._delete_profile)
        self._delete_btn.setEnabled(False)
        layout.addWidget(self._delete_btn)

        update_btn = QPushButton("Update Default")
        update_btn.setProperty("class", "secondary")
        update_btn.setToolTip("Update default profile with current settings (requires password)")
        update_btn.clicked.connect(self._update_default_profile)
        layout.addWidget(update_btn)

        return layout

    def _create_status_bar(self) -> QFrame:
        """Create the status bar."""
        card = QFrame()
        card.setStyleSheet(f"background-color: {COLORS['surface']}; border-radius: 4px; padding: 8px;")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)

        self._status_message = QLabel("Ready")
        self._status_message.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._status_message)

        layout.addStretch()

        minimize_btn = QPushButton("Minimize to Tray")
        minimize_btn.setProperty("class", "secondary")
        minimize_btn.setFixedHeight(28)
        minimize_btn.clicked.connect(self._minimize_to_tray)
        layout.addWidget(minimize_btn)

        return card

    def _load_data(self) -> None:
        """Load initial data."""
        self._refresh_adapters()
        self._refresh_profiles()

        # Select saved adapter
        saved_adapter = self._profile_manager.collection.settings.selected_adapter_name
        for i in range(self._adapter_combo.count()):
            if self._adapter_combo.itemData(i) == saved_adapter:
                self._adapter_combo.setCurrentIndex(i)
                break

    def _refresh_adapters(self) -> None:
        """Refresh the network adapters list."""
        self._adapters = self._network_service.get_network_adapters()
        self._adapter_combo.clear()

        for adapter in self._adapters:
            display = f"{adapter.name} ({adapter.status_text})"
            self._adapter_combo.addItem(display, adapter.name)

        self._update_adapter_status()

    def _on_adapter_changed(self, index: int) -> None:
        """Handle adapter selection change."""
        if index >= 0:
            adapter_name = self._adapter_combo.itemData(index)
            self._profile_manager.collection.settings.selected_adapter_name = adapter_name
            self._profile_manager.save()
            self._update_adapter_status()

    def _update_adapter_status(self) -> None:
        """Update the adapter status display."""
        index = self._adapter_combo.currentIndex()
        if index >= 0 and index < len(self._adapters):
            adapter = self._adapters[index]
            if adapter.is_connected:
                self._status_indicator.setStyleSheet(f"color: {COLORS['success']};")
                self._status_label.setText("Connected")
            else:
                self._status_indicator.setStyleSheet(f"color: {COLORS['error']};")
                self._status_label.setText("Disconnected")

            self._ip_label.setText(adapter.ip_address or "No IP")

    def _refresh_profiles(self) -> None:
        """Refresh the profiles list."""
        self._profile_list.clear()
        profiles = self._profile_manager.collection.profiles
        active_id = self._profile_manager.collection.active_profile_id

        self._empty_label.setVisible(len(profiles) == 0)
        self._profile_list.setVisible(len(profiles) > 0)

        for profile in profiles:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, profile.id)

            widget = ProfileListItem(profile, profile.id == active_id)
            widget.edit_clicked.connect(self._edit_profile)

            item.setSizeHint(widget.sizeHint())
            self._profile_list.addItem(item)
            self._profile_list.setItemWidget(item, widget)

    def _on_profile_selected(self, item: QListWidgetItem) -> None:
        """Handle profile selection."""
        self._selected_profile_id = item.data(Qt.ItemDataRole.UserRole)
        profile = self._profile_manager.get_profile(self._selected_profile_id)

        self._apply_btn.setEnabled(True)
        self._duplicate_btn.setEnabled(True)
        self._delete_btn.setEnabled(profile is not None and not profile.is_default)

    def _add_profile(self) -> None:
        """Add a new profile."""
        profile = NetworkProfile(name="New Profile")
        dialog = ProfileEditorDialog(profile, is_new=True, parent=self)

        if dialog.exec():
            adapter_name = self._adapter_combo.currentData()
            if adapter_name:
                dialog.profile.network_settings.adapter_name = adapter_name
            self._profile_manager.add_profile(dialog.profile)
            self._refresh_profiles()
            self._status_message.setText(f"Created profile: {dialog.profile.name}")

    def _edit_profile(self, profile_id: str) -> None:
        """Edit a profile."""
        profile = self._profile_manager.get_profile(profile_id)
        if not profile:
            return

        dialog = ProfileEditorDialog(profile, is_new=False, parent=self)

        if dialog.exec():
            adapter_name = self._adapter_combo.currentData()
            if adapter_name:
                dialog.profile.network_settings.adapter_name = adapter_name
            self._profile_manager.update_profile(dialog.profile)
            self._refresh_profiles()
            self._status_message.setText(f"Updated profile: {dialog.profile.name}")

    def _apply_selected_profile(self) -> None:
        """Apply the selected profile."""
        if not self._selected_profile_id:
            return

        profile = self._profile_manager.get_profile(self._selected_profile_id)
        if not profile:
            return

        self._status_message.setText(f"Applying {profile.name}...")

        # Ensure adapter is set
        adapter_name = self._adapter_combo.currentData()
        if adapter_name:
            profile.network_settings.adapter_name = adapter_name

        result = self._profile_manager.apply_profile(self._selected_profile_id)
        self._status_message.setText(result.message)

        if result.success:
            self.profile_applied.emit(profile)
            self._refresh_profiles()
            self._refresh_adapters()
        else:
            QMessageBox.warning(self, "Apply Profile", result.message)

    def _duplicate_profile(self) -> None:
        """Duplicate the selected profile."""
        if not self._selected_profile_id:
            return

        try:
            clone = self._profile_manager.duplicate_profile(self._selected_profile_id)
            self._refresh_profiles()
            self._status_message.setText(f"Created copy: {clone.name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _delete_profile(self) -> None:
        """Delete the selected profile."""
        if not self._selected_profile_id:
            return

        profile = self._profile_manager.get_profile(self._selected_profile_id)
        if not profile or profile.is_default:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{profile.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._profile_manager.delete_profile(self._selected_profile_id)
            self._selected_profile_id = None
            self._refresh_profiles()
            self._apply_btn.setEnabled(False)
            self._duplicate_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            self._status_message.setText("Profile deleted.")

    def _update_default_profile(self) -> None:
        """Update the default profile with current settings."""
        dialog = PasswordDialog(self)

        if dialog.exec():
            adapter_name = self._adapter_combo.currentData()
            if not adapter_name:
                QMessageBox.warning(self, "Error", "No adapter selected.")
                return

            result = self._profile_manager.update_default_profile(
                dialog.password,
                adapter_name
            )

            QMessageBox.information(
                self,
                "Success" if result.success else "Error",
                result.message
            )

            if result.success:
                self._refresh_profiles()

    def _minimize_to_tray(self) -> None:
        """Minimize to system tray."""
        self.hide()
        self.minimize_to_tray.emit()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event - minimize to tray instead."""
        event.ignore()
        self._minimize_to_tray()

    def refresh(self) -> None:
        """Refresh all data."""
        self._refresh_adapters()
        self._refresh_profiles()
