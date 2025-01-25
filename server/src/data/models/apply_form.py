from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, Column
from sqlalchemy.types import JSON
from . import BaseModel

if TYPE_CHECKING:
    from .user import User

class ApplicationForm(BaseModel, table=True):
    __tablename__ = "apply_forms"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    site_name: str
    form_data: dict = Field(default={}, sa_column=Column(JSON))

    # Relationship with user
    if not TYPE_CHECKING:
        user: Optional["User"] = Relationship(back_populates="apply_forms")
