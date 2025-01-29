from typing import Optional, List
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.apply_form import ApplicationForm


class ApplyFormManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_apply_form(self, user_id: int, site_name: str, form_data: dict) -> ApplicationForm:
        """
        Adds a new application form.
        Args:
            user_id (int): User ID
            site_name (str): Name of the job site
            form_data (dict): Form data
        Returns:
            ApplicationForm: The created form
        """
        apply_form = ApplicationForm(
            user_id=user_id,
            site_name=site_name,
            form_data=form_data
        )
        self.session.add(apply_form)
        await self.session.commit()
        return apply_form

    async def get_apply_form_by_user_and_site(
        self, user_id: int, site_name: str
    ) -> Optional[ApplicationForm]:
        """
        Retrieves an application form for a specific user and site.
        Args:
            user_id (int): User ID
            site_name (str): Name of the job site
        Returns:
            Optional[ApplicationForm]: The found form or None
        """
        result = await self.session.execute(
            select(ApplicationForm).where(
                ApplicationForm.user_id == user_id,
                ApplicationForm.site_name == site_name
            )
        )
        return result.scalar_one_or_none()

    async def get_last_apply_form_by_user(self, user_id: int) -> Optional[ApplicationForm]:
        """
        Retrieves the last application form for a specific user.
        Args:
            user_id (int): User ID
        Returns:
            Optional[ApplicationForm]: The last form or None
        """
        result = await self.session.execute(
            select(ApplicationForm)
            .where(ApplicationForm.user_id == user_id)
            .order_by(ApplicationForm.id.desc())
        )
        return result.scalar_one_or_none()

    async def get_apply_forms_by_user(self, user_id: int) -> List[ApplicationForm]:
        """
        Retrieves all application forms for a specific user.
        Args:
            user_id (int): User ID
        Returns:
            List[ApplicationForm]: List of forms
        """
        result = await self.session.execute(
            select(ApplicationForm).where(ApplicationForm.user_id == user_id)
        )
        return result.scalars().all()

    async def delete_all_apply_forms(self) -> bool:
        """
        Deletes all application forms.
        Returns:
            bool: True if successful
        """
        result = await self.session.execute(select(ApplicationForm))
        apply_forms = result.scalars().all()

        for apply_form in apply_forms:
            await self.session.delete(apply_form)
        await self.session.commit()
        return True

    async def delete_apply_form(self, apply_form_id: int) -> bool:
        """
        Deletes an application form.
        Args:
            apply_form_id (int): Form ID
        Returns:
            bool: True if deleted, False if not found
        """
        apply_form = await self.session.get(ApplicationForm, apply_form_id)
        if not apply_form:
            return False

        await self.session.delete(apply_form)
        await self.session.commit()
        return True
