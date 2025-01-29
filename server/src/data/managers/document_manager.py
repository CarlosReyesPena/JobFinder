from typing import Optional, List, Tuple
from pathlib import Path
import time
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.document import Document
from ..database import get_app_data_dir


class DocumentManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_document(self, user_id: int, name: str, document_type: str, content: bytes) -> Document:
        """
        Adds a new document for a user.
        Args:
            user_id (int): User ID
            name (str): Document name
            document_type (str): Type of document
            content (bytes): Document content
        Returns:
            Document: The created document
        """
        document = Document(
            user_id=user_id,
            name=name,
            document_type=document_type,
            content=content,
        )
        self.session.add(document)
        await self.session.commit()
        return document

    async def add_document_from_path(self, user_id: int, file_path: str, document_type: str) -> Document:
        """
        Adds a new document for a user from a file.
        Args:
            user_id (int): User ID
            file_path (str): Path to the file
            document_type (str): Document type
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
        await self.session.commit()
        return document

    async def get_document(self, document_id: int) -> Optional[Document]:
        """
        Gets a document by its ID.
        Args:
            document_id (int): Document ID
        Returns:
            Optional[Document]: The document if found, None otherwise
        """
        return await self.session.get(Document, document_id)

    async def get_user_documents(self, user_id: int, document_type: Optional[str] = None) -> List[Document]:
        """
        Gets all documents for a user, optionally filtered by type.
        Args:
            user_id (int): User ID
            document_type (Optional[str]): Document type filter
        Returns:
            List[Document]: List of documents
        """
        query = select(Document).where(Document.user_id == user_id)
        if document_type:
            query = query.where(Document.document_type == document_type)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_document_from_path(self, document_id: int, file_path: str) -> Optional[Document]:
        """
        Updates an existing document with a new file.
        Args:
            document_id (int): Document ID
            file_path (str): Path to the new file
        Returns:
            Optional[Document]: The updated document or None if not found
        """
        document = await self.get_document(document_id)
        if not document:
            return None

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        document.name = path.name
        document.content = path.read_bytes()
        self.session.add(document)
        await self.session.commit()
        return document

    async def extract_to_temp(self, document_id: int) -> Tuple[bool, str]:
        """
        Extracts a document to the temporary folder.
        Args:
            document_id (int): Document ID
        Returns:
            Tuple[bool, str]: (success, file path or error message)
        """
        document = await self.get_document(document_id)
        if not document:
            return False, "Document not found"

        try:
            temp_dir = get_app_data_dir() / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            timestamp = int(time.time())
            ext = Path(document.name).suffix
            filename = f"{Path(document.name).stem}_{timestamp}{ext}"
            file_path = temp_dir / filename

            file_path.write_bytes(document.content)
            return True, str(file_path)

        except Exception as e:
            return False, f"Error during extraction: {e}"

    async def delete_document(self, document_id: int) -> bool:
        """
        Deletes a document.
        Args:
            document_id (int): Document ID
        Returns:
            bool: True if deleted, False if not found
        """
        document = await self.get_document(document_id)
        if not document:
            return False

        await self.session.delete(document)
        await self.session.commit()
        return True