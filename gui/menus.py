from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QMenuBar

def setup_menus(window):
    """Setup all application menus on the QMainWindow."""
    menubar = window.menuBar()
    
    # File menu
    file_menu = menubar.addMenu('File')
    _add_file_menu_actions(window, file_menu)
    
    # View menu
    view_menu = menubar.addMenu('View')
    _add_view_menu_actions(window, view_menu)
    
    # Tools menu
    tools_menu = menubar.addMenu('Tools')
    _add_tools_menu_actions(window, tools_menu)
    
    # Help menu
    help_menu = menubar.addMenu('Help')
    _add_help_menu_actions(window, help_menu)

def _add_file_menu_actions(window, file_menu):
    """Add actions to file menu."""
    # Open action
    open_action = QAction("Open Point Cloud File", window)
    open_action.setShortcut("Ctrl+O")
    open_action.triggered.connect(window.load_file)
    file_menu.addAction(open_action)
    
    # Open Recent submenu
    window.recent_menu = QMenu("Open Recent", file_menu)
    file_menu.addMenu(window.recent_menu)
    window.recent_menu.aboutToShow.connect(window.update_recent_files_menu)
    
    file_menu.addSeparator()
    
    # Other file actions
    actions = [
        ("Export Point Cloud...", "Ctrl+E", window.export_file),
        None,  # Separator
        ("Take Screenshot...", "Ctrl+S", window.take_screenshot),
        None,  # Separator
        ("Exit", "Ctrl+Q", window.close)
    ]
    _add_menu_actions(window, file_menu, actions)

def _add_view_menu_actions(window, view_menu):
    """Add actions to view menu."""
    actions = [
        ("Reset Camera", "0", window.reset_view),
        None,  # Separator
        ("Top View", "1", window._set_top_view),
        ("Front View", "2", window._set_front_view),
        ("Side View", "3", window._set_side_view),
        ("Isometric View", "4", window._set_iso_view),
        None,  # Separator
        ("Fullscreen", "F11", window.toggle_fullscreen),
        ("Toggle Theme", "Ctrl+T", window.toggle_theme)
    ]
    _add_menu_actions(window, view_menu, actions)

def _add_help_menu_actions(window, help_menu):
    """Add actions to help menu."""
    actions = [
        ("About", None, window.show_about)
    ]
    _add_menu_actions(window, help_menu, actions)

def _add_tools_menu_actions(window, tools_menu):
    """Add actions to tools menu (Clipping & Measurement)."""
    actions = [
        ("Toggle Clipping Box", "Ctrl+B", window._on_toggle_clipping_shortcut),
        ("Reset Clipping", None, window._on_reset_clipping),
        None,  # Separator
        ("Measure Distance", "Ctrl+M", window._on_toggle_measure_shortcut),
        ("Clear Measurements", None, window._on_clear_measurements),
    ]
    _add_menu_actions(window, tools_menu, actions)

def _add_menu_actions(window, menu, actions):
    """Helper to add actions to a menu."""
    for action_data in actions:
        if action_data is None:
            menu.addSeparator()
        else:
            action = QAction(action_data[0], window)
            if action_data[1]:  # Has shortcut
                action.setShortcut(action_data[1])
            action.triggered.connect(action_data[2])
            menu.addAction(action)
