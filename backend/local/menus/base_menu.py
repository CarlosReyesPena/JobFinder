import os
from abc import ABC, abstractmethod
from sqlmodel import Session
import asyncio

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

    async def wait_for_user(self, prompt: str = "Press Enter to continue..."):
        # Use asyncio.to_thread to run the blocking input() in a separate thread
        return await asyncio.to_thread(input, prompt)

    @abstractmethod
    async def display(self):
        """Display the menu and handle user input."""
        pass