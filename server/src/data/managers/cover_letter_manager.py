from typing import Optional, List
from sqlmodel import Session, select
from ..models.cover_letter import CoverLetter
from ..database import get_app_data_dir


class CoverLetterManager:
    def __init__(self, session: Session):
        self.session = session

    def add_cover_letter(self, **kwargs) -> CoverLetter:
        """
        Adds a new cover letter.
        Args:
            kwargs (dict): Cover letter data.
        Returns:
            CoverLetter: The created cover letter.
        """
        required_fields = [
            "user_id", "job_id", "subject", "greeting", "introduction",
            "skills_experience", "motivation", "conclusion", "closing"
        ]
        for field in required_fields:
            if not kwargs.get(field):
                raise ValueError(f"The field {field} is required.")

        cover_letter = CoverLetter(**kwargs)
        self.session.add(cover_letter)
        self.session.commit()
        return cover_letter

    def add_pdf_to_cover_letter(self, cover_letter_id: int, pdf_data: bytes) -> Optional[CoverLetter]:
        """
        Adds a PDF to an existing cover letter.
        Args:
            cover_letter_id (int): ID of the letter.
            pdf_data (bytes): PDF file data.
        Returns:
            Optional[CoverLetter]: The updated letter or None if not found.
        """
        cover_letter = self.session.get(CoverLetter, cover_letter_id)
        if not cover_letter:
            raise ValueError(f"Cover letter with ID {cover_letter_id} not found.")
        cover_letter.pdf_data = pdf_data
        self.session.add(cover_letter)
        self.session.commit()
        return cover_letter

    def get_cover_letters(self) -> List[CoverLetter]:
        """
        Retrieves all cover letters.
        Returns:
            List[CoverLetter]: List of letters.
        """
        return self.session.exec(select(CoverLetter)).all()

    def get_cover_letter_by_id(self, cover_letter_id: int) -> Optional[CoverLetter]:
        """
        Retrieves a cover letter by its ID.
        Args:
            cover_letter_id (int): ID of the letter.
        Returns:
            Optional[CoverLetter]: The found letter or None.
        """
        return self.session.get(CoverLetter, cover_letter_id)


    def get_cover_letter_by_user_and_job_id(self, user_id: int, job_id: int, number: int = 1) -> Optional[CoverLetter]:
        """
        Retrieves a cover letter by user and job offer.
        Args:
            user_id (int): User ID.
            job_id (int): Job ID.
            number (int): Letter to retrieve (1 for first, 2 for second, etc.).
        Returns:
            Optional[CoverLetter]: The found letter or None.
        """
        statement = select(CoverLetter).where(CoverLetter.user_id == user_id, CoverLetter.job_id == job_id)
        results = self.session.exec(statement).all()
        if len(results) >= number:
            return results[number - 1]
        return None

    def delete_cover_letter(self, cover_letter_id: int) -> bool:
        """
        Deletes a cover letter.
        Args:
            cover_letter_id (int): ID of the letter.
        Returns:
            bool: True if the letter was deleted, False otherwise.
        """
        cover_letter = self.session.get(CoverLetter, cover_letter_id)
        if not cover_letter:
            return False
        self.session.delete(cover_letter)
        self.session.commit()
        return True

    def delete_all_cover_letters(self) -> bool:
        """
        Deletes all cover letters.
        Returns:
            bool: True if all letters were deleted, False otherwise.
        """
        cover_letters = self.get_cover_letters()
        for cover_letter in cover_letters:
            self.session.delete(cover_letter)
        self.session.commit()
        return True

    def extract_pdf_to_export(self, cover_letter_id: int) -> tuple[bool, str]:
        """
        Extracts the PDF stored in the database to the export folder.
        Args:
            cover_letter_id (int): Cover letter ID
        Returns:
            tuple[bool, str]: (success, file path or error message)
        """
        cover_letter = self.get_cover_letter_by_id(cover_letter_id)
        if not cover_letter or not cover_letter.pdf_data:
            return False, "PDF not found"

        try:
            exports_dir = get_app_data_dir() / "exports"

            if not exports_dir.exists():
                exports_dir.mkdir(parents=True)
            # Create unique filename with timestamp
            filename = f"cover_letter_{cover_letter_id}.pdf"
            file_path = exports_dir / filename

            # Write PDF
            file_path.write_bytes(cover_letter.pdf_data)

            return True, str(file_path)

        except Exception as e:
            return False, f"Error while extracting PDF: {e}"