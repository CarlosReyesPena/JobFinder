"""
Main application entry point.
Runs the application with the necessary pages registered.
"""

import sys
import traceback
from PySide6.QtWidgets import QApplication

from backend.UI.pages.main_window import MainWindow


def start():
    """Start the application."""
    try:
        print("Initializing application...")

        # Create the application
        app = QApplication(sys.argv)

        # Create main window
        window = MainWindow()

        # Register pages

        # Navigate to the user manager page as the starting page
        window.navigate_to.emit("user_manager", None)

        # Show window
        window.show()

        print("Starting application...")
        print("Application window displayed. Running event loop...")

        # Start the application event loop
        return app.exec()
    except Exception as e:
        print(f"Error starting application: {e}")
        print(traceback.format_exc())
        return 1


def main():
    """Main entry point for the application."""
    try:
        # Set up any global configuration here if needed

        # Start the application
        return start()
    except Exception as e:
        print(f"Fatal error: {e}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())