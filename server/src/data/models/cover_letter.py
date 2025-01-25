from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from . import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .job_offer import JobOffer

class CoverLetter(BaseModel, table=True):
    __tablename__ = "cover_letters"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: Optional[int] = Field(default=None, foreign_key="job_offer.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    subject: str
    greeting: str
    introduction: str
    skills_experience: str
    motivation: str
    conclusion: str
    closing: str
    recipient_info: Optional[str] = None
    pdf_data: Optional[bytes] = None

    # Relationships with other tables
    if not TYPE_CHECKING:
        user: Optional["User"] = Relationship(back_populates="cover_letters")
        job_offer: Optional["JobOffer"] = Relationship(back_populates="cover_letters")