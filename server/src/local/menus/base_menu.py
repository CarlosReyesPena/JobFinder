import os
from abc import ABC, abstractmethod
from sqlmodel import Session

class BaseMenu(ABC):
    def __init__(self, session: Session):
        self.session = session

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title: str):
        """Print a formatted header."""
        self.clear_screen()
        print(f"\n=== {title} ===\n")

    def wait_for_user(self):
        """Wait for user input before continuing."""
        input("\nPress Enter to continue...")

    @abstractmethod
    def display(self):
        """Display the menu and handle user input."""
        pass