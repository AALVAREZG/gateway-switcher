"""Application styles and themes."""

# Color palette (Material Design inspired)
COLORS = {
    "primary": "#2196F3",
    "primary_dark": "#1976D2",
    "primary_light": "#BBDEFB",
    "accent": "#FF9800",
    "text_primary": "#212121",
    "text_secondary": "#757575",
    "divider": "#BDBDBD",
    "background": "#FAFAFA",
    "surface": "#FFFFFF",
    "success": "#4CAF50",
    "error": "#F44336",
}

# Global stylesheet
STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLORS["background"]};
}}

QLabel {{
    color: {COLORS["text_primary"]};
}}

QLabel[class="title"] {{
    font-size: 24px;
    font-weight: bold;
    color: {COLORS["text_primary"]};
}}

QLabel[class="subtitle"] {{
    font-size: 14px;
    color: {COLORS["text_secondary"]};
}}

QLabel[class="section-title"] {{
    font-size: 16px;
    font-weight: 600;
    color: {COLORS["text_primary"]};
}}

QPushButton {{
    background-color: {COLORS["primary"]};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 500;
    min-height: 36px;
}}

QPushButton:hover {{
    background-color: {COLORS["primary_dark"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["divider"]};
    color: {COLORS["text_secondary"]};
}}

QPushButton[class="secondary"] {{
    background-color: transparent;
    color: {COLORS["primary"]};
    border: 1px solid {COLORS["primary"]};
}}

QPushButton[class="secondary"]:hover {{
    background-color: {COLORS["primary_light"]};
}}

QPushButton[class="danger"] {{
    background-color: {COLORS["error"]};
}}

QPushButton[class="danger"]:hover {{
    background-color: #D32F2F;
}}

QLineEdit, QSpinBox {{
    border: 1px solid {COLORS["divider"]};
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 14px;
    background-color: {COLORS["surface"]};
}}

QLineEdit:focus, QSpinBox:focus {{
    border: 2px solid {COLORS["primary"]};
    padding: 7px 11px;
}}

QComboBox {{
    border: 1px solid {COLORS["divider"]};
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 14px;
    background-color: {COLORS["surface"]};
    min-height: 20px;
}}

QComboBox:focus {{
    border: 2px solid {COLORS["primary"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}

QCheckBox {{
    font-size: 14px;
    color: {COLORS["text_primary"]};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
}}

QListWidget {{
    border: none;
    background-color: transparent;
    outline: none;
}}

QListWidget::item {{
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 8px;
    margin: 4px 2px;
}}

QListWidget::item:selected {{
    background-color: #E3F2FD;
    border: 2px solid {COLORS["primary"]};
}}

QListWidget::item:hover:!selected {{
    background-color: #F5F5F5;
    border: 1px solid #BDBDBD;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QGroupBox {{
    background-color: {COLORS["surface"]};
    border-radius: 8px;
    padding: 16px;
    margin-top: 8px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: {COLORS["text_primary"]};
}}

QProgressBar {{
    border: none;
    border-radius: 2px;
    background-color: {COLORS["primary_light"]};
    height: 4px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS["primary"]};
    border-radius: 2px;
}}

QMenu {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["divider"]};
    border-radius: 4px;
    padding: 4px 0px;
}}

QMenu::item {{
    padding: 8px 32px 8px 16px;
}}

QMenu::item:selected {{
    background-color: {COLORS["primary_light"]};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS["divider"]};
    margin: 4px 0px;
}}
"""


def get_card_style() -> str:
    """Get style for card-like containers."""
    return f"""
        background-color: {COLORS["surface"]};
        border-radius: 8px;
        padding: 16px;
    """
