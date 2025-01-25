from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship
from . import BaseModel

if TYPE_CHECKING:
    from .application import Application
    from .cover_letter import CoverLetter
    from .browser_cache import BrowserCache
    from .document import Document
    from .apply_form import ApplicationForm


class User(BaseModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str
    password: str
    username: str
    preferences: Optional[str] = None
    cv_text: Optional[str] = None
    reference_letter: Optional[str] = None
    contact_info: Optional[str] = None
    signature: Optional[bytes] = None

    # Relationships with other tables
    if not TYPE_CHECKING:
        applications: List["Application"] = Relationship(back_populates="user")
        cover_letters: List["CoverLetter"] = Relationship(back_populates="user")
        browser_cache: Optional["BrowserCache"] = Relationship(back_populates="user")
        documents: List["Document"] = Relationship(back_populates="user")
        apply_forms: List["ApplicationForm"] = Relationship(back_populates="user")