from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.application import Application


class ApplicationManager:
    def __init__(self, session: AsyncSession):
        """
        Initializes the manager with a database session.

        Args:
            session (AsyncSession): SQLModel database session.
        """
        self.session = session

    async def add_application(self, **kwargs) -> Application:
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
        await self.session.commit()
        return application

    async def get_applications(self) -> List[Application]:
        """
        Retrieves all job applications.

        Returns:
            List[Application]: A list of all applications in the database.
        """
        result = await self.session.execute(select(Application))
        return result.scalars().all()

    async def get_application_by_id(self, application_id: int) -> Optional[Application]:
        """
        Retrieves an application by its ID.

        Args:
            application_id (int): ID of the application.

        Returns:
            Optional[Application]: The application if found, None otherwise.
        """
        return await self.session.get(Application, application_id)

    async def get_applications_by_user(self, user_id: int) -> List[Application]:
        """
        Retrieves all applications submitted by a specific user.

        Args:
            user_id (int): ID of the user.

        Returns:
            List[Application]: A list of applications for the specified user.
        """
        result = await self.session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        return result.scalars().all()

    async def get_applications_by_job(self, job_id: int) -> List[Application]:
        """
        Retrieves all applications submitted for a specific job.

        Args:
            job_id (int): ID of the job.

        Returns:
            List[Application]: A list of applications for the specified job.
        """
        result = await self.session.execute(
            select(Application).where(Application.job_id == job_id)
        )
        return result.scalars().all()

    async def get_application_by_user_and_job(
        self, user_id: int, job_id: int
    ) -> Optional[Application]:
        """
        Retrieves an application submitted by a specific user for a specific job.

        Args:
            user_id (int): ID of the user.
            job_id (int): ID of the job.

        Returns:
            Optional[Application]: The application if found, None otherwise.
        """
        result = await self.session.execute(
            select(Application).where(
                (Application.user_id == user_id) & (Application.job_id == job_id)
            )
        )
        return result.scalar_one_or_none()

    async def update_application_status(
        self, application_id: int, new_status: str
    ) -> Optional[Application]:
        """
        Updates the status of an application.

        Args:
            application_id (int): ID of the application.
            new_status (str): The new status to set.

        Returns:
            Optional[Application]: The updated application if found, None otherwise.
        """
        application = await self.get_application_by_id(application_id)
        if not application:
            raise ValueError(f"Application with ID {application_id} not found.")

        application.application_status = new_status
        self.session.add(application)
        await self.session.commit()
        return application

    async def delete_application(self, application_id: int) -> bool:
        """
        Deletes an application.

        Args:
            application_id (int): ID of the application to delete.

        Returns:
            bool: True if the application was deleted, False otherwise.
        """
        application = await self.get_application_by_id(application_id)
        if not application:
            return False

        await self.session.delete(application)
        await self.session.commit()
        return True

    async def delete_all_applications(self) -> bool:
        """
        Deletes all applications.

        Returns:
            bool: True if all applications were deleted, False otherwise.
        """
        applications = await self.get_applications()
        for application in applications:
            await self.session.delete(application)
        await self.session.commit()
        return True
