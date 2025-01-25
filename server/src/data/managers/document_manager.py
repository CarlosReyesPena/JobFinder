from typing import Optional, List, Tuple
from pathlib import Path
import time
from sqlmodel import Session, select
from ..models.document import Document
from ..database import get_app_data_dir

class DocumentManager:
    def __init__(self, session: Session):
        self.session = session

    def add_document(self, user_id: int, name: str, document_type: str, content: bytes) -> Document:
        """Adds a new document for a user."""
        document = Document(
            user_id=user_id,
            name=name,
            document_type=document_type,
            content=content,
        )
        self.session.add(document)
        self.session.commit()
        return document

    def add_document_from_path(self, user_id: int, file_path: str, document_type: str) -> Document:
        """
        Adds a new document for a user from a file.
        Args:
            user_id: User ID
            file_path: Path to the file
            document_type: Document type
            description: Optional description
            tags: Optional tags
        Returns:
            Document: The created document
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        document = Document(
            user_id=user_id,
            name=path.name,
            document_type=document_type,
            content=path.read_bytes(),
        )

        self.session.add(document)
        self.session.commit()
        return document

    def get_document(self, document_id: int) -> Optional[Document]:
        """Gets a document by its ID."""
        return self.session.get(Document, document_id)

    def get_user_documents(self, user_id: int, document_type: Optional[str] = None) -> List[Document]:
        """Gets all documents for a user, optionally filtered by type."""
        query = select(Document).where(Document.user_id == user_id)
        if document_type:
            query = query.where(Document.document_type == document_type)
        return self.session.exec(query).all()

    def update_document_from_path(self, document_id: int, file_path: str) -> Optional[Document]:
        """Updates an existing document with a new file."""
        document = self.get_document(document_id)
        if not document:
            return None

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        document.name = path.name
        document.content = path.read_bytes()
        self.session.add(document)
        self.session.commit()
        return document

    def extract_to_temp(self, document_id: int) -> Tuple[bool, str]:
        """
        Extracts a document to the temporary folder.
        Returns:
            Tuple[bool, str]: (success, file path or error message)
        """
        document = self.get_document(document_id)
        if not document:
            return False, "Document not found"

        try:
            # Set temp directory path according to OS
            temp_dir = get_app_data_dir() / "temp"

            # Create temp directory
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Create unique filename with timestamp
            timestamp = int(time.time())
            ext = Path(document.name).suffix
            filename = f"{Path(document.name).stem}_{timestamp}{ext}"
            file_path = temp_dir / filename

            # Write file
            file_path.write_bytes(document.content)
            return True, str(file_path)

        except Exception as e:
            return False, f"Error during extraction: {e}"

    def delete_document(self, document_id: int) -> bool:
        """Deletes a document."""
        document = self.get_document(document_id)
        if not document:
            return False

        self.session.delete(document)
        self.session.commit()
        return True