from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication
from logger import logger

# Theme palette variables
DARK_THEME_VARS = {
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
}

LIGHT_THEME_VARS = {
    'bg_main': '#f0f0f0',
    'fg_main': '#000000',
    'border_color': '#d0d0d0',
    'bg_button': '#e0e0e0',
    'bg_button_hover': '#d0d0d0',
    'bg_button_disabled': '#f5f5f5',
    'fg_disabled': '#999999',
    'bg_slider_groove': '#ffffff',
    'bg_combo': '#ffffff',
    'bg_tab_pane': '#ffffff',
    'bg_menubar': '#f0f0f0',
}

# Variable-based stylesheet template
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
    QPushButton:pressed {{ background-color: #2a82da; color: #ffffff; }}
    QPushButton:disabled {{ background-color: {bg_button_disabled}; color: {fg_disabled}; }}
    QLabel {{ color: {fg_main}; background: transparent; }}
    QSlider::groove:horizontal {{
        border: 1px solid {border_color}; height: 8px; background: {bg_slider_groove};
        margin: 2px 0; border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: #2a82da; border: 1px solid {border_color}; width: 18px;
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
        background-color: {bg_combo}; color: {fg_main}; selection-background-color: #2a82da;
        selection-color: #ffffff; border: 1px solid {border_color};
    }}
    QCheckBox {{ color: {fg_main}; spacing: 5px; }}
    QCheckBox::indicator {{ width: 13px; height: 13px; }}
    QCheckBox::indicator:unchecked {{ background-color: {bg_combo}; border: 1px solid {border_color}; }}
    QCheckBox::indicator:checked {{ background-color: #2a82da; border: 1px solid {border_color}; }}
    QTabWidget::pane {{ border: 1px solid {border_color}; background-color: {bg_tab_pane}; }}
    QTabBar::tab {{
        background-color: {bg_button}; border: 1px solid {border_color}; padding: 8px 16px;
        margin-right: 2px; color: {fg_main};
    }}
    QTabBar::tab:selected {{ background-color: #2a82da; color: white; border-bottom: 1px solid #2a82da; }}
    QScrollArea {{ border: none; background-color: {bg_tab_pane}; }}
    QProgressBar {{
        border: 1px solid {border_color}; border-radius: 3px; text-align: center;
        background-color: {bg_slider_groove}; color: {fg_main};
    }}
    QProgressBar::chunk {{ background-color: #2a82da; border-radius: 2px; }}
    QMenuBar {{ background-color: {bg_menubar}; color: {fg_main}; border-bottom: 1px solid {border_color}; }}
    QMenuBar::item {{ background: transparent; padding: 4px 8px; }}
    QMenuBar::item:selected {{ background-color: #2a82da; color: #ffffff; }}
    QMenu {{ background-color: {bg_combo}; color: {fg_main}; border: 1px solid {border_color}; }}
    QMenu::item {{ padding: 8px 32px 8px 16px; }}
    QMenu::item:selected {{ background-color: #2a82da; color: #ffffff; }}
    QStatusBar {{ background-color: {bg_menubar}; color: {fg_main}; border-top: 1px solid {border_color}; }}
"""

def get_theme_stylesheet(is_dark: bool) -> str:
    """Return the formatted stylesheet based on theme selection."""
    theme_vars = DARK_THEME_VARS if is_dark else LIGHT_THEME_VARS
    return STYLESHEET_TEMPLATE.format(**theme_vars)

def apply_theme(window, is_dark: bool):
    """Apply the chosen dark/light theme to the window and the global application palette."""
    app = QApplication.instance()
    if app is None:
        logger.warning("QApplication instance not found, cannot apply palette.")
        return
        
    logger.info(f"Applying {'Dark' if is_dark else 'Light'} theme.")
    
    if is_dark:
        dark_palette = QPalette()
        colors = {
            QPalette.ColorRole.Window: QColor(53, 53, 53),
            QPalette.ColorRole.WindowText: QColor(255, 255, 255),
            QPalette.ColorRole.Base: QColor(25, 25, 25),
            QPalette.ColorRole.AlternateBase: QColor(53, 53, 53),
            QPalette.ColorRole.Text: QColor(255, 255, 255),
            QPalette.ColorRole.BrightText: QColor(255, 0, 0),
            QPalette.ColorRole.Button: QColor(53, 53, 53),
            QPalette.ColorRole.ButtonText: QColor(255, 255, 255),
            QPalette.ColorRole.Highlight: QColor(42, 130, 218),
            QPalette.ColorRole.HighlightedText: QColor(0, 0, 0),
            QPalette.ColorRole.ToolTipBase: QColor(0, 0, 0),
            QPalette.ColorRole.ToolTipText: QColor(255, 255, 255),
        }
        
        # Apply colors to all color groups
        for group in [QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled]:
            for role, color in colors.items():
                dark_palette.setColor(group, role, color)
        
        # Override disabled colors
        disabled_colors = {
            QPalette.ColorRole.WindowText: QColor(127, 127, 127),
            QPalette.ColorRole.Text: QColor(127, 127, 127),
            QPalette.ColorRole.ButtonText: QColor(127, 127, 127),
        }
        
        for role, color in disabled_colors.items():
            dark_palette.setColor(QPalette.ColorGroup.Disabled, role, color)
        
        app.setPalette(dark_palette)
        window.setPalette(dark_palette)
    else:
        app.setPalette(app.style().standardPalette())
        window.setPalette(app.style().standardPalette())
        
    stylesheet = get_theme_stylesheet(is_dark)
    window.setStyleSheet(stylesheet)
    window.update()
