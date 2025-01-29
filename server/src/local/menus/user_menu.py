from .base_menu import BaseMenu
from data.managers.user_manager import UserManager
from win32gui import GetOpenFileNameW

class UserMenu(BaseMenu):
    def __init__(self, session):
        super().__init__(session)
        self.user_manager = UserManager(session)

    async def display(self):
        while True:
            self.print_header("User Management")
            print("1. List All Users")
            print("2. Add New User")
            print("3. Delete User")
            print("4. Add User Signature")
            print("5. Menage Reference Letter")
            print("6. Back to Main Menu")

            choice = input("\nEnter your choice (1-5): ")

            if choice == '1':
                await self.list_users()
            elif choice == '2':
                await self.add_user()
            elif choice == '3':
                await self.delete_user()
            elif choice == '4':
                await self.add_user_signature()
            elif choice == '5':
                await self.menage_reference_letter()
            elif choice == '6':
                break
            else:
                print("\nInvalid choice!")
                self.wait_for_user()

    async def list_users(self):
        users = await self.user_manager.get_users()
        print("\nRegistered Users:")
        for user in users:
            print(f"ID: {user.id}, Name: {user.first_name} {user.last_name}, Email: {user.email}")
        self.wait_for_user()

    async def add_user_signature(self):
        try:
            user_id = int(input("\nEnter user ID: "))

            # Correctly formatted file filter
            file_filter = "Image Files (*.png;*.jpg;*.jpeg;*.bmp)|*.png;*.jpg;*.jpeg;*.bmp|All Files (*.*)|*.*"
            try:
                file_path = GetOpenFileNameW(
                    Filter=file_filter,
                    Title="Select signature image",
                    InitialDir="C:\\"
                )[0]

                if file_path:
                    await self.user_manager.add_signature_from_path(user_id, file_path)
                    print(f"\nSignature added successfully for user ID: {user_id}")
                else:
                    print("\nNo file selected")

            except Exception as e:
                print(f"\nError selecting file: {e}")

        except ValueError:
            print("Invalid user ID")
        self.wait_for_user()

    async def menage_reference_letter(self):
        try:
            user_id = int(input("\nEnter user ID: "))
            print("\n Choose an option: \n 1. Add Reference Letter \n 2. Delete Reference Letter")
            choice = input("\nEnter your choice (1-2): ")
            if choice == '1':
                reference_text = self.get_multiline_input("Enter reference letter text : ")
                try:
                    await self.user_manager.add_reference_letter(user_id, reference_text)
                    print(f"\nReference letter added successfully for user ID: {user_id}")
                except Exception as e:
                    print(f"\nError adding reference letter: {e}")
            elif choice == '2':
                try:
                    await self.user_manager.delete_reference_letter(user_id)
                    print(f"\nReference letter deleted successfully for user ID: {user_id}")
                except Exception as e:
                    print(f"\nError deleting reference letter: {e}")

        except ValueError:
            print("Invalid user or job ID")
        self.wait_for_user()

    def get_multiline_input(self, prompt: str) -> str:
        """
        Allows multiline text input. User ends input with a line containing only '.'
        """
        print(f"{prompt} (end with a line containing only '.')")
        lines = []
        while True:
            line = input()
            if line == '.':
                break
            lines.append(line)
        return '\n'.join(lines)

    async def add_user(self):
        print("\nAdding new user:")
        # Simple fields
        user_data = {
            'first_name': input("First name: "),
            'last_name': input("Last name: "),
            'email': input("Email: "),
            'password': input("Password: "),
            'username': input("Username: "),
        }

        # Multiline fields
        user_data['cv_text'] = self.get_multiline_input("\nCV Text")
        user_data['contact_info'] = self.get_multiline_input("\nContact Info")

        try:
            user = await self.user_manager.add_user(**user_data)
            print(f"\nUser added successfully with ID: {user.id}")
        except Exception as e:
            print(f"\nError adding user: {e}")
        self.wait_for_user()

    async def delete_user(self):
        try:
            user_id = int(input("\nEnter user ID to delete: "))
            if await self.user_manager.delete_user(user_id):
                print(f"User {user_id} deleted successfully")
            else:
                print(f"User {user_id} not found")
        except ValueError:
            print("Invalid user ID")
        self.wait_for_user()