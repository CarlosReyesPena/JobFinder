import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import List, Optional
from sqlmodel import Session
from data.managers.job_offer_manager import JobOfferManager
from data.managers.cover_letter_manager import CoverLetterManager
from data.managers.application_manager import ApplicationManager
from services.generation.generator import CoverLetterGenerator
from services.generation.pdf_builder import PDFCoverLetterGenerator
from services.job_automation.jobup.form_filler import FormFiller
from data.models.job_offer import JobOffer

class AutoApply:
    def __init__(self, session: Session, user_id: int, max_workers: int = 5):
        """
        Initialize AutoApply with database session and configuration.

        Args:
            session (Session): Database session
            user_id (int): User ID for job applications
            max_workers (int): Maximum number of concurrent threads
        """
        self.session = session
        self.user_id = user_id
        self.max_workers = max_workers
        self.job_offer_manager = JobOfferManager(session)
        self.cover_letter_manager = CoverLetterManager(session)
        self.pdf_cover_builder = PDFCoverLetterGenerator(session)
        self.application_manager = ApplicationManager(session)
        self.cover_letter_generator = CoverLetterGenerator(session)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Thread synchronization
        self.applications_processed = 0
        self.applications_lock = Lock()

    def process_single_job(self, job_offer: JobOffer) -> bool:
        """
        Process a single job offer in a thread.

        Args:
            job_offer (JobOffer): Job offer to process

        Returns:
            bool: True if application was successful, False otherwise
        """
        try:
            # Check if application already exists
            existing_application = self.application_manager.get_application_by_user_and_job(
                user_id=self.user_id,
                job_id=job_offer.id
            )

            if existing_application:
                self.logger.info(f"Skipping job {job_offer.job_title} - already applied")
                return False

            # Step 1: Generate Cover Letter
            self.logger.info(f"Generating cover letter for: {job_offer.job_title}")
            cover_letter = self.cover_letter_generator.generate_cover_letter(
                user_id=self.user_id,
                job_id=job_offer.id
            )

            if not cover_letter:
                self.logger.warning(f"Cover letter generation failed for {job_offer.job_title}")
                return False

            # Step 2: Generate PDF
            self.logger.info(f"Generating PDF for: {job_offer.job_title}")
            pdf_success = self.pdf_cover_builder.generate_cover_letter_pdf(
                user_id=self.user_id,
                job_id=job_offer.id
            )

            if not pdf_success:
                self.logger.warning(f"PDF generation failed for {job_offer.job_title}")
                return False

            # Step 3: Fill and Submit Form
            self.logger.info(f"Filling form for: {job_offer.job_title}")
            form_filler = FormFiller(self.session, self.user_id)
            form_filler.fill_form_from_apply_form(job_offer.external_id)

            # Step 4: Update Application Status
            with self.applications_lock:
                self.application_manager.add_application(
                    user_id=self.user_id,
                    job_id=job_offer.id,
                    application_status="Submitted"
                )
                self.applications_processed += 1

            self.logger.info(f"Successfully applied to: {job_offer.job_title}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing {job_offer.job_title}: {str(e)}")
            return False

    def process_job_offers(self, max_applications: Optional[int] = None) -> int:
        """
        Process multiple job offers concurrently using a thread pool.

        Args:
            max_applications (int, optional): Maximum number of applications to process

        Returns:
            int: Number of successful applications
        """
        job_offers = self.job_offer_manager.get_job_offers_by_quick_apply()
        if not job_offers:
            self.logger.info("No job offers found to process")
            return 0

        if max_applications:
            job_offers = job_offers[:max_applications]

        successful_applications = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs to the executor
            future_to_job = {
                executor.submit(self.process_single_job, job_offer): job_offer
                for job_offer in job_offers
            }

            # Process completed futures as they finish
            for future in as_completed(future_to_job):
                job_offer = future_to_job[future]
                try:
                    if future.result():
                        successful_applications += 1
                        self.logger.info(
                            f"Application {successful_applications} completed: "
                            f"{job_offer.job_title} at {job_offer.company_name}"
                        )
                except Exception as e:
                    self.logger.error(
                        f"Application failed for {job_offer.job_title}: {str(e)}"
                    )

        return successful_applications

if __name__ == "__main__":
    import sys
    from data.database import DatabaseManager

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(threadName)s - %(message)s'
    )
    logger = logging.getLogger("AutoApply")

    try:
        if len(sys.argv) < 3:
            print("Usage: python threaded_auto_apply.py <user_id> <max_workers> [max_applications]")
            sys.exit(1)

        user_id = int(sys.argv[1])
        max_workers = int(sys.argv[2])
        max_applications = int(sys.argv[3]) if len(sys.argv) > 3 else None

        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            auto_apply = AutoApply(
                session=session,
                user_id=user_id,
                max_workers=max_workers
            )
            successful = auto_apply.process_job_offers(max_applications)
            logger.info(f"Completed with {successful} successful applications")

    except (IndexError, ValueError) as e:
        logger.error(f"Invalid arguments: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")