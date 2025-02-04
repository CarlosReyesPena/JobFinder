from .base_menu import BaseMenu
from data.managers.document_manager import DocumentManager
from data.managers.cover_letter_manager import CoverLetterManager
from win32gui import GetOpenFileNameW

class DocumentMenu(BaseMenu):
    def __init__(self, session):
        super().__init__(session)
        self.document_manager = DocumentManager(session)
        self.cover_manager = CoverLetterManager(session)

    async def display(self):
        while True:
            self.print_header("Document Management")
            print("1. List User Documents")
            print("2. Add Document")
            print("3. Delete Document")
            print("4. Back to Main Menu")

            choice = input("\nEnter your choice (1-4): ")

            if choice == '1':
                await self.list_documents()
            elif choice == '2':
                await self.add_document()
            elif choice == '3':
                await self.delete_document()
            elif choice == '4':
                break
            else:
                print("\nInvalid choice!")
                await self.wait_for_user()

    async def list_documents(self):
        try:
            user_id = int(input("\nEnter user ID: "))
            documents = await self.document_manager.get_user_documents(user_id)
            print("\nUser Documents:")
            for doc in documents:
                print(f"ID: {doc.id}, Name: {doc.name}, Type: {doc.document_type}")
        except ValueError:
            print("Invalid user ID")
        await self.wait_for_user()

    async def add_document(self):
        try:
            user_id = int(input("\nEnter user ID: "))

            # Ask for document type first
            print("\nSelect document type:")
            print("1. CV")
            print("2. Others")
            type_choice = input("Enter your choice (1-2): ")

            if type_choice == "1":
                doc_type = "CV"
            elif type_choice == "2":
                doc_type = "others"
            else:
                print("Invalid document type")
                return

            # Open native file selection window
            file_filter = (
                "Documents (*.pdf;*.doc;*.docx)|*.pdf;*.doc;*.docx|"
                "All files (*.*)|*.*|"
            )

            try:
                file_path = GetOpenFileNameW(
                    Filter=file_filter,
                    Title="Select document",
                    InitialDir="C:\\"
                )[0]  # [0] returns only the file path

                if file_path:  # If a file was selected
                    doc = await self.document_manager.add_document_from_path(user_id, file_path, doc_type)
                    print(f"\nDocument added successfully with ID: {doc.id}")
                else:
                    print("\nNo file selected")

            except Exception as e:
                print("\nNo file selected")

        except Exception as e:
            print(f"Error adding document: {e}")

        await self.wait_for_user()

    async def delete_document(self):
        try:
            doc_id = int(input("\nEnter document ID to delete: "))
            if await self.document_manager.delete_document(doc_id):
                print("Document deleted successfully")
            else:
                print("Document not found")
        except ValueError:
            print("Invalid document ID")
        await self.wait_for_user()