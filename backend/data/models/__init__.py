from sqlmodel import SQLModel

class BaseModel(SQLModel):
    def as_dict(self, exclude_unset: bool = True) -> dict:
        """Convertit un modèle SQLModel en dictionnaire."""
        return self.dict(exclude_unset=exclude_unset)

    @classmethod
    def from_dict(cls, data: dict) -> "BaseModel":
        """Crée une instance du modèle à partir d'un dictionnaire."""
        return cls(**data)

# Import all models to make them available through models package
from .user import User
from .application import Application
from .job_offer import JobOffer
from .cover_letter import CoverLetter
from .document import Document
from .browser_cache import BrowserCache
from .apply_form import ApplicationForm

__all__ = [
    "User",
    "Application",
    "JobOffer",
    "CoverLetter",
    "Document",
    "BrowserCache",
    "ApplicationForm",
    "BaseModel"
]