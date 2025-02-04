from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship
from . import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .job_offer import JobOffer

class Application(BaseModel, table=True):
    __tablename__ = "applications"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    job_id: Optional[int] = Field(default=None, foreign_key="job_offer.id")
    application_status: str
    application_date: datetime = Field(default_factory=datetime.utcnow)

    # Relations with other tables
    if not TYPE_CHECKING:
        user: Optional["User"] = Relationship(back_populates="applications")
        job_offer: Optional["JobOffer"] = Relationship(back_populates="applications")