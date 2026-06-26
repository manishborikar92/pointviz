from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication
from logger import logger

# ─── Dark Theme ───────────────────────────────────────────────────────────────
DARK_THEME = {
    'bg_main': '#353535',
    'fg_main': '#ffffff',
    'border_color': '#5a5a5a',
    'bg_button': '#454545',
    'bg_button_hover': '#565656',
    'bg_button_disabled': '#2a2a2a',
    'fg_disabled': '#7f7f7f',
    'bg_slider_groove': '#353535',
    'bg_combo': '#454545',
    'bg_tab_pane': '#353535',
    'bg_menubar': '#353535',
    'accent': '#2a82da',
}

# ─── Light Theme ──────────────────────────────────────────────────────────────
LIGHT_THEME = {
    'bg_main': '#FFFFFF',
    'fg_main': '#0F172A',
    'border_color': '#E2E8F0',
    'bg_button': '#F8FAFC',
    'bg_button_hover': '#E2E8F0',
    'bg_button_disabled': '#F1F5F6',
    'fg_disabled': '#94A3B8',
    'bg_slider_groove': '#F1F5F9',
    'bg_combo': '#FFFFFF',
    'bg_tab_pane': '#FFFFFF',
    'bg_menubar': '#F8FAFC',
    'accent': '#2563EB',
}

# ─── Stylesheet template (uses {accent} — no hardcoded colour values) ─────────
STYLESHEET_TEMPLATE = """
    QMainWindow {{ background-color: {bg_main}; color: {fg_main}; }}
    QWidget {{ background-color: {bg_main}; color: {fg_main}; }}
    QGroupBox {{
        font-weight: bold; border: 2px solid {border_color}; border-radius: 5px;
        margin-top: 1ex; padding-top: 5px; background-color: {bg_main}; color: {fg_main};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; color: {fg_main};
    }}
    QPushButton {{
        background-color: {bg_button}; border: 1px solid {border_color}; border-radius: 3px;
        padding: 5px; color: {fg_main};
    }}
    QPushButton:hover {{ background-color: {bg_button_hover}; }}
    QPushButton:pressed {{ background-color: {accent}; color: #ffffff; }}
    QPushButton:disabled {{ background-color: {bg_button_disabled}; color: {fg_disabled}; }}
    QLabel {{ color: {fg_main}; background: transparent; }}
    QSlider::groove:horizontal {{
        border: 1px solid {border_color}; height: 8px; background: {bg_slider_groove};
        margin: 2px 0; border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {accent}; border: 1px solid {border_color}; width: 18px;
        margin: -2px 0; border-radius: 3px;
    }}
    QComboBox {{
        background-color: {bg_combo}; border: 1px solid {border_color}; border-radius: 3px;
        padding: 5px; color: {fg_main};
    }}
    QComboBox::drop-down {{ border-left: 1px solid {border_color}; width: 15px; background-color: {bg_button}; }}
    QComboBox::down-arrow {{
        image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
        border-top: 5px solid {fg_main}; margin-left: 2px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {bg_combo}; color: {fg_main}; selection-background-color: {accent};
        selection-color: #ffffff; border: 1px solid {border_color};
    }}
    QCheckBox {{ color: {fg_main}; spacing: 5px; }}
    QCheckBox::indicator {{ width: 13px; height: 13px; }}
    QCheckBox::indicator:unchecked {{ background-color: {bg_combo}; border: 1px solid {border_color}; }}
    QCheckBox::indicator:checked {{ background-color: {accent}; border: 1px solid {border_color}; }}
    QTabWidget::pane {{ border: 1px solid {border_color}; background-color: {bg_tab_pane}; }}
    QTabWidget::tab-bar {{ left: 0px; right: 0px; }}
    QTabBar {{ qproperty-drawBase: 0; }}
    QTabBar::tab {{
        background-color: {bg_button}; border: 1px solid {border_color}; padding: 8px 16px;
        margin-right: 2px; color: {fg_main};
    }}
    QTabBar::tab:selected {{ background-color: {accent}; color: white; border-bottom: 1px solid {accent}; }}
    QTabBar::scroller {{
        width: 0px;
        height: 0px;
    }}
    QTabBar QToolButton {{
        width: 0px;
        height: 0px;
        border: none;
        background: transparent;
    }}
    QScrollArea {{ border: none; background-color: {bg_tab_pane}; }}
    QTextBrowser {{
        border: none;
        background-color: transparent;
        padding: 10px;
    }}
    QTextBrowser table {{
        border-collapse: collapse;
        width: 100%;
        margin-top: 10px;
        margin-bottom: 10px;
    }}
    QTextBrowser th {{
        background-color: {bg_button};
        padding: 8px;
        border: 1px solid {border_color};
        font-weight: bold;
        text-align: left;
    }}
    QTextBrowser td {{
        padding: 8px;
        border: 1px solid {border_color};
    }}
    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {border_color};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {accent};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
        height: 0px;
        width: 0px;
    }}
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
        border: none;
        background: none;
        image: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        border: none;
        background: transparent;
        height: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {border_color};
        min-width: 20px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {accent};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        border: none;
        background: none;
        width: 0px;
        height: 0px;
    }}
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
        border: none;
        background: none;
        image: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    QProgressBar {{
        border: 1px solid {border_color}; border-radius: 3px; text-align: center;
        background-color: {bg_slider_groove}; color: {fg_main};
    }}
    QProgressBar::chunk {{ background-color: {accent}; border-radius: 2px; }}
    QMenuBar {{ background-color: {bg_menubar}; color: {fg_main}; border-bottom: 1px solid {border_color}; }}
    QMenuBar::item {{ background: transparent; padding: 4px 8px; }}
    QMenuBar::item:selected {{ background-color: {accent}; color: #ffffff; }}
    QMenu {{ background-color: {bg_combo}; color: {fg_main}; border: 1px solid {border_color}; }}
    QMenu::item {{ padding: 8px 32px 8px 16px; }}
    QMenu::item:selected {{ background-color: {accent}; color: #ffffff; }}
    QStatusBar {{ background-color: {bg_menubar}; color: {fg_main}; border-top: 1px solid {border_color}; }}

    QLabel#clipping_info_label {{
        color: {fg_main};
        background-color: {bg_button};
        border: 1px solid {border_color};
        border-radius: 4px;
        padding: 6px;
        font-style: italic;
    }}
"""


def get_theme_stylesheet(is_dark: bool) -> str:
    """Return the formatted stylesheet based on theme selection."""
    theme_vars = DARK_THEME if is_dark else LIGHT_THEME
    return STYLESHEET_TEMPLATE.format(**theme_vars)


def apply_theme(window, is_dark: bool):
    """Apply the chosen theme to the window and the global application palette."""
    app = QApplication.instance()
    if app is None:
        logger.warning("QApplication instance not found, cannot apply palette.")
        return

    logger.info(f"Applying {'Dark' if is_dark else 'Light'} theme.")
    theme_vars = DARK_THEME if is_dark else LIGHT_THEME

    palette = QPalette()
    colors = {
        QPalette.ColorRole.Window: QColor(theme_vars['bg_main']),
        QPalette.ColorRole.WindowText: QColor(theme_vars['fg_main']),
        QPalette.ColorRole.Base: QColor(theme_vars['bg_slider_groove']),
        QPalette.ColorRole.AlternateBase: QColor(theme_vars['bg_main']),
        QPalette.ColorRole.Text: QColor(theme_vars['fg_main']),
        QPalette.ColorRole.BrightText: QColor(255, 0, 0),
        QPalette.ColorRole.Button: QColor(theme_vars['bg_button']),
        QPalette.ColorRole.ButtonText: QColor(theme_vars['fg_main']),
        QPalette.ColorRole.Highlight: QColor(theme_vars['accent']),
        QPalette.ColorRole.HighlightedText: QColor(255, 255, 255),
        QPalette.ColorRole.ToolTipBase: QColor(theme_vars['bg_main']),
        QPalette.ColorRole.ToolTipText: QColor(theme_vars['fg_main']),
    }

    for group in [QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled]:
        for role, color in colors.items():
            palette.setColor(group, role, color)

    disabled_colors = {
        QPalette.ColorRole.WindowText: QColor(theme_vars['fg_disabled']),
        QPalette.ColorRole.Text: QColor(theme_vars['fg_disabled']),
        QPalette.ColorRole.ButtonText: QColor(theme_vars['fg_disabled']),
    }
    for role, color in disabled_colors.items():
        palette.setColor(QPalette.ColorGroup.Disabled, role, color)

    app.setPalette(palette)
    window.setPalette(palette)

    stylesheet = get_theme_stylesheet(is_dark)
    window.setStyleSheet(stylesheet)
    window.update()
