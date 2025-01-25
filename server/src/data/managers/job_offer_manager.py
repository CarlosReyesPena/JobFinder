from typing import Optional, List
from sqlmodel import Session, select
from ..models.job_offer import JobOffer


class JobOfferManager:
    def __init__(self, session: Session):
        self.session = session

    def add_job_offer(self, **kwargs) -> Optional[JobOffer]:
        """
        Adds a new job offer to the database.
        Checks if the offer with `external_id` already exists.
        Args:
            kwargs (dict): Job offer data.
        Returns:
            Optional[JobOffer]: The created offer or None if it already exists.
        """
        # Required fields
        required_fields = ["external_id", "job_description", "job_link"]
        for field in required_fields:
            if not kwargs.get(field):
                raise ValueError(f"The field {field} is required.")

        # Check if offer already exists
        existing_offer = self.get_job_offer_by_external_id(kwargs["external_id"])
        if existing_offer:
            return existing_offer

        # Create and add the offer
        job_offer = JobOffer(**kwargs)
        self.session.add(job_offer)
        self.session.commit()
        return job_offer

    def get_job_offers(self) -> List[JobOffer]:
        """
        Retrieves all job offers.
        Returns:
            List[JobOffer]: List of job offers.
        """
        return self.session.exec(select(JobOffer)).all()

    def get_job_offers_by_quick_apply(self) -> List[JobOffer]:
        """
        Retrieves job offers with quick apply enabled.
        Returns:
            List[JobOffer]: List of Quick Apply job offers.
        """
        statement = select(JobOffer).where(JobOffer.quick_apply == True)
        return self.session.exec(statement).all()

    def get_job_offer_by_id(self, id: int) -> Optional[JobOffer]:
        """
        Retrieves a job offer by its ID.
        Args:
            id (int): Offer ID.
        Returns:
            Optional[JobOffer]: The found offer or None.
        """
        return self.session.get(JobOffer, id)

    def get_job_offer_by_external_id(self, external_id: str) -> Optional[JobOffer]:
        """
        Retrieves a job offer by its unique external_id.
        Args:
            external_id (str): Unique identifier of the offer.
        Returns:
            Optional[JobOffer]: The found offer or None.
        """
        statement = select(JobOffer).where(JobOffer.external_id == external_id)
        return self.session.exec(statement).first()

    def update_job_offer(self, external_id: int, **kwargs) -> Optional[JobOffer]:
        """
        Updates job offer information.
        Args:
            external_id (int): ID of the offer to update.
            kwargs (dict): Fields to update.
        Returns:
            Optional[JobOffer]: The updated offer or None if not found.
        """
        job_offer = self.get_job_offer_by_id(external_id)
        if not job_offer:
            raise ValueError(f"Cannot update offer with ID {external_id}: not found.")

        for key, value in kwargs.items():
            if hasattr(job_offer, key) and value is not None:
                setattr(job_offer, key, value)

        self.session.add(job_offer)
        self.session.commit()
        return job_offer

    def get_id_by_external_id(self, external_id: str) -> Optional[int]:
        """
        Retrieves a job offer ID by its external_id.
        Args:
            external_id (str): Unique identifier of the offer.
        Returns:
            Optional[int]: Offer ID or None if not found.
        """
        job_offer = self.get_job_offer_by_external_id(external_id)
        if job_offer:
            return job_offer.id
        return None

    def delete_job_offer(self, external_id: int) -> bool:
        """
        Deletes a job offer.
        Args:
            external_id (int): ID of the offer to delete.
        Returns:
            bool: True if the offer was deleted, False otherwise.
        """
        job_offer = self.get_job_offer_by_id(external_id)
        if not job_offer:
            return False

        self.session.delete(job_offer)
        self.session.commit()
        return True

    def delete_all_job_offers(self) -> bool:
        """
        Deletes all job offers.
        Returns:
            bool: True if all offers were deleted, False otherwise.
        """
        job_offers = self.get_job_offers()
        for job_offer in job_offers:
            self.session.delete(job_offer)
        self.session.commit()
        return True
