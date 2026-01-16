"""Route rules editor dialog."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QSpinBox, QGroupBox, QFormLayout,
    QListWidget, QListWidgetItem, QWidget, QMessageBox,
    QComboBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..models import RouteRule
from .styles import COLORS


class RouteRuleItem(QWidget):
    """Widget to display a route rule in the list."""

    edit_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)

    def __init__(self, rule: RouteRule):
        super().__init__()
        self.rule = rule
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI."""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumHeight(70)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Enable indicator
        status_indicator = QLabel("●")
        color = "#4CAF50" if self.rule.enabled else "#9E9E9E"
        status_indicator.setStyleSheet(f"color: {color}; font-size: 16px; background: transparent;")
        layout.addWidget(status_indicator)

        # Rule info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Name and pattern
        name_text = self.rule.name or self.rule.pattern
        name_label = QLabel(name_text)
        name_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #1a1a1a; background: transparent;")
        info_layout.addWidget(name_label)

        # Pattern info
        match_types = {
            "exact": "Exact match",
            "suffix": "Domain & subdomains",
            "contains": "Contains",
            "regex": "Regex pattern"
        }
        match_desc = match_types.get(self.rule.match_type, self.rule.match_type)
        if self.rule.name:
            pattern_label = QLabel(f"Pattern: {self.rule.pattern} ({match_desc})")
        else:
            pattern_label = QLabel(f"{match_desc}")
        pattern_label.setStyleSheet("font-size: 11px; color: #555555; background: transparent;")
        info_layout.addWidget(pattern_label)

        # Action description
        desc_label = QLabel(self.rule.description)
        desc_label.setStyleSheet("font-size: 11px; color: #9C27B0; background: transparent;")
        info_layout.addWidget(desc_label)

        layout.addLayout(info_layout, 1)

        # Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2196F3;
                border: 1px solid #2196F3;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #E3F2FD; }
        """)
        edit_btn.setFixedWidth(50)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.rule.id))
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Del")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #F44336;
                border: 1px solid #F44336;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #FFEBEE; }
        """)
        delete_btn.setFixedWidth(50)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.rule.id))
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(400, 75)


class RouteRuleEditorDialog(QDialog):
    """Dialog for editing a single route rule."""

    def __init__(self, rule: RouteRule, is_new: bool = False, parent=None):
        super().__init__(parent)
        self._is_new = is_new
        self.rule = RouteRule(
            id=rule.id,
            name=rule.name,
            pattern=rule.pattern,
            match_type=rule.match_type,
            enabled=rule.enabled,
            use_custom_gateway=rule.use_custom_gateway,
            custom_gateway=rule.custom_gateway,
            bypass_proxy=rule.bypass_proxy,
            use_custom_proxy=rule.use_custom_proxy,
            custom_proxy_server=rule.custom_proxy_server,
            custom_proxy_port=rule.custom_proxy_port,
            use_custom_dns=rule.use_custom_dns,
            custom_dns=rule.custom_dns
        )
        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        title = "Add Route Rule" if self._is_new else "Edit Route Rule"
        self.setWindowTitle(title)
        self.setMinimumSize(450, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)

        # Description
        desc = QLabel(
            "Create rules to route specific domains differently.\n"
            "E.g., use a different gateway or bypass proxy for certain sites."
        )
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Basic info section
        basic_group = QGroupBox("Rule Configuration")
        basic_layout = QFormLayout(basic_group)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Anthropic API (optional)")
        basic_layout.addRow("Name:", self._name_edit)

        self._pattern_edit = QLineEdit()
        self._pattern_edit.setPlaceholderText("e.g., api.anthropic.com or *.google.com")
        basic_layout.addRow("Pattern:", self._pattern_edit)

        self._match_type_combo = QComboBox()
        self._match_type_combo.addItem("Exact match", "exact")
        self._match_type_combo.addItem("Domain & subdomains", "suffix")
        self._match_type_combo.addItem("Contains", "contains")
        self._match_type_combo.addItem("Regex", "regex")
        basic_layout.addRow("Match Type:", self._match_type_combo)

        self._enabled_check = QCheckBox("Rule is enabled")
        self._enabled_check.setChecked(True)
        basic_layout.addRow("", self._enabled_check)

        layout.addWidget(basic_group)

        # Gateway override section
        gateway_group = QGroupBox("Gateway Override")
        gateway_layout = QVBoxLayout(gateway_group)

        self._use_gateway_check = QCheckBox("Use custom gateway for matching traffic")
        self._use_gateway_check.stateChanged.connect(self._on_gateway_changed)
        gateway_layout.addWidget(self._use_gateway_check)

        self._gateway_widget = QWidget()
        gw_layout = QFormLayout(self._gateway_widget)
        gw_layout.setContentsMargins(20, 8, 0, 0)
        self._gateway_edit = QLineEdit()
        self._gateway_edit.setPlaceholderText("e.g., 10.0.0.1")
        gw_layout.addRow("Gateway IP:", self._gateway_edit)
        gateway_layout.addWidget(self._gateway_widget)

        layout.addWidget(gateway_group)

        # Proxy override section
        proxy_group = QGroupBox("Proxy Override")
        proxy_layout = QVBoxLayout(proxy_group)

        self._bypass_proxy_check = QCheckBox("Bypass proxy for matching traffic (direct connection)")
        self._bypass_proxy_check.stateChanged.connect(self._on_proxy_changed)
        proxy_layout.addWidget(self._bypass_proxy_check)

        self._use_custom_proxy_check = QCheckBox("Use different proxy for matching traffic")
        self._use_custom_proxy_check.stateChanged.connect(self._on_proxy_changed)
        proxy_layout.addWidget(self._use_custom_proxy_check)

        self._proxy_widget = QWidget()
        proxy_form = QHBoxLayout(self._proxy_widget)
        proxy_form.setContentsMargins(20, 8, 0, 0)

        self._proxy_server_edit = QLineEdit()
        self._proxy_server_edit.setPlaceholderText("proxy.example.com")
        proxy_form.addWidget(QLabel("Server:"))
        proxy_form.addWidget(self._proxy_server_edit, 2)

        self._proxy_port_spin = QSpinBox()
        self._proxy_port_spin.setRange(1, 65535)
        self._proxy_port_spin.setValue(8080)
        proxy_form.addWidget(QLabel("Port:"))
        proxy_form.addWidget(self._proxy_port_spin, 1)

        proxy_layout.addWidget(self._proxy_widget)

        layout.addWidget(proxy_group)

        # DNS override section
        dns_group = QGroupBox("DNS Override (Optional)")
        dns_layout = QVBoxLayout(dns_group)

        self._use_dns_check = QCheckBox("Use custom DNS for resolving this domain")
        self._use_dns_check.stateChanged.connect(self._on_dns_changed)
        dns_layout.addWidget(self._use_dns_check)

        self._dns_widget = QWidget()
        dns_form = QFormLayout(self._dns_widget)
        dns_form.setContentsMargins(20, 8, 0, 0)
        self._dns_edit = QLineEdit()
        self._dns_edit.setPlaceholderText("e.g., 8.8.8.8")
        dns_form.addRow("DNS Server:", self._dns_edit)
        dns_layout.addWidget(self._dns_widget)

        layout.addWidget(dns_group)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Rule")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_values(self) -> None:
        """Load rule values into the form."""
        self._name_edit.setText(self.rule.name)
        self._pattern_edit.setText(self.rule.pattern)
        self._enabled_check.setChecked(self.rule.enabled)

        # Set match type
        index = self._match_type_combo.findData(self.rule.match_type)
        if index >= 0:
            self._match_type_combo.setCurrentIndex(index)

        # Gateway
        self._use_gateway_check.setChecked(self.rule.use_custom_gateway)
        self._gateway_edit.setText(self.rule.custom_gateway)

        # Proxy
        self._bypass_proxy_check.setChecked(self.rule.bypass_proxy)
        self._use_custom_proxy_check.setChecked(self.rule.use_custom_proxy)
        self._proxy_server_edit.setText(self.rule.custom_proxy_server)
        self._proxy_port_spin.setValue(self.rule.custom_proxy_port)

        # DNS
        self._use_dns_check.setChecked(self.rule.use_custom_dns)
        self._dns_edit.setText(self.rule.custom_dns)

        # Update visibility
        self._on_gateway_changed()
        self._on_proxy_changed()
        self._on_dns_changed()

    def _on_gateway_changed(self) -> None:
        """Handle gateway checkbox change."""
        self._gateway_widget.setEnabled(self._use_gateway_check.isChecked())

    def _on_proxy_changed(self) -> None:
        """Handle proxy checkbox changes."""
        # Bypass and custom proxy are mutually exclusive
        if self._bypass_proxy_check.isChecked():
            self._use_custom_proxy_check.setChecked(False)
            self._use_custom_proxy_check.setEnabled(False)
        else:
            self._use_custom_proxy_check.setEnabled(True)

        self._proxy_widget.setEnabled(
            self._use_custom_proxy_check.isChecked() and
            not self._bypass_proxy_check.isChecked()
        )

    def _on_dns_changed(self) -> None:
        """Handle DNS checkbox change."""
        self._dns_widget.setEnabled(self._use_dns_check.isChecked())

    def _save(self) -> None:
        """Validate and save the rule."""
        pattern = self._pattern_edit.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Validation Error", "Please enter a pattern.")
            self._pattern_edit.setFocus()
            return

        # Validate gateway if enabled
        if self._use_gateway_check.isChecked():
            gateway = self._gateway_edit.text().strip()
            if not gateway:
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a gateway IP or disable custom gateway."
                )
                return

        # Validate proxy if enabled
        if self._use_custom_proxy_check.isChecked():
            server = self._proxy_server_edit.text().strip()
            if not server:
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a proxy server or disable custom proxy."
                )
                return

        # Validate DNS if enabled
        if self._use_dns_check.isChecked():
            dns = self._dns_edit.text().strip()
            if not dns:
                QMessageBox.warning(
                    self, "Validation Error",
                    "Please enter a DNS server or disable custom DNS."
                )
                return

        # Save values
        self.rule.name = self._name_edit.text().strip()
        self.rule.pattern = pattern
        self.rule.match_type = self._match_type_combo.currentData()
        self.rule.enabled = self._enabled_check.isChecked()
        self.rule.use_custom_gateway = self._use_gateway_check.isChecked()
        self.rule.custom_gateway = self._gateway_edit.text().strip()
        self.rule.bypass_proxy = self._bypass_proxy_check.isChecked()
        self.rule.use_custom_proxy = self._use_custom_proxy_check.isChecked()
        self.rule.custom_proxy_server = self._proxy_server_edit.text().strip()
        self.rule.custom_proxy_port = self._proxy_port_spin.value()
        self.rule.use_custom_dns = self._use_dns_check.isChecked()
        self.rule.custom_dns = self._dns_edit.text().strip()

        self.accept()


class RouteRulesEditorDialog(QDialog):
    """Dialog for managing route rules in a profile."""

    def __init__(self, rules: list[RouteRule], parent=None):
        super().__init__(parent)
        # Deep copy rules
        self.rules = [r.clone() for r in rules]
        for i, orig in enumerate(rules):
            self.rules[i].id = orig.id  # Keep original IDs
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Route Rules")
        self.setMinimumSize(550, 450)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Custom Route Rules")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+ Add Rule")
        add_btn.clicked.connect(self._add_rule)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # Description
        desc = QLabel(
            "Configure how specific domains should be routed. "
            "Rules let you use different gateways or bypass proxy for certain sites."
        )
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Rules list
        self._rules_list = QListWidget()
        self._rules_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background-color: #FAFAFA;
            }
            QListWidget::item {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                margin: 4px;
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                border: 1px solid #2196F3;
            }
        """)
        layout.addWidget(self._rules_list, 1)

        # Empty state
        self._empty_label = QLabel(
            "No route rules configured.\n"
            "Click '+ Add Rule' to create custom routing for specific domains."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 40px;")
        layout.addWidget(self._empty_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Rules")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _refresh_list(self) -> None:
        """Refresh the rules list."""
        self._rules_list.clear()

        self._empty_label.setVisible(len(self.rules) == 0)
        self._rules_list.setVisible(len(self.rules) > 0)

        for rule in self.rules:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, rule.id)

            widget = RouteRuleItem(rule)
            widget.edit_clicked.connect(self._edit_rule)
            widget.delete_clicked.connect(self._delete_rule)

            item.setSizeHint(widget.sizeHint())
            self._rules_list.addItem(item)
            self._rules_list.setItemWidget(item, widget)

    def _add_rule(self) -> None:
        """Add a new route rule."""
        rule = RouteRule()
        dialog = RouteRuleEditorDialog(rule, is_new=True, parent=self)

        if dialog.exec():
            self.rules.append(dialog.rule)
            self._refresh_list()

    def _edit_rule(self, rule_id: str) -> None:
        """Edit an existing route rule."""
        rule = next((r for r in self.rules if r.id == rule_id), None)
        if not rule:
            return

        dialog = RouteRuleEditorDialog(rule, is_new=False, parent=self)

        if dialog.exec():
            # Update the rule in place
            idx = self.rules.index(rule)
            self.rules[idx] = dialog.rule
            self._refresh_list()

    def _delete_rule(self, rule_id: str) -> None:
        """Delete a route rule."""
        rule = next((r for r in self.rules if r.id == rule_id), None)
        if not rule:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this rule?\n\n"
            f"Pattern: {rule.pattern}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.rules.remove(rule)
            self._refresh_list()
