from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from . import BaseModel

if TYPE_CHECKING:
    from .user import User

class BrowserCache(BaseModel, table=True):
    __tablename__ ="browser_cache"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    cache_data: bytes
    last_updated: str

    # Relationship with user
    if not TYPE_CHECKING:
        user: Optional["User"] = Relationship(back_populates="browser_cache")