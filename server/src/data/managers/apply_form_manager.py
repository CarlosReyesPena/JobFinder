from typing import Optional, List
from sqlmodel import Session, select
from ..models.apply_form import ApplicationForm


class ApplyFormManager:
    def __init__(self, session: Session):
        self.session = session

    def add_apply_form(self, user_id: int, site_name: str, form_data: dict) -> ApplicationForm:
        """
        Adds a new application form.
        """
        apply_form = ApplicationForm(user_id=user_id, site_name=site_name, form_data=form_data)
        self.session.add(apply_form)
        self.session.commit()
        return apply_form

    def get_apply_form_by_user_and_site(self, user_id: int, site_name: str) -> Optional[ApplicationForm]:
        """
        Retrieves an application form for a specific user and site.
        """
        statement = select(ApplicationForm).where(ApplicationForm.user_id == user_id, ApplicationForm.site_name == site_name)
        return self.session.exec(statement).first()

    def get_last_apply_form_by_user(self, user_id: int) -> Optional[ApplicationForm]:
        """
        Retrieves the last application form for a specific user.
        """
        statement = select(ApplicationForm).where(ApplicationForm.user_id == user_id).order_by(ApplicationForm.id.desc())
        return self.session.exec(statement).first()

    def get_apply_forms_by_user(self, user_id: int) -> List[ApplicationForm]:
        """
        Retrieves all application forms for a specific user.
        """
        return self.session.exec(select(ApplicationForm).where(ApplicationForm.user_id == user_id)).all()

    def delete_all_apply_forms(self) -> bool:
        """
        Deletes all application forms.
        """
        apply_forms = self.session.exec(select(ApplicationForm)).all()
        for apply_form in apply_forms:
            self.session.delete(apply_form)
        self.session.commit()
        return True

    def delete_apply_form(self, apply_form_id: int) -> bool:
        """
        Deletes an application form.
        """
        apply_form = self.session.get(ApplicationForm, apply_form_id)
        if not apply_form:
            return False
        self.session.delete(apply_form)
        self.session.commit()
        return True
