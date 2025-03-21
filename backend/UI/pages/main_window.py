"""
Main Window module with permanent header and menu bar.
This serves as the main application window that loads pages in its central area.
"""
import os
import sys
import json
from typing import Dict, List, Optional, Type, Any
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QVBoxLayout, QHBoxLayout, QWidget, QStatusBar, QLabel, QPushButton,
    QComboBox, QDialog, QFrame, QMessageBox, QGraphicsDropShadowEffect, QCheckBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QColor, QCursor, QGuiApplication, QIcon
from backend.UI.translations.translator import AutoTranslator

class ThemeManager:
    """
    Manages application themes.
    Provides theme definitions and switching functionality.
    """

    # Theme definitions
    LIGHT = "light"
    DARK = "dark"
    BLUE = "blue"

    # Theme colors
    THEMES = {
        LIGHT: {
            "name": "Light",
            "background": "#FFFFFF",
            "surface": "#F5F5F5",
            "primary": "#2196F3",
            "primary_dark": "#1976D2",
            "primary_light": "#BBDEFB",
            "accent": "#FF4081",
            "text_primary": "#212121",
            "text_secondary": "#757575",
            "divider": "#BDBDBD",
            "error": "#F44336",
            "warning": "#FF9800",
            "success": "#4CAF50",
            "info": "#2196F3",
            "card_background": "#FFFFFF",
            "card_border": "#E0E0E0"
        },
        DARK: {
            "name": "Dark",
            "background": "#121212",
            "surface": "#1E1E1E",
            "primary": "#2196F3",
            "primary_dark": "#1976D2",
            "primary_light": "#0D47A1",
            "accent": "#FF4081",
            "text_primary": "#FFFFFF",
            "text_secondary": "#B0B0B0",
            "divider": "#424242",
            "error": "#F44336",
            "warning": "#FF9800",
            "success": "#4CAF50",
            "info": "#2196F3",
            "card_background": "#1E1E1E",
            "card_border": "#333333"
        },
        BLUE: {
            "name": "Blue",
            "background": "#0A1929",
            "surface": "#132F4C",
            "primary": "#3399FF",
            "primary_dark": "#006BE6",
            "primary_light": "#66B2FF",
            "accent": "#FF4081",
            "text_primary": "#FFFFFF",
            "text_secondary": "#B2BAC2",
            "divider": "#1E4976",
            "error": "#EB0014",
            "warning": "#FFAB00",
            "success": "#1DB45A",
            "info": "#29B6F6",
            "card_background": "#132F4C",
            "card_border": "#1E4976"
        }
    }

    def __init__(self):
        """Initialize the theme manager with the default theme."""
        self.current_theme = self.LIGHT

    def get_theme(self, theme_name: Optional[str] = None) -> Dict[str, str]:
        """
        Get a theme by name or the current theme if no name is provided.

        Args:
            theme_name: Name of the theme to get, or None for current theme

        Returns:
            Dict[str, str]: Theme colors dictionary
        """
        if theme_name is None:
            theme_name = self.current_theme

        return self.THEMES.get(theme_name, self.THEMES[self.LIGHT])

    def set_theme(self, theme_name: str) -> bool:
        """
        Set the current theme.

        Args:
            theme_name: Name of the theme to set

        Returns:
            bool: True if theme was changed, False otherwise
        """
        if theme_name in self.THEMES and theme_name != self.current_theme:
            self.current_theme = theme_name
            return True
        return False

    def get_available_themes(self) -> Dict[str, str]:
        """
        Get available themes.

        Returns:
            Dict[str, str]: Dictionary of theme ids to display names
        """
        return {key: theme["name"] for key, theme in self.THEMES.items()}

    def get_stylesheet(self, theme_name: Optional[str] = None) -> str:
        """
        Get the stylesheet for a theme.

        Args:
            theme_name: Name of the theme, or None for current theme

        Returns:
            str: CSS stylesheet for the theme
        """
        theme = self.get_theme(theme_name)

        return f"""
            /* Main application styles */
            QMainWindow {{
                background-color: transparent;
                color: {theme["text_primary"]};
            }}

            /* Central widget - this is where we want the border and rounded corners */
            .QWidget {{
                background-color: {theme["background"]};
                color: {theme["text_primary"]};
                border: 1px solid {theme["divider"]};
                border-radius: 8px;
            }}

            /* Dialog styles */
            QDialog {{
                background-color: {theme["background"]};
                color: {theme["text_primary"]};
                border: 1px solid {theme["divider"]};
                border-radius: 6px;
            }}

            /* General widget styles */
            QWidget {{
                background-color: {theme["background"]};
                color: {theme["text_primary"]};
            }}

            /* Frame styles */
            QFrame {{
                background-color: {theme["surface"]};
                color: {theme["text_primary"]};
                border-radius: 6px;
            }}

            /* Special frames */
            QFrame#header-widget {{
                border-radius: 8px;
                background-color: {theme["surface"]};
                border-bottom: 1px solid {theme["divider"]};
            }}

            QFrame#welcome-frame, QFrame#stats-widget, QFrame#activity-widget, QFrame#settings-frame {{
                border: 1px solid {theme["divider"]};
            }}

            /* Menu styles */
            QMenu {{
                background-color: {theme["surface"]};
                color: {theme["text_primary"]};
                border: 1px solid {theme["divider"]};
                border-radius: 4px;
            }}

            QMenu::item {{
                padding: 6px 20px 6px 20px;
            }}

            QMenu::item:selected {{
                background-color: {theme["primary"]};
                color: white;
            }}

            /* ToolBar styles */
            QToolBar {{
                background-color: {theme["surface"]};
                color: {theme["text_primary"]};
                border-bottom: 1px solid {theme["divider"]};
                spacing: 5px;
            }}

            QToolBar::separator {{
                background-color: {theme["divider"]};
                width: 1px;
                margin: 0 10px;
            }}

            /* Button styles */
            QPushButton {{
                background-color: {theme["primary"]};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}

            QPushButton:hover {{
                background-color: {theme["primary_dark"]};
            }}

            QPushButton:pressed {{
                background-color: {theme["primary_light"]};
            }}

            QPushButton:disabled {{
                background-color: {theme["divider"]};
                color: {theme["text_secondary"]};
            }}

            /* Header button styles */
            QPushButton[class="header-button"] {{
                background-color: transparent;
                color: {theme["text_primary"]};
                border: 1px solid {theme["divider"]};
                padding: 4px 10px;
                border-radius: 4px;
            }}

            QPushButton[class="header-button"]:hover {{
                background-color: {theme["primary"]};
                color: white;
                border: 1px solid {theme["primary"]};
            }}

            /* Window control button styles - using SVG icons without circular backgrounds */
            QPushButton[class="window-control-button-close"] {{
                background-color: transparent;
                border: none;
                padding: 0;
            }}

            QPushButton[class="window-control-button-minimize"] {{
                background-color: transparent;
                border: none;
                padding: 0;
            }}

            QPushButton[class="window-control-button-maximize"] {{
                background-color: transparent;
                border: none;
                padding: 0;
            }}

            /* Label styles */
            QLabel {{
                color: {theme["text_primary"]};
                background-color: transparent;
            }}

            /* ComboBox styles */
            QComboBox {{
                background-color: {theme["surface"]};
                color: {theme["text_primary"]};
                border: 1px solid {theme["divider"]};
                border-radius: 4px;
                padding: 4px 8px;
            }}

            QComboBox:hover {{
                border: 1px solid {theme["primary"]};
            }}

            QComboBox QAbstractItemView {{
                background-color: {theme["surface"]};
                color: {theme["text_primary"]};
                selection-background-color: {theme["primary"]};
                selection-color: white;
                border: 1px solid {theme["divider"]};
                border-radius: 4px;
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid {theme["divider"]};
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }}

            /* Header ComboBox styles */
            QComboBox[class="header-combo"] {{
                background-color: {theme["surface"]};
                border: 1px solid {theme["divider"]};
                min-width: 120px;
                border-radius: 4px;
            }}

            QComboBox[class="header-combo"]:hover {{
                border: 1px solid {theme["primary"]};
            }}

            /* TabWidget styles */
            QTabWidget::pane {{
                border: 1px solid {theme["divider"]};
                background-color: {theme["surface"]};
                border-radius: 4px;
            }}

            QTabBar::tab {{
                background-color: {theme["background"]};
                color: {theme["text_primary"]};
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid {theme["divider"]};
                border-bottom: none;
                margin-right: 2px;
            }}

            QTabBar::tab:selected {{
                background-color: {theme["primary"]};
                color: white;
            }}

            QTabBar::tab:!selected:hover {{
                background-color: {theme["surface"]};
            }}

            /* ScrollBar styles */
            QScrollBar:vertical {{
                background-color: {theme["background"]};
                width: 14px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {theme["divider"]};
                min-height: 30px;
                border-radius: 7px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {theme["primary"]};
            }}

            QScrollBar:horizontal {{
                background-color: {theme["background"]};
                height: 14px;
                margin: 0px;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {theme["divider"]};
                min-width: 30px;
                border-radius: 7px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {theme["primary"]};
            }}

            QScrollBar::add-line, QScrollBar::sub-line {{
                width: 0px;
                height: 0px;
            }}

            /* Main content styles */
            QFrame#main-content {{
                background-color: {theme["background"]};
                border-radius: 8px;
                padding: 4px;
            }}

            #page-stack {{
                background-color: {theme["background"]};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}

            /* Checkbox styles */
            QCheckBox {{
                color: {theme["text_primary"]};
                spacing: 5px;
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {theme["divider"]};
                border-radius: 2px;
            }}

            QCheckBox::indicator:checked {{
                background-color: {theme["primary"]};
                border: 1px solid {theme["primary"]};
            }}

            QCheckBox::indicator:unchecked:hover {{
                border: 1px solid {theme["primary"]};
            }}

            /* SpinBox styles */
            QSpinBox, QDoubleSpinBox {{
                background-color: {theme["surface"]};
                color: {theme["text_primary"]};
                border: 1px solid {theme["divider"]};
                border-radius: 4px;
                padding: 4px;
            }}

            QSpinBox:hover, QDoubleSpinBox:hover {{
                border: 1px solid {theme["primary"]};
            }}

            /* Form layout styles */
            QFormLayout {{
                background-color: transparent;
            }}

            /* GroupBox styles */
            QGroupBox {{
                background-color: {theme["surface"]};
                border: 1px solid {theme["divider"]};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                color: {theme["text_primary"]};
            }}

            /* Sidebar styling */
            QFrame#sidebar {{
                background-color: {theme["surface"]};
                border-radius: 8px;
                border-right: 1px solid {theme["divider"]};
            }}
        """

class BasePage(QWidget):
    """
    Base class for all pages in the application.
    Provides common functionality and properties.
    """

    # Signal to request navigation to another page
    navigate_to = Signal(str, object)

    # Signal to request language change
    change_language = Signal(str)

    def __init__(self, main_window: 'MainWindow', parent=None):
        """
        Initialize the base page.

        Args:
            main_window: The main window that contains this page
            parent: Parent widget
        """
        super().__init__(parent)
        self.main_window = main_window
        self.page_id = self.__class__.__name__

        # Dictionary to track functions to call for updating theme-dependent widgets
        # Format: {function_name: (function, args, kwargs)}
        self.theme_updaters = {}

        # Set up layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Connect language change signal to main window
        self.change_language.connect(self.main_window.set_language)

        # Default setup
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface. Override in subclasses."""
        pass

    def on_enter(self):
        """
        Called when the page is shown.

        Args:
            data: Optional data passed from the previous page
        """
        # Apply current theme
        self.apply_theme()
        pass

    def on_exit(self):
        """Called when the page is about to be hidden."""
        pass

    def tr(self, text: str) -> str:
        """
        Translate text using the main window's translator.

        Args:
            text: Text to translate

        Returns:
            str: Translated text
        """
        return self.main_window.translate(text)

    def label(self, text, **kwargs):
        """
        Create a translated label.

        Args:
            text: The text for the label
            **kwargs: Additional arguments for QLabel

        Returns:
            QLabel: A translated label
        """
        return QLabel(self.tr(text), **kwargs)

    def button(self, text, on_click=None, **kwargs):
        """
        Create a translated button.

        Args:
            text: The text for the button
            on_click: Optional click handler function
            **kwargs: Additional arguments for QPushButton

        Returns:
            QPushButton: A translated button
        """
        button = QPushButton(self.tr(text), **kwargs)
        if on_click:
            button.clicked.connect(on_click)
        return button

    def checkbox(self, text, checked=False, **kwargs):
        """
        Create a translated checkbox.

        Args:
            text: The text for the checkbox
            checked: Whether the checkbox is checked
            **kwargs: Additional arguments for QCheckBox

        Returns:
            QCheckBox: A translated checkbox
        """
        checkbox = QCheckBox(self.tr(text), **kwargs)
        checkbox.setChecked(checked)
        return checkbox

    def combobox(self, items=None, on_change=None, **kwargs):
        """
        Create a combobox with translated items.

        Args:
            items: List of items to add
            on_change: Optional change handler function
            **kwargs: Additional arguments for QComboBox

        Returns:
            QComboBox: A combobox with translated items
        """
        combo = QComboBox(**kwargs)

        if items:
            for item in items:
                if isinstance(item, tuple):
                    text, data = item
                    combo.addItem(self.tr(text), data)
                else:
                    combo.addItem(self.tr(item))

        # Connect change signal if provided
        if on_change:
            combo.currentIndexChanged.connect(on_change)

        return combo

    def register_theme_updater(self, name, updater_func, *args, **kwargs):
        """
        Register a function to call when the theme changes.

        Args:
            name: A unique name for this updater
            updater_func: The function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        self.theme_updaters[name] = (updater_func, args, kwargs)

    def apply_theme(self):
        """
        Apply the current theme to all custom widgets.
        This base implementation handles registered theme updaters.
        Override in subclasses for custom behavior.
        """
        # Get current theme
        theme = self.main_window.theme_manager.get_theme()

        # Make a copy of the dict to safely handle removal during iteration
        updaters_to_call = list(self.theme_updaters.items())

        # Call all registered theme updater functions
        for name, (func, args, kwargs) in updaters_to_call:
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Error in theme updater {name}: {e}")
                # Consider removing failed updaters
                if name in self.theme_updaters:
                    del self.theme_updaters[name]

        # Apply theme to child widgets if needed
        # (This is where specific widget styling could happen)

    def open_dialog(self, dialog_class: Type[QDialog], data=None, **kwargs) -> Any:
        """
        Open a dialog and return its result.

        Args:
            dialog_class: Dialog class to instantiate
            data: Optional data to pass to the dialog
            **kwargs: Additional keyword arguments for the dialog

        Returns:
            Any: Result from the dialog
        """
        dialog = dialog_class(self.main_window, self, **kwargs)
        if data is not None and hasattr(dialog, 'set_data'):
            dialog.set_data(data)
        return dialog.exec()

    def show_secondary_window(self, window_class: Type[QMainWindow], data=None, **kwargs) -> QMainWindow:
        """
        Open a secondary window.

        Args:
            window_class: Window class to instantiate
            data: Optional data to pass to the window
            **kwargs: Additional keyword arguments for the window

        Returns:
            QMainWindow: The created window instance
        """
        window = window_class(self.main_window, **kwargs)
        if data is not None and hasattr(window, 'set_data'):
            window.set_data(data)
        window.show()
        return window

    def styled_frame(self, style_class=None, **kwargs):
        """
        Create a QFrame with theme-aware styles.

        Args:
            style_class: Optional CSS class name
            **kwargs: Additional arguments for QFrame

        Returns:
            QFrame: A theme-aware frame
        """
        frame = QFrame(**kwargs)

        if style_class:
            frame.setProperty("class", style_class)

        # Register a theme updater if needed
        self.register_theme_updater(
            f"frame_{id(frame)}",
            self._update_frame_style,
            frame, style_class
        )

        # Apply initial style
        self._update_frame_style(frame, style_class)

        return frame

    def _update_frame_style(self, frame, style_class):
        """Update frame style based on current theme."""
        # Get current theme
        theme = self.main_window.theme_manager.get_theme()

        # Apply specific styling based on style_class if needed
        if style_class == "card":
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {theme["card_background"]};
                    border: 1px solid {theme["card_border"]};
                    border-radius: 6px;
                }}
            """)
            frame.setGraphicsEffect(None)

        elif style_class == "panel":
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {theme["surface"]};
                    border: 1px solid {theme["divider"]};
                    border-radius: 6px;
                }}
            """)
            frame.setGraphicsEffect(None)

        elif style_class == "no-border":
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border: none;
                    border-radius: 0px;
                }}
            """)
            frame.setGraphicsEffect(None)

    def header_label(self, text, level=1, **kwargs):
        """
        Create a header label with theme-aware styling.

        Args:
            text: The header text
            level: Header level (1=largest, 3=smallest)
            **kwargs: Additional arguments for QLabel

        Returns:
            QLabel: A styled header label
        """
        label = self.label(text, **kwargs)

        # Register a theme updater
        self.register_theme_updater(
            f"header_{id(label)}",
            self._update_header_style,
            label, level
        )

        # Apply initial style
        self._update_header_style(label, level)

        return label

    def _update_header_style(self, label, level):
        """Update header label style based on level and theme."""
        # Get current theme
        theme = self.main_window.theme_manager.get_theme()

        # Set style based on level
        if level == 1:
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 24px;
                    font-weight: bold;
                    color: {theme["text_primary"]};
                }}
            """)
        elif level == 2:
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 20px;
                    font-weight: bold;
                    color: {theme["text_primary"]};
                }}
            """)
        elif level == 3:
            label.setStyleSheet(f"""
                QLabel {{
                    font-size: 16px;
                    font-weight: bold;
                    color: {theme["text_primary"]};
                }}
            """)

    def card(self, title=None, **kwargs):
        """
        Create a card frame with title for organizing content.

        Args:
            title: Optional card title
            **kwargs: Additional arguments for QFrame

        Returns:
            tuple: (frame, layout) - The card frame and its layout for adding content
        """
        # Create card frame
        card_frame = self.styled_frame(style_class="card", **kwargs)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)

        # Add title if provided
        if title:
            title_label = self.header_label(title, level=3)
            card_layout.addWidget(title_label)

            # Add line separator
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)

            # Register theme updater for separator
            self.register_theme_updater(
                f"separator_{id(separator)}",
                lambda s: s.setStyleSheet(f"background-color: {self.main_window.theme_manager.get_theme()['divider']};"),
                separator
            )

            card_layout.addWidget(separator)

        return card_frame, card_layout

class AboutDialog(QDialog):
    """About dialog showing application information."""

    def __init__(self, main_window, parent=None):
        """Initialize the about dialog."""
        super().__init__(parent)
        self.main_window = main_window

        # Set dialog properties
        self.setWindowTitle(self.main_window.translate("About"))
        self.setMinimumWidth(400)
        self.setModal(True)

        # Set up layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # App title and version
        title_label = QLabel(self.main_window.translate("Application Name"))
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Description
        description = QLabel(self.main_window.translate(
            "This is a modular application with a permanent header, "
            "menu bar, and support for multiple themes and languages."
        ))
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignLeft)
        layout.addWidget(description)

        # Close button
        close_button = QPushButton(self.main_window.translate("Close"))
        close_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)


class MainWindow(QMainWindow):
    """
    Main application window with permanent header and menu bar.
    Handles page navigation, theme and language management.
    """

    # Navigation signal
    navigate_to = Signal(str, object)
    
    # Fichier de configuration
    CONFIG_FILE = "config.json"

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.translator = AutoTranslator()
        self.theme_manager = ThemeManager()
        self.current_language = "en"

        # Charger la configuration si elle existe
        self._load_config()

        # Remove window frame for custom window appearance
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Enable translucent background for rounded corners
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Initialize variables for window dragging
        self.dragging = False
        self.drag_position = None

        # Initialize variables for window resizing
        self.resizing = False
        self.resize_edge = None
        self.resize_start_geometry = None
        self.resize_start_pos = None
        self.border_width = 5  # Width of the resize border area

        # Initialize collections for page management
        self.pages = {}
        self.page_classes = {}
        self.history = []

        # Set window properties
        self.setMinimumSize(800, 600)
        self.setWindowTitle("JobFinder")
        
        # Set window size to 75% of screen resolution
        self._adjust_window_size()

        # Create the main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)  # Légère marge pour la bordure
        self.main_layout.setSpacing(0)

        # Create and set up components
        self._create_header()
        self._create_content_area()
        self._create_footer()

        # Connect navigation signals
        self.navigate_to.connect(self._on_navigate_to)

        # Apply initial theme
        self.apply_theme()

        # Enable mouse tracking to handle resize cursor changes
        self.setMouseTracking(True)
        self.central_widget.setMouseTracking(True)

        # Enable mouse tracking on all child widgets recursively
        self._enable_mouse_tracking_recursive(self)

        # Force resize cursor to appear at window border even over child widgets
        self.installEventFilter(self)

        # The navigate_to.emit call will be in run_app.py after pages are registered

    def _enable_mouse_tracking_recursive(self, widget):
        """Enable mouse tracking on a widget and all its children recursively."""
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)

            # Install event filter on direct children of central widget to propagate mouse events
            if child.parent() == self.central_widget:
                child.installEventFilter(self)

    def eventFilter(self, watched, event):
        """Filter events to ensure resize cursor appears over entire window border."""
        if watched == self and event.type() == event.Type.MouseMove:
            # This will ensure mouseMoveEvent is called to update cursor
            self.mouseMoveEvent(event)
            return False  # Continue event propagation

        # For child widgets, forward mouse move events to the main window
        if event.type() == event.Type.MouseMove and watched != self:
            # Forward mouse event to main window for cursor update
            self.mouseMoveEvent(event)
            return False  # Continue event propagation

        return super().eventFilter(watched, event)

    def _create_header(self):
        """Set up the header widget with logos, combos and info button."""
        self.header_widget = QFrame(self)
        self.header_widget.setObjectName("header-widget")
        self.header_widget.setMouseTracking(True)  # Enable mouse tracking
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(15, 10, 15, 10)

        # App title / logo
        self.title_label = QLabel("JobFinder", self.header_widget)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(self.title_label)

        # Add spacer item
        self.header_layout.addStretch(1)

        # Language selector
        self.language_label = QLabel(self.translate("Language:"), self.header_widget)
        self.header_layout.addWidget(self.language_label)

        self.language_combo = QComboBox(self.header_widget)
        self.language_combo.setProperty("class", "header-combo")
        for lang_code, lang_name in sorted(self.translator.get_available_languages().items()):
            self.language_combo.addItem(lang_name, lang_code)

        index = self.language_combo.findData(self.current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        self.header_layout.addWidget(self.language_combo)

        # Theme selector
        self.theme_label = QLabel(self.translate("Theme:"), self.header_widget)
        self.header_layout.addWidget(self.theme_label)

        self.theme_combo = QComboBox(self.header_widget)
        self.theme_combo.setProperty("class", "header-combo")

        # Add theme items with their display names (not internal keys)
        theme_names = self.theme_manager.get_available_themes()
        for theme_id, theme_name in sorted(theme_names.items()):
            self.theme_combo.addItem(theme_name, theme_id)

        # Set current theme
        current_theme = self.theme_manager.current_theme
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.header_layout.addWidget(self.theme_combo)

        # About button
        self.about_button = QPushButton(self.translate("About"), self.header_widget)
        self.about_button.setProperty("class", "header-button")
        self.about_button.clicked.connect(self._show_about_dialog)
        self.header_layout.addWidget(self.about_button)

        # Add spacing between about button and window controls
        self.header_layout.addSpacing(20)

        # Get the icons directory
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icons")

        # Window control buttons - Windows style order (minimize, maximize, close)
        window_controls_layout = QHBoxLayout()
        window_controls_layout.setSpacing(10)  # Spacing between buttons

        # Minimize button (yellow)
        self.minimize_button = QPushButton(self.header_widget)
        self.minimize_button.setProperty("class", "window-control-button-minimize")
        self.minimize_button.setFixedSize(18, 18)  # Slightly larger size
        self.minimize_button.setIcon(QIcon(os.path.join(icons_dir, "minus.svg")))
        self.minimize_button.setIconSize(self.minimize_button.size())
        self.minimize_button.clicked.connect(self.showMinimized)
        window_controls_layout.addWidget(self.minimize_button)

        # Maximize/restore button (green)
        self.maximize_button = QPushButton(self.header_widget)
        self.maximize_button.setProperty("class", "window-control-button-maximize")
        self.maximize_button.setFixedSize(18, 18)
        self.maximize_button.setIcon(QIcon(os.path.join(icons_dir, "maximize.svg")))
        self.maximize_button.setIconSize(self.maximize_button.size())
        self.maximize_button.clicked.connect(self._toggle_maximize)
        window_controls_layout.addWidget(self.maximize_button)

        # Close button (red)
        self.close_button = QPushButton(self.header_widget)
        self.close_button.setProperty("class", "window-control-button-close")
        self.close_button.setFixedSize(18, 18)
        self.close_button.setIcon(QIcon(os.path.join(icons_dir, "close.svg")))
        self.close_button.setIconSize(self.close_button.size())
        self.close_button.clicked.connect(self.close)
        window_controls_layout.addWidget(self.close_button)

        # Add the window controls to the header layout
        self.header_layout.addLayout(window_controls_layout)

        self.main_layout.addWidget(self.header_widget)

    def _toggle_maximize(self):
        """Toggle between maximized and normal window state."""
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")
        if self.isMaximized():
            self.showNormal()
            # Update button icon when returning to normal
            self.maximize_button.setIcon(QIcon(os.path.join(icons_dir, "maximize.svg")))
        else:
            self.showMaximized()
            # Update button icon when maximized - in this case we keep the same icon
            # as the SVG already represents the maximize state adequately

    def mousePressEvent(self, event):
        """Handle mouse press events for dragging and resizing."""
        if event.button() == Qt.LeftButton:
            # Check if we're on the resize border
            edge = self._get_resize_edge(event.pos())
            if edge:
                self.resizing = True
                self.resize_edge = edge
                self.resize_start_geometry = self.geometry()
                self.resize_start_pos = event.globalPos()
                event.accept()
                return

            # Check if we're on the header for dragging
            if self.header_widget.geometry().contains(event.pos()):
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging, resizing and cursor updates."""
        # Handle resizing - when actively resizing
        if event.buttons() & Qt.LeftButton and self.resizing:
            self._handle_resize(event.globalPos())
            return

        # Handle dragging - when actively dragging
        if event.buttons() & Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            return

        # Reset cursor by default
        cursor_set = False

        # Update cursor for resize edges when mouse is moving
        if not self.isMaximized():
            edge = self._get_resize_edge(event.pos())
            if edge:
                # Set appropriate cursor based on which edge we're hovering over
                if edge in ['top', 'bottom']:
                    self.setCursor(Qt.SizeVerCursor)
                    cursor_set = True
                elif edge in ['left', 'right']:
                    self.setCursor(Qt.SizeHorCursor)
                    cursor_set = True
                elif edge in ['topleft', 'bottomright']:
                    self.setCursor(Qt.SizeFDiagCursor)
                    cursor_set = True
                elif edge in ['topright', 'bottomleft']:
                    self.setCursor(Qt.SizeBDiagCursor)
                    cursor_set = True

        # If we haven't set a special cursor, make sure we reset to arrow
        if not cursor_set:
            self.setCursor(Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events to stop dragging and resizing."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_edge = None
            # Reset cursor when stopping resize
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def _get_resize_edge(self, pos):
        """
        Determine if the position is on a resize edge.

        Args:
            pos: Mouse position in window coordinates

        Returns:
            str: Edge identifier ('top', 'left', etc.) or None if not on edge
        """
        rect = self.rect()
        border = self.border_width

        # Don't detect resize edges when maximized
        if self.isMaximized():
            return None

        # Check for corners first (they have priority)
        if pos.x() <= border and pos.y() <= border:
            return 'topleft'
        if pos.x() >= rect.width() - border and pos.y() <= border:
            return 'topright'
        if pos.x() <= border and pos.y() >= rect.height() - border:
            return 'bottomleft'
        if pos.x() >= rect.width() - border and pos.y() >= rect.height() - border:
            return 'bottomright'

        # Then check for edges
        if pos.x() <= border:
            return 'left'
        if pos.x() >= rect.width() - border:
            return 'right'
        if pos.y() <= border:
            return 'top'
        if pos.y() >= rect.height() - border:
            return 'bottom'

        return None

    def _handle_resize(self, global_pos):
        """
        Resize the window based on mouse movement.

        Args:
            global_pos: Current global mouse position
        """
        delta = global_pos - self.resize_start_pos
        new_geometry = self.resize_start_geometry

        if self.resize_edge == 'left' or self.resize_edge == 'topleft' or self.resize_edge == 'bottomleft':
            # Don't resize below minimum width
            if new_geometry.width() - delta.x() >= self.minimumWidth():
                new_geometry.setLeft(new_geometry.left() + delta.x())

        if self.resize_edge == 'top' or self.resize_edge == 'topleft' or self.resize_edge == 'topright':
            # Don't resize below minimum height
            if new_geometry.height() - delta.y() >= self.minimumHeight():
                new_geometry.setTop(new_geometry.top() + delta.y())

        if self.resize_edge == 'right' or self.resize_edge == 'topright' or self.resize_edge == 'bottomright':
            new_width = new_geometry.width() + delta.x()
            if new_width >= self.minimumWidth():
                new_geometry.setRight(new_geometry.right() + delta.x())

        if self.resize_edge == 'bottom' or self.resize_edge == 'bottomleft' or self.resize_edge == 'bottomright':
            new_height = new_geometry.height() + delta.y()
            if new_height >= self.minimumHeight():
                new_geometry.setBottom(new_geometry.bottom() + delta.y())

        self.setGeometry(new_geometry)
        self.resize_start_pos = global_pos

    def _create_content_area(self):
        """Create the content area with page stack."""
        # Content container
        self.content_widget = QWidget()
        self.content_widget.setObjectName("main-content")
        self.content_widget.setMouseTracking(True)  # Enable mouse tracking
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Page stack
        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("page-stack")
        self.page_stack.setMouseTracking(True)  # Enable mouse tracking
        content_layout.addWidget(self.page_stack)

        # Add to main layout
        self.main_layout.addWidget(self.content_widget)
        self.main_layout.setStretchFactor(self.content_widget, 1)

    def _create_footer(self):
        """Create the footer with status bar."""
        # Complètement masquer la barre de statut pour éviter les artefacts visuels
        self.setStatusBar(None)

    def _on_navigate_to(self, page_id, data=None):
        """Handle navigation requests from signals."""
        self.navigate_to_page(page_id, data)

    def register_page(self, page_id: str, page_class: Type[BasePage]) -> None:
        """
        Register a page class with the manager.

        Args:
            page_id: Unique identifier for the page
            page_class: Page class to register
        """
        self.page_classes[page_id] = page_class

    def create_page(self, page_id: str) -> BasePage:
        """
        Create a page instance.

        Args:
            page_id: Page identifier

        Returns:
            BasePage: The created page instance

        Raises:
            KeyError: If page_id is not registered
        """
        if page_id not in self.page_classes:
            raise KeyError(f"Page '{page_id}' not registered")

        page = self.page_classes[page_id](self)
        page.page_id = page_id

        # Connect navigation signal
        page.navigate_to.connect(self._on_navigate_to)

        return page

    def navigate_to_page(self, page_id: str, data=None) -> None:
        """
        Navigate to a page.

        Args:
            page_id: Page identifier
            data: Optional data to pass to the page
        """
        # If we're already on this page, just update with new data
        if self.history and self.history[-1] == page_id:
            if page_id in self.pages:
                self.pages[page_id].on_enter(data)
            return

        # Get current page to call on_exit
        if self.history and self.history[-1] in self.pages:
            current_page = self.pages[self.history[-1]]
            current_page.on_exit()

        # Create page if needed
        if page_id not in self.pages:
            self.pages[page_id] = self.create_page(page_id)
            self.page_stack.addWidget(self.pages[page_id])
            # Enable mouse tracking on the new page
            self._enable_mouse_tracking_recursive(self.pages[page_id])

        # Update history and show page
        self.history.append(page_id)
        self.page_stack.setCurrentWidget(self.pages[page_id])
        self.pages[page_id].on_enter(data)

    def navigate_back(self) -> bool:
        """
        Navigate to the previous page in history.

        Returns:
            bool: True if navigation succeeded, False if history is empty
        """
        if len(self.history) <= 1:
            # Can't go back if we're on the first page
            return False

        # Get current page
        current_page_id = self.history.pop()
        if current_page_id in self.pages:
            self.pages[current_page_id].on_exit()

        # Get previous page
        previous_page_id = self.history[-1]
        if previous_page_id in self.pages:
            self.page_stack.setCurrentWidget(self.pages[previous_page_id])
            self.pages[previous_page_id].on_enter()

        return True

    def translate(self, text: str) -> str:
        """
        Translate text to the current language.

        Args:
            text: Text to translate

        Returns:
            str: Translated text
        """
        return self.translator.translate(text, self.current_language)

    def set_language(self, language_code: str) -> None:
        """
        Set the current language.

        Args:
            language_code: Language code to set
        """
        if language_code != self.current_language:
            try:
                # Store the old language in case we need to revert
                old_language = self.current_language
                
                # Store current page and data for reload
                current_page_id = None
                if self.history:
                    current_page_id = self.history[-1]

                # Set the new language
                self.current_language = language_code

                # Update UI texts in the main window
                self._update_ui_texts()
                
                # Reload current page instead of calling update_texts
                if current_page_id:
                    # Remove the current page instance
                    if current_page_id in self.pages:
                        current_page = self.pages[current_page_id]
                        current_page.on_exit()
                        self.page_stack.removeWidget(current_page)
                        del self.pages[current_page_id]
                        
                        # Pop current page from history as we're going to add it again
                        self.history.pop()
                        
                        # Recreate and navigate to the page
                        self.navigate_to_page(current_page_id)

                print(f"Language changed to: {language_code}")
                
                # Sauvegarder la configuration après le changement
                self._save_config()

            except Exception as e:
                # Revert to the old language in case of error
                print(f"Error changing language: {e}")
                self.current_language = old_language
                self._update_ui_texts()

    def _update_ui_texts(self):
        """Update all translatable texts in the main window."""
        # Update window title
        self.setWindowTitle(self.translate("JobFinder"))

        # Update header items
        self.title_label.setText(self.translate("JobFinder"))
        self.language_label.setText(self.translate("Language:"))
        self.theme_label.setText(self.translate("Theme:"))
        self.about_button.setText(self.translate("About"))

        # Update language combo box items (keeping the same language codes)
        current_lang_code = self.language_combo.currentData()
        self.language_combo.blockSignals(True)  # Prevent triggering change events
        self.language_combo.clear()

        for lang_code, lang_name in sorted(self.translator.get_available_languages().items()):
            self.language_combo.addItem(lang_name, lang_code)

        index = self.language_combo.findData(current_lang_code)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        self.language_combo.blockSignals(False)

    def apply_theme(self, theme_name: str = None) -> None:
        """
        Apply a theme to the application.

        Args:
            theme_name: Name of the theme to apply, or None for current theme
        """
        try:
            if theme_name is not None:
                self.theme_manager.set_theme(theme_name)

            # Get current theme
            theme = self.theme_manager.get_theme()

            # Apply stylesheet
            stylesheet = self.theme_manager.get_stylesheet()
            self.setStyleSheet(stylesheet)

            # Update icons color based on theme
            icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")
            
            # Update the button icons - we don't need to change the SVG files,
            # the stylesheet will handle the colors through the background

            # Update theme in the combo box if needed
            current_index = self.theme_combo.currentIndex()
            theme_id_at_index = self.theme_combo.itemData(current_index)

            if theme_id_at_index != self.theme_manager.current_theme:
                new_index = self.theme_combo.findData(self.theme_manager.current_theme)
                if new_index >= 0 and new_index != current_index:
                    # Block signals to prevent circular calls
                    self.theme_combo.blockSignals(True)
                    self.theme_combo.setCurrentIndex(new_index)
                    self.theme_combo.blockSignals(False)

            # Update all pages
            for page in self.pages.values():
                # Force update if there's a specific method
                if hasattr(page, 'apply_theme'):
                    page.apply_theme()

            # Force update
            self.update()

        except Exception as e:
            print(f"Error applying theme: {e}")

    @Slot()
    def _on_theme_changed(self, index):
        """Handle theme change from the selector."""
        theme_id = self.theme_combo.itemData(index)
        if theme_id:
            # Temporarily block signals to prevent circular calls
            old_style = self.styleSheet()
            try:
                self.apply_theme(theme_id)
                # Sauvegarder la configuration après le changement
                self._save_config()
            except Exception as e:
                # If theme application fails, restore the old style
                print(f"Theme change failed: {e}")
                self.setStyleSheet(old_style)

    @Slot()
    def _on_language_changed(self, index):
        """Handle language change from the selector."""
        lang_code = self.language_combo.itemData(index)
        if lang_code:
            self.set_language(lang_code)
            # La configuration est déjà sauvegardée dans set_language
            
    @Slot()
    def _on_theme_action_triggered(self):
        """Handle theme selection from menu."""
        action = self.sender()
        if action and action.isChecked():
            theme_id = action.data()

            # Update combo box
            index = self.theme_combo.findData(theme_id)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)

            # Apply theme
            self.apply_theme(theme_id)

    @Slot()
    def _on_language_action_triggered(self):
        """Handle language selection from menu."""
        action = self.sender()
        if action and action.isChecked():
            lang_code = action.data()

            # Update combo box
            index = self.language_combo.findData(lang_code)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)

            # Set language
            self.set_language(lang_code)

    @Slot()
    def _show_about_dialog(self):
        """Show the about dialog."""
        dialog = AboutDialog(self, self)
        dialog.exec()

    def closeEvent(self, event):
        """Handle window close event."""
        # Call on_exit for current page
        if self.history and self.history[-1] in self.pages:
            self.pages[self.history[-1]].on_exit()

        # Accept the close event
        event.accept()

    def leaveEvent(self, event):
        """Reset cursor when mouse leaves the window."""
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def _load_config(self):
        """Charger la configuration depuis le fichier JSON."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.CONFIG_FILE)
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                # Appliquer les paramètres chargés
                if "theme" in config:
                    self.theme_manager.set_theme(config["theme"])
                    
                if "language" in config:
                    self.current_language = config["language"]
                    
                print(f"Configuration chargée: thème={self.theme_manager.current_theme}, langue={self.current_language}")
            else:
                print("Aucun fichier de configuration trouvé. Création avec les paramètres par défaut.")
                self._save_config()  # Créer le fichier avec les valeurs par défaut
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")

    def _save_config(self):
        """Sauvegarder la configuration dans un fichier JSON."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.CONFIG_FILE)
        
        try:
            config = {
                "theme": self.theme_manager.current_theme,
                "language": self.current_language
            }
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
                
            print(f"Configuration sauvegardée dans {config_path}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")

    def _adjust_window_size(self):
        """Set window size to 75% of the screen resolution."""
        # Get primary screen
        screen = QGuiApplication.primaryScreen().availableGeometry()
        
        # Calculate 75% of screen size
        width = int(screen.width() * 0.75)
        height = int(screen.height() * 0.75)
        
        # Center the window
        x = int((screen.width() - width) / 2)
        y = int((screen.height() - height) / 2)
        
        # Set geometry (position and size)
        self.setGeometry(x, y, width, height)
        print(f"Window sized to 75% of screen: {width}x{height}")


