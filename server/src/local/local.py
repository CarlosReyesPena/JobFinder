import sys
import logging
import asyncio
from typing import Optional
from data.database import DatabaseManager
from .menus.database_menu import DatabaseMenu
from .menus.user_menu import UserMenu
from .menus.jobup_menu import JobUpMenu
from .menus.document_menu import DocumentMenu

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jobfinder.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class LocalApp:
    def __init__(self):
        """Initialize the local application with database connection and menus."""
        self.db: Optional[DatabaseManager] = None
        self.session = None
        self.menus = {}

    async def initialize(self):
        """Asynchronously initialize the application."""
        try:
            await self.setup_database()
            self.init_menus()
            logger.info("LocalApp initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LocalApp: {e}")
            await self.cleanup()
            raise

    async def setup_database(self):
        """Setup database connection and session."""
        try:
            self.db = DatabaseManager()
            self.session = await self.db.get_session()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise

    def init_menus(self):
        """Initialize all menu classes."""
        try:
            self.menus = {
                '1': DatabaseMenu(self.session),
                '2': UserMenu(self.session),
                '3': JobUpMenu(self.session),
                '4': DocumentMenu(self.session)
            }
            logger.info("All menus initialized")
        except Exception as e:
            logger.error(f"Menu initialization failed: {e}")
            raise

    async def display_main_menu(self):
        """Display the main menu and handle user input."""
        while True:
            try:
                self.menus['1'].clear_screen()  # Using any menu's clear_screen method
                self._print_main_menu()
                choice = input("\nEnter your choice (1-5): ").strip()

                if choice == '5':
                    print("\nGoodbye!")
                    break
                elif choice in self.menus:
                    await self.menus[choice].display()
                else:
                    print("\nInvalid choice! Please try again.")
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n\nProgram interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in main menu: {e}")
                print(f"\nAn error occurred: {e}")
                input("\nPress Enter to continue...")

    def _print_main_menu(self):
        """Print the main menu options."""
        print("\n=== JobFinder Management System ===")
        print("\n1. Database Management")
        print("2. User Management")
        print("3. JobUp Operations")
        print("4. Document Management")
        print("5. Exit")

    async def cleanup(self):
        """Cleanup resources before exiting."""
        if self.session:
            try:
                await self.session.close()
                logger.info("Database session closed")
            except Exception as e:
                logger.error(f"Error closing database session: {e}")

    async def run(self):
        """Main entry point to run the application."""
        try:
            await self.initialize()
            await self.display_main_menu()
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            await self.cleanup()

def main():
    """Application entry point with error handling."""
    try:
        app = LocalApp()
        asyncio.run(app.run())
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()