from typing import Optional, List, Dict, Any
from sqlmodel import Field, Relationship, SQLModel, Column, JSON
from sqlalchemy import Integer, Index
from datetime import datetime, timezone
from enum import IntEnum

# =====================
# Classe de base
# =====================
class BaseModel(SQLModel):
    def as_dict(self, exclude_unset: bool = True) -> dict:
        """Convertit un modèle SQLModel en dictionnaire."""
        return self.model_dump(exclude_unset=exclude_unset)

    @classmethod
    def from_dict(cls, data: dict) -> "BaseModel":
        """Crée une instance du modèle à partir d'un dictionnaire."""
        return cls(**data)

# =====================
# Énumérations
# =====================
class DocumentType(IntEnum):
    """Types de documents supportés par l'application."""
    COVER_LETTER = 1
    CV = 2
    APPLICATION_FORM = 3
    BROWSER_CACHE = 4
    REFERENCE_LETTER = 5
    SIGNATURE = 6
    PHOTO = 7
    APPLICATION_DOCUMENT = 8
    OTHER = 99

# =====================
# Modèles principaux
# =====================
class User(BaseModel, table=True):
    """Utilisateur de l'application."""
    __tablename__ = "users"

    # Ajouter extend_existing pour éviter les erreurs d'importation multiple
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    first_name: str
    last_name: str
    password: str
    config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Relations
    documents: List["Document"] = Relationship(back_populates="user")
    applications: List["Application"] = Relationship(back_populates="user")

class JobSite(IntEnum):
    """Sites d'emploi d'où proviennent les offres."""
    LINKEDIN = 1
    INDEED = 2
    JOBUP = 3
    MONSTER = 4
    GLASSDOOR = 5
    COMPANY_WEBSITE = 6
    OTHER = 99


class JobOffer(BaseModel, table=True):
    """Offre d'emploi."""
    __tablename__ = "job_offers"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_site: JobSite = Field(sa_column=Column(Integer), default=JobSite.OTHER)
    job_link: Optional[str] = Field(unique=True)
    job_info: Dict[str, Any] = Field(sa_column=Column(JSON))
    quick_apply: bool = Field(default=False)

    # Add the index manually in __table_args__
    __table_args__ = (
        Index("idx_job_site", "job_site"),
        Index("idx_job_link", "job_link"),
        {'extend_existing': True}
    )

    # Relations
    applications: List["Application"] = Relationship(back_populates="job_offer")
    documents: List["Document"] = Relationship(back_populates="job_offer")

class Document(BaseModel, table=True):
    """Modèle générique pour tous types de documents."""
    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)

    # Propriétaire du document
    user_id: int = Field(foreign_key="users.id")

    # Direct relationships to entities (replacing DocumentRelation)
    job_id: Optional[int] = Field(default=None, foreign_key="job_offers.id")
    application_id: Optional[int] = Field(default=None, foreign_key="applications.id")

    # Type et métadonnées
    document_type: DocumentType = Field(sa_column=Column(Integer))
    name: str

    # Contenu (différents formats possibles)
    binary_content: Optional[bytes] = None
    json_content: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    text_content: Optional[str] = None

    # Métadonnées - renamed to 'doc_metadata' to avoid naming conflict
    doc_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    # Index
    __table_args__ = (
        Index("idx_documents_user_type", "user_id", "document_type"),
        Index("idx_documents_job", "job_id"),
        Index("idx_documents_application", "application_id"),
        Index("idx_documents_user", "user_id"),
        {'extend_existing': True}
    )

    # Relations
    user: "User" = Relationship(back_populates="documents")
    job_offer: Optional["JobOffer"] = Relationship(back_populates="documents")
    application: Optional["Application"] = Relationship(back_populates="documents")

class Application(BaseModel, table=True):
    """Candidature à une offre d'emploi."""
    __tablename__ = "applications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    job_id: int = Field(foreign_key="job_offers.id")

    status: str  # "submitted", "rejected", "in_progress", etc.
    application_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: Optional[datetime] = None
    app_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Index
    __table_args__ = (
        Index("idx_applications_user", "user_id"),
        Index("idx_applications_job", "job_id"),
        Index("idx_applications_status", "status"),
        {'extend_existing': True}
    )

    # Relations
    user: "User" = Relationship(back_populates="applications")
    job_offer: "JobOffer" = Relationship(back_populates="applications")
    documents: List["Document"] = Relationship(back_populates="application")