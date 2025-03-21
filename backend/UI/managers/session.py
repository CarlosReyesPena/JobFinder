"""
Session Management for the application.
Provides a centralized way to handle the current user session.
"""
from PySide6.QtCore import QObject, Signal

class SessionManager(QObject):
    """
    SessionManager provides a centralized system for tracking the current user session.

    Implemented as a singleton to ensure only one instance exists.
    Uses signals to notify components when the user changes.
    """

    # Singleton instance
    _instance = None

    # Signal emitted when user changes (login/logout)
    user_changed = Signal(object)

    @classmethod
    def get_instance(cls):
        """Get the singleton instance, creating it if necessary."""
        if cls._instance is None:
            cls._instance = SessionManager()
        return cls._instance

    def __init__(self):
        """Initialize the session manager."""
        super().__init__()
        # Private attributes
        self._current_user = None

    @property
    def current_user(self):
        """Get the current logged-in user or None if not logged in."""
        return self._current_user

    @property
    def is_logged_in(self):
        """Check if a user is currently logged in."""
        return self._current_user is not None

    def login(self, user):
        """
        Set the current user and emit a signal.

        Args:
            user: User object containing user data
        """
        # Set current user
        self._current_user = user
        # Emit signal with user data
        self.user_changed.emit(user)
        # Log event
        print(f"User logged in: {user.username}")

    def logout(self):
        """
        Clear the current user and emit a signal.
        """
        # Check if already logged out
        if self._current_user is None:
            return

        # Get username for logging
        username = self._current_user.username

        # Clear current user
        self._current_user = None
        # Emit signal with None to indicate logout
        self.user_changed.emit(None)
        # Log event
        print(f"User logged out: {username}")