from pydantic import BaseModel
from typing import List, Optional
from backend.data.managers import UserManager, JobOfferManager, DocumentManager
from backend.data.models import Document, DocumentType
from backend.core.llm_manager import LLMManager


class RecipientInfoResponse(BaseModel):
    company_name: Optional[str]
    recipient: str
    address: Optional[List[str]]

class CoverLetterResponse(BaseModel):
    subject: str
    greeting: str
    introduction: str
    skills_experience: str
    motivation: str
    conclusion: str
    closing: str

class CoverLetterGenerator:
    def __init__(self):
        self.user_manager = UserManager()
        self.job_offer_manager = JobOfferManager()
        self.document_manager = DocumentManager()
        self.llm_client = LLMManager()


    async def generate_cover_letter(self, user_id: int, job_id: int) -> Optional[Document]:
        """
        Generate a cover letter using a user ID and a job ID.

        Args:
            user_id (int): ID of the user
            job_id (int): ID of the job offer

        Returns:
            Optional[Document]: Generated cover letter or None if generation failed
        """
        user = await self.user_manager.get_user_by_id(user_id)
        job_offer = await self.job_offer_manager.get_job_offer_by_id(job_id)

        if not user or not job_offer:
            print("User or job offer missing.")
            return None

        return await self._generate_cover_letter_from_job_offer(user_id, job_offer)

    async def generate_cover_letter_by_link(self, user_id: int, job_link: str) -> Optional[Document]:
        """
        Generate a cover letter using a user ID and a job link.

        Args:
            user_id (int): ID of the user
            job_link (str): Link to the job offer

        Returns:
            Optional[Document]: Generated cover letter or None if generation failed
        """
        user = await self.user_manager.get_user_by_id(user_id)
        job_offer = await self.job_offer_manager.get_job_offer_by_link(job_link)

        if not user or not job_offer:
            print("User or job offer missing.")
            return None

        return await self._generate_cover_letter_from_job_offer(user_id, job_offer)

    async def _generate_cover_letter_from_job_offer(self, user_id: int, job_offer) -> Optional[Document]:
        """
        Internal method to generate a cover letter from a job offer object.

        Args:
            user_id (int): ID of the user
            job_offer: The job offer object

        Returns:
            Optional[Document]: Generated cover letter or None if generation failed
        """
        # Get job info from the job_info JSON field
        job_info = job_offer.job_info
        job_description = (
            f"Company name: {job_info.get('company_name', 'Unknown')}\n"
            f"Company information: {job_info.get('company_description', 'Not provided')}\n"
            f"Job title: {job_info.get('job_title', 'Not provided')}\n"
            f"Job description: {job_info.get('job_description', 'Not provided')}\n"
            f"Job location: {job_info.get('location', 'Not provided')}\n"
            f"Job type: {job_info.get('job_type', 'Not provided')}\n"
            f"Responsibilities: {job_info.get('responsibilities', 'Not provided')}\n"
            f"Requirements: {job_info.get('requirements', 'Not provided')}\n"
            f"Benefits: {job_info.get('benefits', 'Not provided')}\n"
            f"Contact information: {job_info.get('contact_info', 'Not provided')}"
        )

        # Get user CV from documents
        user_cv = await self.document_manager.get_last_document_by_type(
            user_id=user_id,
            document_type=DocumentType.CV
        )
        cv_text = ""
        if user_cv:
            # Use the text content of the most recent CV
            cv_text = user_cv.text_content or ""

        # Get reference letter if available
        reference_letters = await self.document_manager.get_user_documents(
            user_id=user_id,
            document_type=DocumentType.REFERENCE_LETTER
        )
        reference_letter_text = ""
        if reference_letters and len(reference_letters) > 0:
            reference_letter_text = reference_letters[0].text_content or ""

        # Generate recipient info using BAML
        recipient_info = await self.llm_client.generate_recipient_info(
            job_description=job_description
        )
        if not recipient_info:
            return None

        # Generate cover letter body using BAML
        cover_letter_body = await self.llm_client.generate_cover_letter_body(
            user_profile=cv_text,
            job_description=job_description,
            reference_letter=reference_letter_text
        )

        if not cover_letter_body:
            return None

        # Format recipient info
        recipient_info_str = self.format_recipient_info(recipient_info)

        # Save the cover letter
        return await self.save_cover_letter(
            user_id=user_id,
            job_id=job_offer.id,
            cover_letter_response=cover_letter_body,
            recipient_info=recipient_info_str
        )

    async def generate_cover_letter_from_string(self, user_id: int, job_offer_text: str) -> Optional[Document]:
        """
        Generate a cover letter using a user ID and a job offer text string

        Args:
            user_id (int): ID of the user
            job_offer_text (str): Raw text of the job offer

        Returns:
            Optional[Document]: Generated cover letter or None if generation failed
        """
        try:
            user = await self.user_manager.get_user_by_id(user_id)

            if not user:
                print("User not found.")
                return None

            # Get user CV from documents
            user_cv = await self.document_manager.get_user_documents(
                user_id=user_id,
                document_type=DocumentType.CV
            )
            cv_text = ""
            if user_cv and len(user_cv) > 0:
                # Use the text content of the most recent CV
                cv_text = user_cv[0].text_content or ""

            # Get reference letter if available
            reference_letters = await self.document_manager.get_user_documents(
                user_id=user_id,
                document_type=DocumentType.REFERENCE_LETTER
            )
            reference_letter_text = ""
            if reference_letters and len(reference_letters) > 0:
                reference_letter_text = reference_letters[0].text_content or ""

            # Generate recipient info using BAML
            recipient_info = await self.llm_client.generate_recipient_info(
                job_description=job_offer_text
            )
            if not recipient_info:
                return None

            # Generate cover letter body using BAML
            cover_letter_body = await self.llm_client.generate_cover_letter_body(
                user_profile=cv_text,
                job_description=job_offer_text,
                reference_letter=reference_letter_text
            )

            if not cover_letter_body:
                return None

            # Format recipient info
            recipient_info_str = self.format_recipient_info(recipient_info)

            # Save the cover letter without a job_id
            return await self.save_cover_letter(
                user_id=user_id,
                job_id=None,  # job_id is optional
                cover_letter_response=cover_letter_body,
                recipient_info=recipient_info_str
            )
        except Exception as e:
            print(f"Error in generate_cover_letter_from_string: {e}")
            return None

    def format_recipient_info(self, recipient_info) -> str:
        """
        Format the recipient information from a CoverLetterRecipient object into a multi-line string.

        Args:
            recipient_info: CoverLetterRecipient object containing recipient details

        Returns:
            str: Formatted recipient information as a multi-line string
        """
        lines = []

        # Add company name if available
        if recipient_info.company_name:
            lines.append(recipient_info.company_name)

        # Add either recipient_name or generic_greeting (only one will be present)
        if recipient_info.recipient_name:
            lines.append(recipient_info.recipient_name)
        elif recipient_info.generic_greeting:
            lines.append(recipient_info.generic_greeting)

        # Add address lines if available
        if recipient_info.address_lines:
            lines.extend(recipient_info.address_lines)

        return "\n".join(filter(None, lines))

    async def save_cover_letter(self, user_id: int, cover_letter_response,
                              recipient_info: str = "", job_id: Optional[int] = None) -> Optional[Document]:
        """
        Save a cover letter to the database using the unified Document model

        Args:
            user_id (int): ID of the user
            cover_letter_response: Cover letter response object
            recipient_info (str): Formatted recipient information
            job_id (Optional[int]): ID of the job offer (can be None for text-based generation)

        Returns:
            Optional[Document]: The saved cover letter document or None if save failed
        """
        try:
            # Create a JSON content structure for the cover letter
            cover_letter_content = {
                "subject": cover_letter_response.subject,
                "greeting": cover_letter_response.greeting,
                "introduction": cover_letter_response.introduction,
                "skills_experience": cover_letter_response.skills_experience,
                "motivation": cover_letter_response.motivation,
                "conclusion": cover_letter_response.conclusion,
                "closing": cover_letter_response.closing,
                "recipient_info": recipient_info
            }

            # Use document_manager to create a cover letter document
            if job_id:
                # If job_id is provided, use the cover_letter_for_job method
                return await self.document_manager.create_cover_letter_for_job(
                    user_id=user_id,
                    job_id=job_id,
                    name="Cover Letter",
                    content=cover_letter_content,
                    metadata={"generated": True, "version": "1.0"}
                )
            else:
                # Otherwise create a standalone cover letter
                return await self.document_manager.create_document(
                    user_id=user_id,
                    document_type=DocumentType.COVER_LETTER,
                    name="Cover Letter",
                    json_content=cover_letter_content,
                    metadata={"generated": True, "version": "1.0"}
                )
        except Exception as e:
            print(f"Error in save_cover_letter: {e}")
            return None