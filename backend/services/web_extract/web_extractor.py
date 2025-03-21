"""
Web extraction service for JobFinder application.
Uses Playwright to extract content from web pages and processes it to extract job offers.
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urlparse

from pydantic import BaseModel
from playwright.async_api import async_playwright

from backend.core.llm_manager import LLMManager
from backend.core.baml_src.baml_client.types import JobOfferStructure
from backend.data.managers import JobOfferManager
from backend.data.models import JobSite


class WebExtractionError(Exception):
    """Exception raised for errors in the web extraction process."""
    pass


class JobOfferExtractionResult(BaseModel):
    """Result of job offer extraction process"""
    url: str
    raw_text: str
    extracted_offer: Optional[JobOfferStructure] = None
    job_id: Optional[int] = None
    error: Optional[str] = None
    success: bool = True


class WebExtractor:
    """Service for extracting content from web pages and processing it to extract job offers."""

    def __init__(self):
        self._configure_logger()
        self.llm_manager = LLMManager()
        self.job_offer_manager = JobOfferManager()

    def _configure_logger(self):
        """Configure logging system"""
        self.logger = logging.getLogger("WebExtractor")
        self.logger.setLevel(logging.INFO)

    async def extract_page_content(self, url: str) -> str:
        """
        Extract text content from a web page using Playwright's async API

        Args:
            url (str): URL of the web page to extract content from

        Returns:
            str: Text content of the web page

        Raises:
            WebExtractionError: If there's an error during extraction
        """
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise WebExtractionError(f"Invalid URL: {url}")

        self.logger.info(f"Extracting content from {url}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
                )

                try:
                    context = await browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        locale="fr-FR"
                    )

                    page = await context.new_page()
                    await page.goto(url, wait_until="networkidle", timeout=60000)

                    # Extract text content
                    content = await page.evaluate("() => document.body.innerText")

                    self.logger.info(f"Successfully extracted content from {url}")
                    return content

                finally:
                    await browser.close()

        except Exception as e:
            error_msg = f"Error extracting content from {url}: {str(e)}"
            self.logger.error(error_msg)
            raise WebExtractionError(error_msg)

    async def extract_job_offer_from_url(self, url: str) -> JobOfferExtractionResult:
        """
        Extract job offer information from a URL

        Args:
            url (str): URL of the job offer page

        Returns:
            JobOfferExtractionResult: Result of the extraction process
        """
        result = JobOfferExtractionResult(url=url, raw_text="", success=False)

        try:
            # Extract page content
            raw_text = await self.extract_page_content(url)
            result.raw_text = raw_text

            # Extract job offer structure
            extracted_offer = await self.llm_manager.extract_job_offer(raw_text)

            if extracted_offer:
                result.extracted_offer = extracted_offer
                result.success = True
                self.logger.info(f"Successfully extracted job offer from {url}")
            else:
                result.error = "Failed to extract job offer structure"
                self.logger.warning(f"Failed to extract job offer structure from {url}")

        except WebExtractionError as e:
            result.error = str(e)
            self.logger.error(f"Web extraction error: {str(e)}")

        except Exception as e:
            result.error = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error during job offer extraction: {str(e)}")

        return result

    async def create_job_offer_in_db(self, url: str) -> Tuple[bool, str, Optional[int]]:
        """
        Extract job offer from URL and create it in the database

        Args:
            url (str): URL of the job offer page

        Returns:
            Tuple[bool, str, Optional[int]]: Success status, message, and job_id if successful
        """

        try:
            # Extract job offer
            result = await self.extract_job_offer_from_url(url)

            if not result.success or not result.extracted_offer:
                return False, result.error or "Failed to extract job offer", None

            # Check if job offer with this URL already exists
            existing_job = await self.job_offer_manager.get_job_offer_by_link(url)
            if existing_job:
                return True, f"Job offer already exists with ID {existing_job.id}", existing_job.id

            # Create job info dictionary from extracted offer
            job_info = result.extracted_offer.dict()

            # Determine if quick apply is available based on the job content
            quick_apply = self._detect_quick_apply(url, result.raw_text, job_info)

            # Determine job site from URL
            job_site = self._determine_job_site_from_url(url)

            # Create job offer in database
            job_offer = await self.job_offer_manager.add_job_offer(
                job_link=url,
                job_info=job_info,
                job_site=job_site,
                quick_apply=quick_apply
            )

            return True, f"Successfully created job offer with ID {job_offer.id}", job_offer.id

        except Exception as e:
            self.logger.error(f"Error creating job offer in database: {str(e)}")
            return False, f"Error creating job offer: {str(e)}", None

    def _detect_quick_apply(self, url: str, raw_text: str, job_info: Dict[str, Any]) -> bool:
        """
        Detect if an offer supports quick apply based on its content and source

        Args:
            url: URL of the job offer
            raw_text: Raw text content of the job page
            job_info: Extracted job information

        Returns:
            bool: True if quick apply is likely available
        """
        domain = urlparse(url).netloc.lower()

        # Common keywords that suggest quick apply availability
        quick_apply_keywords = [
            "quick apply", "apply now", "easy apply", "1-click apply",
            "postuler facilement", "postuler rapidement", "candidature simplifiée",
            "postuler en 1 clic", "postuler avec votre profil"
        ]

        # Check URL domain - some job sites are known to support quick apply
        if "linkedin.com" in domain and "/jobs/" in url:
            return True
        if "indeed.com" in domain and "apply" in raw_text.lower():
            return True
        if "jobup.ch" in domain and "postuler" in raw_text.lower():
            return True

        # Check for keywords in the text content
        lower_text = raw_text.lower()
        for keyword in quick_apply_keywords:
            if keyword in lower_text:
                return True

        # Check application instructions in job info
        if job_info.get("application_instructions"):
            instructions = job_info["application_instructions"].lower()
            if any(keyword in instructions for keyword in quick_apply_keywords):
                return True

        # Default to False if no evidence of quick apply
        return False

    def _determine_job_site_from_url(self, url: str) -> JobSite:
        """
        Determine the job site from the URL

        Args:
            url (str): URL of the job offer

        Returns:
            JobSite: Enum value representing the job site
        """
        domain = urlparse(url).netloc.lower()
        if "linkedin.com" in domain:
            return JobSite.LINKEDIN
        elif "indeed.com" in domain:
            return JobSite.INDEED
        elif "monster.com" in domain or "monster.fr" in domain:
            return JobSite.MONSTER
        elif "jobup.ch" in domain:
            return JobSite.JOBUP
        elif "glassdoor.com" in domain:
            return JobSite.GLASSDOOR
        else:
            # Check if it might be a company website
            if "jobs" in domain or "careers" in domain or "emploi" in domain or "carriere" in domain:
                return JobSite.COMPANY_WEBSITE
            return JobSite.OTHER

    async def extract_and_create_job_offers_batch(self, urls: List[str]) -> List[JobOfferExtractionResult]:
        """
        Extract job offers from multiple URLs and create them in the database

        Args:
            urls (List[str]): List of URLs to extract job offers from

        Returns:
            List[JobOfferExtractionResult]: Results of the extraction and creation processes
        """
        results = []

        for url in urls:
            try:
                success, message, job_id = await self.create_job_offer_in_db(url)

                # Get the extraction result with detailed information
                extraction_result = await self.extract_job_offer_from_url(url)

                # Update with job_id
                extraction_result.job_id = job_id

                if not success:
                    extraction_result.success = False
                    extraction_result.error = message

                results.append(extraction_result)

            except Exception as e:
                results.append(JobOfferExtractionResult(
                    url=url,
                    raw_text="",
                    error=f"Error: {str(e)}",
                    success=False
                ))

        return results


async def extract_and_create_job_offer(url: str) -> Dict[str, Any]:
    """
    Standalone function to extract job offer from a URL and create it in the database

    Args:
        url (str): URL of the job offer page

    Returns:
        Dict[str, Any]: Dictionary containing extraction results
    """
    extractor = WebExtractor()

    try:
        success, message, job_id = await extractor.create_job_offer_in_db(url)

        if success and job_id:
            job_offer = await extractor.job_offer_manager.get_job_offer_by_id(job_id)
            return {
                "success": True,
                "url": url,
                "job_id": job_id,
                "job_offer": job_offer.job_info,
                "message": message
            }
        else:
            return {
                "success": False,
                "url": url,
                "error": message,
                "message": message
            }
    except Exception as e:
        logging.error(f"Error extracting and creating job offer: {str(e)}")
        return {
            "success": False,
            "url": url,
            "error": f"Unexpected error: {str(e)}",
            "message": f"Unexpected error: {str(e)}"
        }