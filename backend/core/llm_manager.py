from typing import Optional
from pydantic import BaseModel
import logging
import os
import dotenv
from .baml_src.baml_client.async_client import b
from .baml_src.baml_client.types import CoverLetterBody, CoverLetterRecipient, JobOfferStructure
from .baml_src.baml_client import reset_baml_env_vars

# Load environment variables from .env file
dotenv.load_dotenv()

# Reset BAML environment variables with current environment
reset_baml_env_vars(dict(os.environ))

class LLMManager:
    """Central class for managing LLM API interactions using BAML"""

    def __init__(self):
        self._configure_logger()
        self._check_api_keys()

    def _configure_logger(self):
        """Configure logging system"""
        self.logger = logging.getLogger("LLMManager")
        self.logger.setLevel(logging.INFO)

    def _check_api_keys(self):
        """Check if necessary API keys are set in environment variables"""
        required_keys = ["GOOGLE_API_KEY", "OPENROUTER_API_KEY"]
        missing_keys = [key for key in required_keys if not os.environ.get(key)]

        if missing_keys:
            self.logger.warning(f"Missing API keys in environment: {', '.join(missing_keys)}")
            self.logger.info("Some LLM functionality may not work without these keys")
        else:
            self.logger.info("All required API keys found in environment")

    async def generate_cover_letter_body(
        self,
        user_profile: str,
        job_description: str,
        reference_letter: Optional[str] = None
    ) -> Optional[CoverLetterBody]:
        """
        Generate cover letter body using BAML
        Args:
            user_profile (str): User's CV/profile text
            job_description (str): Job description text
            reference_letter (Optional[str]): Reference letter for style matching
        Returns:
            Optional[CoverLetterBody]: Generated cover letter body or None if generation failed
        """
        try:
            self.logger.info("Generating cover letter body...")
            result = await b.GenerateCoverLetter(
                user_profile=user_profile,
                job_description=job_description,
                reference_letter=reference_letter
            )
            self.logger.info("Cover letter body generated successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error generating cover letter body: {e}")
            return None

    async def generate_recipient_info(
        self,
        job_description: str
    ) -> Optional[CoverLetterRecipient]:
        """
        Extract recipient information from job description
        Args:
            job_description (str): Job description text
        Returns:
            Optional[CoverLetterRecipient]: Extracted recipient information or None if extraction failed
        """
        try:
            self.logger.info("Extracting recipient information...")
            result = await b.GenerateCoverRecipient(job_description=job_description)
            self.logger.info("Recipient information extracted successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error extracting recipient information: {e}")
            return None

    async def extract_job_offer(
        self,
        webpage_text: str
    ) -> Optional[JobOfferStructure]:
        """
        Extract job offer structure from webpage text
        Args:
            webpage_text (str): Text content of the job offer webpage
        Returns:
            Optional[JobOfferStructure]: Extracted job offer structure or None if extraction failed
        """
        try:
            self.logger.info("Extracting job offer structure...")
            result = await b.ExtractJobOffer(webpage_text=webpage_text)
            self.logger.info("Job offer structure extracted successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error extracting job offer structure: {e}")
            return None

    async def regenerate_text(
        self,
        original_text: str,
        selected_text: str,
        user_feedback: str,
        user_profile: Optional[str] = None,
        job_description: Optional[str] = None
    ) -> Optional[str]:
        """
        Regenerate a portion of text based on user feedback
        Args:
            original_text (str): The full original text
            selected_text (str): The portion of text to regenerate
            user_feedback (str): User feedback for regeneration
            user_profile (Optional[str]): User profile for context
            job_description (Optional[str]): Job description for context
        Returns:
            Optional[str]: Regenerated text or None if regeneration failed
        """
        try:
            self.logger.info("Regenerating text based on user feedback...")

            # Prepare context
            context = {}
            if user_profile:
                context["user_profile"] = user_profile
            if job_description:
                context["job_description"] = job_description

            result = await b.RegenerateText(
                original_text=original_text,
                selected_text=selected_text,
                user_feedback=user_feedback,
                **context
            )

            self.logger.info("Text regenerated successfully")
            return result.content
        except Exception as e:
            self.logger.error(f"Error regenerating text: {e}")
            return None


class LLMResponse(BaseModel):
    """Base model for LLM responses"""
    content: str
    metadata: Optional[dict] = None