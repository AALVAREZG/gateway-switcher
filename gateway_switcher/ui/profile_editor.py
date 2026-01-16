"""Profile editor dialog."""

import ipaddress
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QSpinBox, QGroupBox, QFormLayout,
    QScrollArea, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt

from ..models import NetworkProfile, RouteRule
from .styles import COLORS
from .route_rules_editor import RouteRulesEditorDialog


class ProfileEditorDialog(QDialog):
    """Dialog for editing network profile settings."""

    def __init__(self, profile: NetworkProfile, is_new: bool = False, parent=None):
        super().__init__(parent)
        self._is_new = is_new

        # Clone the profile for editing
        self.profile = NetworkProfile(
            id=profile.id,
            name=profile.name,
            is_default=profile.is_default,
            created_at=profile.created_at,
            last_modified=profile.last_modified,
            network_settings=profile.network_settings.clone(),
            proxy_settings=profile.proxy_settings.clone(),
            route_rules=[r.clone() for r in profile.route_rules]
        )
        # Keep original IDs for route rules
        for i, orig in enumerate(profile.route_rules):
            if i < len(self.profile.route_rules):
                self.profile.route_rules[i].id = orig.id

        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        title = "Create New Profile" if self._is_new else "Edit Profile"
        self.setWindowTitle(title)
        self.setMinimumSize(450, 550)
        self.resize(480, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)

        # Profile name
        name_group = self._create_name_section()
        content_layout.addWidget(name_group)

        # Network settings
        network_group = self._create_network_section()
        content_layout.addWidget(network_group)

        # Proxy settings
        proxy_group = self._create_proxy_section()
        content_layout.addWidget(proxy_group)

        # Route rules section
        route_group = self._create_route_rules_section()
        content_layout.addWidget(route_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Buttons
        buttons = self._create_buttons()
        layout.addLayout(buttons)

    def _create_name_section(self) -> QGroupBox:
        """Create the profile name section."""
        group = QGroupBox("Profile Name")
        layout = QVBoxLayout(group)

        self._name_edit = QLineEdit()
        self._name_edit.setMaxLength(50)
        self._name_edit.setPlaceholderText("Enter profile name")
        layout.addWidget(self._name_edit)

        return group

    def _create_network_section(self) -> QGroupBox:
        """Create the network settings section."""
        group = QGroupBox("Network Settings")
        layout = QVBoxLayout(group)

        # DHCP toggle
        self._dhcp_check = QCheckBox("Obtain IP address automatically (DHCP)")
        self._dhcp_check.stateChanged.connect(self._on_dhcp_changed)
        layout.addWidget(self._dhcp_check)

        # Static IP fields
        self._static_ip_widget = QWidget()
        static_layout = QFormLayout(self._static_ip_widget)
        static_layout.setContentsMargins(0, 8, 0, 0)

        self._ip_edit = QLineEdit()
        self._ip_edit.setPlaceholderText("192.168.1.100")
        static_layout.addRow("IP Address:", self._ip_edit)

        self._subnet_edit = QLineEdit()
        self._subnet_edit.setPlaceholderText("255.255.255.0")
        static_layout.addRow("Subnet Mask:", self._subnet_edit)

        self._gateway_edit = QLineEdit()
        self._gateway_edit.setPlaceholderText("192.168.1.1")
        static_layout.addRow("Gateway:", self._gateway_edit)

        layout.addWidget(self._static_ip_widget)

        # DNS section
        layout.addWidget(QLabel(""))  # Spacer

        self._dhcp_dns_check = QCheckBox("Obtain DNS server address automatically")
        self._dhcp_dns_check.stateChanged.connect(self._on_dhcp_dns_changed)
        layout.addWidget(self._dhcp_dns_check)

        self._dns_widget = QWidget()
        dns_layout = QFormLayout(self._dns_widget)
        dns_layout.setContentsMargins(0, 8, 0, 0)

        self._primary_dns_edit = QLineEdit()
        self._primary_dns_edit.setPlaceholderText("8.8.8.8")
        dns_layout.addRow("Primary DNS:", self._primary_dns_edit)

        self._secondary_dns_edit = QLineEdit()
        self._secondary_dns_edit.setPlaceholderText("8.8.4.4")
        dns_layout.addRow("Secondary DNS:", self._secondary_dns_edit)

        layout.addWidget(self._dns_widget)

        return group

    def _create_proxy_section(self) -> QGroupBox:
        """Create the proxy settings section."""
        group = QGroupBox("Proxy Settings")
        layout = QVBoxLayout(group)

        # Proxy enable toggle
        self._proxy_check = QCheckBox("Use a proxy server")
        self._proxy_check.stateChanged.connect(self._on_proxy_changed)
        layout.addWidget(self._proxy_check)

        # Proxy settings
        self._proxy_widget = QWidget()
        proxy_layout = QVBoxLayout(self._proxy_widget)
        proxy_layout.setContentsMargins(0, 8, 0, 0)

        # Server and port
        server_layout = QHBoxLayout()

        server_field = QVBoxLayout()
        server_field.addWidget(QLabel("Proxy Server"))
        self._proxy_server_edit = QLineEdit()
        self._proxy_server_edit.setPlaceholderText("proxy.example.com")
        server_field.addWidget(self._proxy_server_edit)
        server_layout.addLayout(server_field, 2)

        port_field = QVBoxLayout()
        port_field.addWidget(QLabel("Port"))
        self._proxy_port_spin = QSpinBox()
        self._proxy_port_spin.setRange(1, 65535)
        self._proxy_port_spin.setValue(8080)
        port_field.addWidget(self._proxy_port_spin)
        server_layout.addLayout(port_field, 1)

        proxy_layout.addLayout(server_layout)

        # Authentication
        self._auth_check = QCheckBox("Proxy requires authentication")
        self._auth_check.stateChanged.connect(self._on_auth_changed)
        proxy_layout.addWidget(self._auth_check)

        self._auth_widget = QWidget()
        auth_layout = QHBoxLayout(self._auth_widget)
        auth_layout.setContentsMargins(0, 0, 0, 0)

        user_field = QVBoxLayout()
        user_field.addWidget(QLabel("Username"))
        self._proxy_user_edit = QLineEdit()
        user_field.addWidget(self._proxy_user_edit)
        auth_layout.addLayout(user_field)

        pass_field = QVBoxLayout()
        pass_field.addWidget(QLabel("Password"))
        self._proxy_pass_edit = QLineEdit()
        self._proxy_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pass_field.addWidget(self._proxy_pass_edit)
        auth_layout.addLayout(pass_field)

        proxy_layout.addWidget(self._auth_widget)

        # Bypass settings
        self._bypass_local_check = QCheckBox("Bypass proxy for local addresses")
        proxy_layout.addWidget(self._bypass_local_check)

        bypass_layout = QVBoxLayout()
        bypass_layout.addWidget(QLabel("Bypass List (semicolon separated)"))
        self._bypass_edit = QLineEdit()
        self._bypass_edit.setPlaceholderText("localhost;127.0.0.1;*.local")
        bypass_layout.addWidget(self._bypass_edit)
        proxy_layout.addLayout(bypass_layout)

        layout.addWidget(self._proxy_widget)

        return group

    def _create_route_rules_section(self) -> QGroupBox:
        """Create the route rules section."""
        group = QGroupBox("Custom Route Rules")
        layout = QVBoxLayout(group)

        # Description
        desc = QLabel(
            "Configure different gateways or proxy settings for specific domains.\n"
            "Example: Bypass proxy for api.anthropic.com"
        )
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Rules summary
        self._rules_summary = QLabel("No route rules configured")
        self._rules_summary.setStyleSheet("font-size: 13px; padding: 8px 0;")
        layout.addWidget(self._rules_summary)

        # Edit button
        self._edit_rules_btn = QPushButton("Configure Route Rules...")
        self._edit_rules_btn.setProperty("class", "secondary")
        self._edit_rules_btn.clicked.connect(self._edit_route_rules)
        layout.addWidget(self._edit_rules_btn)

        return group

    def _edit_route_rules(self) -> None:
        """Open the route rules editor dialog."""
        dialog = RouteRulesEditorDialog(self.profile.route_rules, parent=self)

        if dialog.exec():
            self.profile.route_rules = dialog.rules
            self._update_rules_summary()

    def _update_rules_summary(self) -> None:
        """Update the route rules summary label."""
        count = len(self.profile.route_rules)
        enabled = sum(1 for r in self.profile.route_rules if r.enabled)

        if count == 0:
            self._rules_summary.setText("No route rules configured")
        elif count == 1:
            rule = self.profile.route_rules[0]
            status = "enabled" if rule.enabled else "disabled"
            self._rules_summary.setText(f"1 rule: {rule.pattern} ({status})")
        else:
            self._rules_summary.setText(f"{count} rules configured ({enabled} enabled)")

    def _create_buttons(self) -> QHBoxLayout:
        """Create the dialog buttons."""
        layout = QHBoxLayout()
        layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Profile")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        return layout

    def _load_values(self) -> None:
        """Load profile values into the form."""
        self._name_edit.setText(self.profile.name)

        # Network settings
        ns = self.profile.network_settings
        self._dhcp_check.setChecked(ns.use_dhcp)
        self._ip_edit.setText(ns.ip_address)
        self._subnet_edit.setText(ns.subnet_mask)
        self._gateway_edit.setText(ns.gateway)
        self._dhcp_dns_check.setChecked(ns.use_dhcp_dns)
        self._primary_dns_edit.setText(ns.primary_dns)
        self._secondary_dns_edit.setText(ns.secondary_dns)

        # Proxy settings
        ps = self.profile.proxy_settings
        self._proxy_check.setChecked(ps.enabled)
        self._proxy_server_edit.setText(ps.proxy_server)
        self._proxy_port_spin.setValue(ps.proxy_port)
        self._auth_check.setChecked(ps.use_authentication)
        self._proxy_user_edit.setText(ps.username)
        self._proxy_pass_edit.setText(ps.password)
        self._bypass_local_check.setChecked(ps.bypass_local)
        self._bypass_edit.setText(ps.bypass_list)

        # Update visibility
        self._on_dhcp_changed()
        self._on_dhcp_dns_changed()
        self._on_proxy_changed()
        self._on_auth_changed()

        # Update route rules summary
        self._update_rules_summary()

    def _on_dhcp_changed(self) -> None:
        """Handle DHCP checkbox change."""
        self._static_ip_widget.setEnabled(not self._dhcp_check.isChecked())

    def _on_dhcp_dns_changed(self) -> None:
        """Handle DHCP DNS checkbox change."""
        self._dns_widget.setEnabled(not self._dhcp_dns_check.isChecked())

    def _on_proxy_changed(self) -> None:
        """Handle proxy checkbox change."""
        self._proxy_widget.setEnabled(self._proxy_check.isChecked())

    def _on_auth_changed(self) -> None:
        """Handle auth checkbox change."""
        self._auth_widget.setEnabled(self._auth_check.isChecked())

    def _validate_ip(self, ip_str: str) -> bool:
        """Validate an IP address string."""
        if not ip_str:
            return False
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False

    def _save(self) -> None:
        """Validate and save the profile."""
        # Validate name
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a profile name.")
            self._name_edit.setFocus()
            return

        # Validate IP settings if not using DHCP
        if not self._dhcp_check.isChecked():
            ip = self._ip_edit.text().strip()
            if not ip:
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter an IP address or enable DHCP."
                )
                return

            if not self._validate_ip(ip):
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a valid IP address."
                )
                return

            subnet = self._subnet_edit.text().strip()
            if subnet and not self._validate_ip(subnet):
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a valid subnet mask."
                )
                return

            gateway = self._gateway_edit.text().strip()
            if gateway and not self._validate_ip(gateway):
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a valid gateway address."
                )
                return

        # Validate DNS if not using DHCP DNS
        if not self._dhcp_dns_check.isChecked():
            primary_dns = self._primary_dns_edit.text().strip()
            if primary_dns and not self._validate_ip(primary_dns):
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a valid primary DNS address."
                )
                return

            secondary_dns = self._secondary_dns_edit.text().strip()
            if secondary_dns and not self._validate_ip(secondary_dns):
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a valid secondary DNS address."
                )
                return

        # Validate proxy settings if enabled
        if self._proxy_check.isChecked():
            server = self._proxy_server_edit.text().strip()
            if not server:
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a proxy server address."
                )
                return

            port = self._proxy_port_spin.value()
            if port <= 0 or port > 65535:
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a valid port number (1-65535)."
                )
                return

        # Save values to profile
        self.profile.name = name

        ns = self.profile.network_settings
        ns.use_dhcp = self._dhcp_check.isChecked()
        ns.ip_address = self._ip_edit.text().strip()
        ns.subnet_mask = self._subnet_edit.text().strip()
        ns.gateway = self._gateway_edit.text().strip()
        ns.use_dhcp_dns = self._dhcp_dns_check.isChecked()
        ns.primary_dns = self._primary_dns_edit.text().strip()
        ns.secondary_dns = self._secondary_dns_edit.text().strip()

        ps = self.profile.proxy_settings
        ps.enabled = self._proxy_check.isChecked()
        ps.proxy_server = self._proxy_server_edit.text().strip()
        ps.proxy_port = self._proxy_port_spin.value()
        ps.use_authentication = self._auth_check.isChecked()
        ps.username = self._proxy_user_edit.text()
        ps.password = self._proxy_pass_edit.text()
        ps.bypass_local = self._bypass_local_check.isChecked()
        ps.bypass_list = self._bypass_edit.text()

        self.accept()
