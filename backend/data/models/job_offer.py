from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship
from . import BaseModel

if TYPE_CHECKING:
    from .application import Application
    from .cover_letter import CoverLetter

class JobOffer(BaseModel, table=True):
    __tablename__ = "job_offer"
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, unique=True)
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    job_description: str
    job_link: str
    posted_date: Optional[str] = None
    work_location: Optional[str] = None
    contract_type: Optional[str] = None
    activity_rate: Optional[str] = None
    company_info: Optional[str] = None
    company_contact: Optional[str] = None
    company_url: Optional[str] = None
    categories: Optional[str] = None
    quick_apply: Optional[bool] = None

    # Relationships with other tables
    if not TYPE_CHECKING:
        applications: List["Application"] = Relationship(back_populates="job_offer")
        cover_letters: List["CoverLetter"] = Relationship(back_populates="job_offer")