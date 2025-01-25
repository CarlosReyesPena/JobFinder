from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import Session, select
from ..models.application import Application


class ApplicationManager:
    def __init__(self, session: Session):
        """
        Initializes the manager with a database session.

        Args:
            session (Session): SQLModel database session.
        """
        self.session = session

    def add_application(self, **kwargs) -> Application:
        """
        Adds a new job application.

        Args:
            kwargs (dict): Data for the application.

        Returns:
            Application: The created application.
        """
        # Required fields
        required_fields = ["user_id", "job_id", "application_status"]
        for field in required_fields:
            if not kwargs.get(field):
                raise ValueError(f"The field '{field}' is required.")

        # Set default for application_date if not provided
        if "application_date" not in kwargs or kwargs["application_date"] is None:
            kwargs["application_date"] = datetime.now(timezone.utc)

        # Create and save the application
        application = Application(**kwargs)
        self.session.add(application)
        self.session.commit()
        return application

    def get_applications(self) -> List[Application]:
        """
        Retrieves all job applications.

        Returns:
            List[Application]: A list of all applications in the database.
        """
        return self.session.exec(select(Application)).all()

    def get_application_by_id(self, application_id: int) -> Optional[Application]:
        """
        Retrieves an application by its ID.

        Args:
            application_id (int): ID of the application.

        Returns:
            Optional[Application]: The application if found, None otherwise.
        """
        return self.session.get(Application, application_id)

    def get_applications_by_user(self, user_id: int) -> List[Application]:
        """
        Retrieves all applications submitted by a specific user.

        Args:
            user_id (int): ID of the user.

        Returns:
            List[Application]: A list of applications for the specified user.
        """
        statement = select(Application).where(Application.user_id == user_id)
        return self.session.exec(statement).all()

    def get_applications_by_job(self, job_id: int) -> List[Application]:
        """
        Retrieves all applications submitted for a specific job.

        Args:
            job_id (int): ID of the job.

        Returns:
            List[Application]: A list of applications for the specified job.
        """
        statement = select(Application).where(Application.job_id == job_id)
        return self.session.exec(statement).all()

    def get_application_by_user_and_job(self, user_id: int, job_id: int) -> Optional[Application]:
        """
        Retrieves an application submitted by a specific user for a specific job.

        Args:
            user_id (int): ID of the user.
            job_id (int): ID of the job.

        Returns:
            Optional[Application]: The application if found, None otherwise.
        """
        statement = select(Application).where(
            (Application.user_id == user_id) & (Application.job_id == job_id)
        )
        return self.session.exec(statement).first()

    def update_application_status(self, application_id: int, new_status: str) -> Optional[Application]:
        """
        Updates the status of an application.

        Args:
            application_id (int): ID of the application.
            new_status (str): The new status to set.

        Returns:
            Optional[Application]: The updated application if found, None otherwise.
        """
        application = self.session.get(Application, application_id)
        if not application:
            raise ValueError(f"Application with ID {application_id} not found.")

        application.application_status = new_status
        self.session.add(application)
        self.session.commit()
        return application

    def delete_application(self, application_id: int) -> bool:
        """
        Deletes an application.

        Args:
            application_id (int): ID of the application to delete.

        Returns:
            bool: True if the application was deleted, False otherwise.
        """
        application = self.session.get(Application, application_id)
        if not application:
            return False

        self.session.delete(application)
        self.session.commit()
        return True

    def delete_all_applications(self) -> bool:
        """
        Deletes all applications.

        Returns:
            bool: True if all applications were deleted, False otherwise.
        """
        applications = self.get_applications()
        for application in applications:
            self.session.delete(application)
        self.session.commit()
        return True
