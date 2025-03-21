from typing import Optional, List, Dict, Any, Tuple, Type, TypeVar
from pathlib import Path
import time
import logging
from sqlmodel import select
from datetime import datetime, timezone
import tempfile
import os

from backend.data.models import (
    User, JobOffer, Document, DocumentType, Application, JobSite
)
from backend.data.database import (
    get_app_data_dir, read_session_context, write_session_context
)

# Type variable for generic methods
T = TypeVar('T')

# Logging configuration
logger = logging.getLogger(__name__)

class BaseManager:
    """Base class for all managers with common methods."""

    def __init__(self):
        """Initialize the manager without a session."""
        pass

    async def get_by_id(self, model_class: Type[T], id: int) -> Optional[T]:
        """Get an entity by its ID."""
        async with read_session_context() as session:
            return await session.get(model_class, id)

    async def get_all(self, model_class: Type[T]) -> List[T]:
        """Get all entities of a given type."""
        async with read_session_context() as session:
            result = await session.execute(select(model_class))
            return result.scalars().all()

    async def delete(self, entity) -> bool:
        """Delete an entity."""
        if not entity:
            return False
        async with write_session_context() as session:
            await session.delete(entity)
            await session.commit()
            return True


class UserManager(BaseManager):
    """Manager for user-related operations."""

    async def add_user(self,
                      email: str,
                      username: str,
                      password: str,
                      first_name: str,
                      last_name: str,
                      config: Optional[Dict[str, Any]] = None) -> User:
        """Add a new user."""
        user = User(
            email=email,
            username=username,
            password=password,  # Ideally, the password should be hashed before storing
            first_name=first_name,
            last_name=last_name,
            config=config or {}
        )
        async with write_session_context() as session:
            session.add(user)
            await session.commit()
            return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return await self.get_by_id(User, user_id)

    async def get_users(self) -> List[User]:
        """Get all users."""
        return await self.get_all(User)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        async with read_session_context() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        async with read_session_context() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update a user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update attributes
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        async with write_session_context() as session:
            session.add(user)
            await session.commit()
            return user

    async def update_config(self, user_id: int, config: Dict[str, Any]) -> Optional[User]:
        """Update a user's configuration."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Merge with existing configuration
        if user.config is None:
            user.config = {}
        user.config.update(config)

        async with write_session_context() as session:
            session.add(user)
            await session.commit()
            return user

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = await self.get_user_by_id(user_id)
        return await self.delete(user)


class JobOfferManager(BaseManager):
    """Manager for job offer related operations."""

    async def add_job_offer(self,
                           job_link: str,
                           job_info: Dict[str, Any],
                           job_site: JobSite = JobSite.OTHER,
                           quick_apply: bool = False) -> JobOffer:
        """Add a new job offer."""
        job_offer = JobOffer(
            job_link=job_link,
            job_info=job_info,
            job_site=job_site,
            quick_apply=quick_apply
        )
        async with write_session_context() as session:
            session.add(job_offer)
            await session.commit()
            return job_offer

    async def get_job_offer_by_id(self, job_id: int) -> Optional[JobOffer]:
        """Get a job offer by ID."""
        return await self.get_by_id(JobOffer, job_id)

    async def get_job_offers(self) -> List[JobOffer]:
        """Get all job offers."""
        return await self.get_all(JobOffer)

    async def get_job_offer_by_link(self, job_link: str) -> Optional[JobOffer]:
        """Get a job offer by its link."""
        async with read_session_context() as session:
            result = await session.execute(
                select(JobOffer).where(JobOffer.job_link == job_link)
            )
            return result.scalar_one_or_none()

    async def update_job_offer(self, job_id: int, **kwargs) -> Optional[JobOffer]:
        """Update a job offer."""
        job_offer = await self.get_job_offer_by_id(job_id)
        if not job_offer:
            return None

        # Update attributes
        for key, value in kwargs.items():
            if hasattr(job_offer, key):
                setattr(job_offer, key, value)

        async with write_session_context() as session:
            session.add(job_offer)
            await session.commit()
            return job_offer

    async def update_quick_apply_status(self, job_id: int, quick_apply: bool) -> Optional[JobOffer]:
        """
        Update the quick apply status of a job offer.

        Args:
            job_id: ID of the job offer
            quick_apply: New quick apply status

        Returns:
            Optional[JobOffer]: Updated job offer or None if not found
        """
        job_offer = await self.get_job_offer_by_id(job_id)
        if not job_offer:
            return None

        job_offer.quick_apply = quick_apply

        async with write_session_context() as session:
            session.add(job_offer)
            await session.commit()
            return job_offer

    async def update_job_info(self, job_id: int, job_info: Dict[str, Any]) -> Optional[JobOffer]:
        """Update job offer information."""
        job_offer = await self.get_job_offer_by_id(job_id)
        if not job_offer:
            return None

        # Merge with existing information
        job_offer.job_info.update(job_info)

        async with write_session_context() as session:
            session.add(job_offer)
            await session.commit()
            return job_offer

    async def delete_job_offer(self, job_id: int) -> bool:
        """Delete a job offer."""
        job_offer = await self.get_job_offer_by_id(job_id)
        return await self.delete(job_offer)

    async def get_quick_apply_job_offers(self) -> List[JobOffer]:
        """
        Get all job offers that support quick apply.

        Returns:
            List[JobOffer]: List of job offers with quick_apply=True
        """
        async with read_session_context() as session:
            result = await session.execute(
                select(JobOffer).where(JobOffer.quick_apply == True)
            )
            return result.scalars().all()


class DocumentManager(BaseManager):
    """Manager for document operations."""

    async def create_document(
        self,
        user_id: int,
        document_type: DocumentType,
        name: str,
        job_id: Optional[int] = None,
        application_id: Optional[int] = None,
        binary_content: Optional[bytes] = None,
        json_content: Optional[Dict[str, Any]] = None,
        text_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Create a document.

        Args:
            user_id: User ID
            document_type: Document type
            name: Document name
            job_id: Optional job ID
            application_id: Optional application ID
            binary_content: Optional binary content
            json_content: Optional JSON content
            text_content: Optional text content
            metadata: Optional metadata

        Returns:
            Document: The created document
        """
        document = Document(
            user_id=user_id,
            document_type=document_type,
            name=name,
            job_id=job_id,
            application_id=application_id,
            binary_content=binary_content,
            json_content=json_content,
            text_content=text_content,
            doc_metadata=metadata,
            updated_at=datetime.now(timezone.utc)
        )
        async with write_session_context() as session:
            session.add(document)
            await session.commit()
            return document

    async def get_document_by_id(self, document_id: int) -> Optional[Document]:
        """Get a document by ID."""
        return await self.get_by_id(Document, document_id)

    async def get_documents(self) -> List[Document]:
        """Get all documents."""
        return await self.get_all(Document)

    async def get_user_documents(
        self,
        user_id: int,
        document_type: Optional[DocumentType] = None
    ) -> List[Document]:
        """Get all documents for a user, optionally filtered by type."""
        async with read_session_context() as session:
            query = select(Document).where(Document.user_id == user_id)
            if document_type:
                query = query.where(Document.document_type == document_type)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_documents_for_job(
        self,
        job_id: int,
        user_id: Optional[int] = None,
        document_type: Optional[DocumentType] = None
    ) -> List[Document]:
        """
        Get all documents for a job offer, optionally filtered by user and type.

        Args:
            job_id: ID of the job offer
            user_id: Optional user ID filter
            document_type: Optional document type filter

        Returns:
            List[Document]: Documents for the job
        """
        async with read_session_context() as session:
            query = select(Document).where(Document.job_id == job_id)
            if user_id:
                query = query.where(Document.user_id == user_id)
            if document_type:
                query = query.where(Document.document_type == document_type)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_documents_for_application(
        self,
        application_id: int,
        document_type: Optional[DocumentType] = None
    ) -> List[Document]:
        """
        Get all documents for an application, optionally filtered by type.

        Args:
            application_id: ID of the application
            document_type: Optional document type filter

        Returns:
            List[Document]: Documents for the application
        """
        async with read_session_context() as session:
            query = select(Document).where(Document.application_id == application_id)
            if document_type:
                query = query.where(Document.document_type == document_type)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_last_document_by_type(
        self,
        user_id: int,
        document_type: DocumentType
    ) -> Optional[Document]:
        """
        Get the most recent document of a specific type for a user.

        Args:
            user_id: User ID
            document_type: Type of document

        Returns:
            Optional[Document]: The most recent document or None
        """
        async with read_session_context() as session:
            query = (
                select(Document)
                .where(Document.user_id == user_id)
                .where(Document.document_type == document_type)
                .order_by(Document.created_at.desc())
                .limit(1)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_latest_cover_letter_for_job(
        self,
        job_id: int,
        user_id: int
    ) -> Optional[Document]:
        """Get the latest cover letter for a specific job."""
        async with read_session_context() as session:
            query = (
                select(Document)
                .where(Document.job_id == job_id)
                .where(Document.user_id == user_id)
                .where(Document.document_type == DocumentType.COVER_LETTER)
                .order_by(Document.created_at.desc())
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def create_document_from_path(
        self,
        user_id: int,
        document_type: DocumentType,
        file_path: str,
        job_id: Optional[int] = None,
        application_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create a document from a file path."""
        try:
            # Read file content
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            binary_content = path.read_bytes()
            name = path.name

            # Create document
            return await self.create_document(
                user_id=user_id,
                document_type=document_type,
                name=name,
                job_id=job_id,
                application_id=application_id,
                binary_content=binary_content,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error creating document from path: {str(e)}")
            raise

    async def update_document(
        self,
        document_id: int,
        **kwargs
    ) -> Optional[Document]:
        """Update a document."""
        document = await self.get_document_by_id(document_id)
        if not document:
            return None

        # Update attributes
        for key, value in kwargs.items():
            if hasattr(document, key):
                setattr(document, key, value)

        # For JSON content updates, merge instead of replace
        if 'json_content' in kwargs and isinstance(kwargs['json_content'], dict):
            if not document.json_content:
                document.json_content = {}
            document.json_content.update(kwargs['json_content'])

        async with write_session_context() as session:
            session.add(document)
            await session.commit()
            return document

    async def delete_document(self, document_id: int) -> bool:
        """
        Delete a document.

        Args:
            document_id: The ID of the document to delete.

        Returns:
            bool: True if the document was successfully deleted, False otherwise.
        """
        async with write_session_context() as session:
            try:
                document = await session.get(Document, document_id)
                if not document:
                    return False

                await session.delete(document)
                await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error deleting document: {e}")
                return False

    async def extract_to_temp(self, document_id: int) -> tuple[bool, str]:
        """
        Extract a document to a temporary file and return the path.

        Args:
            document_id: The ID of the document to extract.

        Returns:
            tuple[bool, str]: A tuple containing a boolean indicating success and either
                              the path to the temporary file or an error message.
        """
        async with read_session_context() as session:
            try:
                document = await session.get(Document, document_id)
                if not document:
                    return False, "Document not found"
                    
                # Create temp file with appropriate extension
                file_name = document.name if document.name else f"document_{document_id}"
                
                # Try to extract file extension from the name
                _, ext = os.path.splitext(file_name)
                if not ext and document.metadata and "original_file_path" in document.metadata:
                    _, ext = os.path.splitext(document.metadata["original_file_path"])
                    
                # Create a temporary file
                fd, temp_path = tempfile.mkstemp(suffix=ext)
                
                # Write content to the temp file
                with os.fdopen(fd, 'wb') as tmp:
                    # Use binary content if available
                    if document.binary_content:
                        tmp.write(document.binary_content)
                    # Fallback to JSON content
                    elif document.json_content:
                        import json
                        tmp.write(json.dumps(document.json_content, indent=2).encode('utf-8'))
                    # Fallback to text content
                    elif document.text_content:
                        tmp.write(document.text_content.encode('utf-8'))
                    else:
                        os.unlink(temp_path)
                        return False, "Document has no content"
                    
                return True, temp_path
                
            except Exception as e:
                logger.error(f"Error extracting document to temp file: {e}")
                return False, f"Error extracting document: {str(e)}"

    async def create_cover_letter_for_job(
        self,
        user_id: int,
        job_id: int,
        name: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create a cover letter document for a job."""
        # Generate a text version of the cover letter
        text_content = (
            f"{content.get('greeting', '')}\n\n"
            f"{content.get('introduction', '')}\n\n"
            f"{content.get('skills_experience', '')}\n\n"
            f"{content.get('motivation', '')}\n\n"
            f"{content.get('conclusion', '')}\n\n"
            f"{content.get('closing', '')}"
        )
        
        return await self.create_document(
            user_id=user_id,
            document_type=DocumentType.COVER_LETTER,
            name=name,
            job_id=job_id,
            json_content=content,
            text_content=text_content,
            metadata=metadata
        )

    async def create_cv(
        self,
        user_id: int,
        name: str,
        binary_content: Optional[bytes] = None,
        json_content: Optional[Dict[str, Any]] = None,
        text_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create a CV document."""
        return await self.create_document(
            user_id=user_id,
            document_type=DocumentType.CV,
            name=name,
            binary_content=binary_content,
            json_content=json_content,
            text_content=text_content,
            metadata=metadata
        )

    async def create_application_form(
        self,
        user_id: int,
        name: str,
        form_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create an application form document."""
        return await self.create_document(
            user_id=user_id,
            document_type=DocumentType.APPLICATION_FORM,
            name=name,
            json_content=form_data,
            metadata=metadata
        )

    async def create_document_for_application(
        self,
        user_id: int,
        application_id: int,
        document_type: DocumentType,
        name: str,
        binary_content: Optional[bytes] = None,
        json_content: Optional[Dict[str, Any]] = None,
        text_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create a document associated with an application."""
        return await self.create_document(
            user_id=user_id,
            document_type=document_type,
            name=name,
            application_id=application_id,
            binary_content=binary_content,
            json_content=json_content,
            text_content=text_content,
            metadata=metadata
        )

    async def extract_latest_document_by_type_to_temp(
        self,
        user_id: int,
        document_type: DocumentType
    ) -> Tuple[bool, str]:
        """
        Extract the latest document of a specific type for a user to a temporary file.

        Args:
            user_id: User ID
            document_type: Type of document

        Returns:
            Tuple[bool, str]: Success status and file path or error message
        """
        # Get the latest document
        document = await self.get_last_document_by_type(user_id, document_type)
        if not document:
            return False, f"No {document_type.value} found for this user"
        
        # Vérifier si le document a du contenu binaire
        if not document.binary_content:
            # Si pas de contenu binaire, créer un fichier texte avec le contenu texte si disponible
            if document.text_content:
                # Create temp directory if it doesn't exist
                temp_dir = get_app_data_dir() / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)

                # Create a filename with timestamp
                timestamp = int(time.time())
                filename = f"{document.name.split('.')[0]}_{timestamp}.txt"
                
                # Create the temp file path
                temp_path = temp_dir / filename
                
                # Write text content to temp file
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(document.text_content)
                    
                return True, str(temp_path)
            else:
                return False, "Document has no content to extract"
            
        # Extract to temp file
        return await self.extract_to_temp(document.id)

    async def update_document_json_content(
        self,
        document_id: int,
        json_content: Dict[str, Any]
    ) -> bool:
        """
        Update JSON content for a document.
        
        Args:
            document_id: ID of the document to update
            json_content: New JSON content to merge
            
        Returns:
            bool: True if update was successful
        """
        document = await self.get_document_by_id(document_id)
        if not document:
            return False
            
        # Ensure the document has JSON content
        if not document.json_content:
            document.json_content = {}
            
        # Merge the new content
        document.json_content.update(json_content)
        
        # Update the text content if it's a cover letter
        if document.document_type == DocumentType.COVER_LETTER:
            # Regenerate text content based on JSON
            text_content = (
                f"{json_content.get('greeting', '')}\n\n"
                f"{json_content.get('introduction', '')}\n\n"
                f"{json_content.get('skills_experience', '')}\n\n"
                f"{json_content.get('motivation', '')}\n\n"
                f"{json_content.get('conclusion', '')}\n\n"
                f"{json_content.get('closing', '')}"
            )
            document.text_content = text_content
        
        # Save changes
        async with write_session_context() as session:
            session.add(document)
            await session.commit()
            return True


class ApplicationManager(BaseManager):
    """Manager for application tracking operations."""

    async def create_application(
        self,
        user_id: int,
        job_id: int,
        status: str = "submitted",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Application:
        """
        Create a new application.

        Args:
            user_id: User ID
            job_id: Job offer ID
            status: Application status (default: "submitted")
            metadata: Additional metadata

        Returns:
            Application: The created application
        """
        application = Application(
            user_id=user_id,
            job_id=job_id,
            status=status,
            app_metadata=metadata or {}
        )
        async with write_session_context() as session:
            session.add(application)
            await session.commit()
            return application

    async def get_application_by_id(self, application_id: int) -> Optional[Application]:
        """Get an application by ID."""
        return await self.get_by_id(Application, application_id)

    async def get_applications(self) -> List[Application]:
        """Get all applications."""
        return await self.get_all(Application)

    async def get_user_applications(self, user_id: int) -> List[Application]:
        """Get all applications for a user."""
        async with read_session_context() as session:
            result = await session.execute(
                select(Application).where(Application.user_id == user_id)
            )
            return result.scalars().all()

    async def get_job_applications(self, job_id: int) -> List[Application]:
        """Get all applications for a job."""
        async with read_session_context() as session:
            result = await session.execute(
                select(Application).where(Application.job_id == job_id)
            )
            return result.scalars().all()

    async def update_application_status(
        self,
        application_id: int,
        status: str
    ) -> Optional[Application]:
        """
        Update the status of an application.

        Args:
            application_id: Application ID
            status: New status

        Returns:
            Optional[Application]: Updated application or None if not found
        """
        application = await self.get_application_by_id(application_id)
        if not application:
            return None

        application.status = status
        application.last_updated = datetime.now(timezone.utc)

        async with write_session_context() as session:
            session.add(application)
            await session.commit()
            return application

    async def update_application(
        self,
        application_id: int,
        **kwargs
    ) -> Optional[Application]:
        """
        Update an application.

        Args:
            application_id: Application ID
            **kwargs: Attributes to update

        Returns:
            Optional[Application]: Updated application or None if not found
        """
        application = await self.get_application_by_id(application_id)
        if not application:
            return None

        # Gérer spécifiquement app_metadata pour fusionner au lieu de remplacer
        if 'app_metadata' in kwargs and isinstance(kwargs['app_metadata'], dict):
            if not application.app_metadata:
                application.app_metadata = {}
            application.app_metadata.update(kwargs.pop('app_metadata'))

        # Update attributes
        for key, value in kwargs.items():
            if hasattr(application, key):
                setattr(application, key, value)

        # Always update the updated_at timestamp
        application.last_updated = datetime.now(timezone.utc)

        async with write_session_context() as session:
            session.add(application)
            await session.commit()
            return application

    async def delete_application(self, application_id: int) -> bool:
        """Delete an application."""
        application = await self.get_application_by_id(application_id)
        return await self.delete(application)