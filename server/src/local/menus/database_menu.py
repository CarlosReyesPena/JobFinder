from .base_menu import BaseMenu
from data.managers.user_manager import UserManager
from data.managers.job_offer_manager import JobOfferManager
from data.database import DatabaseManager

class DatabaseMenu(BaseMenu):
    def __init__(self, session):
        super().__init__(session)
        self.db = DatabaseManager()
        self.user_manager = UserManager(session)
        self.job_manager = JobOfferManager(session)

    async def display(self):
        while True:
            self.print_header("Database Management")
            print("1. Show Database Info")
            print("2. Reset Database")
            print("3. Back to Main Menu")

            choice = input("\nEnter your choice (1-3): ")

            if choice == '1':
                await self.show_info()
            elif choice == '2':
                await self.reset_database()
            elif choice == '3':
                break
            else:
                print("\nInvalid choice!")
                self.wait_for_user()

    async def show_info(self):
        print("\nDatabase Information:")
        users = len(await self.user_manager.get_users())
        jobs = len(await self.job_manager.get_job_offers())
        print(f"Users: {users}")
        print(f"Job Offers: {jobs}")
        self.wait_for_user()

    async def reset_database(self):
        confirm = input("\nWARNING: This will delete all data. Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            if await self.db.delete_database():
                print("Database reset successful")
                await self.db.init_db()
                print("New database initialized")
            else:
                print("Failed to reset database")
            self.wait_for_user()