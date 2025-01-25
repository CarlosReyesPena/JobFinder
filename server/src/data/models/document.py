from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from . import BaseModel

if TYPE_CHECKING:
    from .user import User

class Document(BaseModel, table=True):
    __tablename__ = "documents"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

    # Document metadata
    name: str  # Original filename
    document_type: str  # CV, photo, others
    # Content and dates
    content: bytes  # The document itself

    # Relationship with user
    if not TYPE_CHECKING:
        user: Optional["User"] = Relationship(back_populates="documents")