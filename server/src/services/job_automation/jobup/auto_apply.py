import logging
from sqlmodel import Session
from data.managers.job_offer_manager import JobOfferManager
from data.managers.cover_letter_manager import CoverLetterManager
from data.managers.application_manager import ApplicationManager
from services.generation.generator import CoverLetterGenerator
from services.generation.pdf_builder import PDFCoverLetterGenerator
from services.job_automation.jobup.form_filler import FormFiller

class AutoApply:
    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id
        self.job_offer_manager = JobOfferManager(session)
        self.cover_letter_manager = CoverLetterManager(session)
        self.pdf_cover_builder = PDFCoverLetterGenerator(session)
        self.application_manager = ApplicationManager(session)
        self.cover_letter_generator = CoverLetterGenerator(session)
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_job_offers(self, max_applications: int = None):
        """
        Process job offers: create cover letter, fill the form, apply, and update the database.

        Args:
            max_applications (int, optional): Maximum number of applications to process. Defaults to None (process all offers).
        """
        job_offers = self.job_offer_manager.get_job_offers_by_quick_apply()
        applications_processed = 0

        for job_offer in job_offers:
            if max_applications and applications_processed >= max_applications:
                self.logger.info(f"Reached the maximum limit of {max_applications} applications.")
                break

            # Check if an application already exists for this user and job offer
            existing_application = self.application_manager.get_application_by_user_and_job(
                user_id=self.user_id, job_id=job_offer.id
            )

            if existing_application:
                self.logger.info(f"Skipping job {job_offer.job_title} at {job_offer.company_name} as it is already applied.")
                continue

            try:
                # Step 1: Generate Cover Letter
                self.logger.info(f"Generating cover letter for job: {job_offer.job_title} at {job_offer.company_name}")
                cover_letter = self.cover_letter_generator.generate_cover_letter(
                    user_id=self.user_id,
                    job_id=job_offer.id
                )

                if not cover_letter:
                    self.logger.warning(f"Skipping job {job_offer.job_title} due to cover letter generation failure.")
                    continue

                # Step 2: generate pdf cover
                self.logger.info(f"Generating PDF cover letter for job: {job_offer.job_title} at {job_offer.company_name}")
                pdf_cover = self.pdf_cover_builder.generate_cover_letter_pdf(user_id=self.user_id, job_id=job_offer.id)

                if not pdf_cover:
                    self.logger.warning(f"Skipping job {job_offer.job_title} due to PDF cover letter generation failure.")
                    continue
                # Step 3: Fill and Submit the Application Form
                self.logger.info(f"Filling application form for job: {job_offer.job_title} at {job_offer.company_name}")
                form_filler = FormFiller(self.session, self.user_id)
                form_filler.fill_apply_form(job_offer.external_id)

                # Step 4: Update the Application Status in the Database
                self.logger.info(f"Updating application status for job: {job_offer.job_title} at {job_offer.company_name}")
                self.application_manager.add_application(
                    user_id=self.user_id,
                    job_id=job_offer.id,
                    application_status="Submitted"
                )

                applications_processed += 1
                self.logger.info(f"Successfully applied for job: {job_offer.job_title} at {job_offer.company_name}")

            except Exception as e:
                self.logger.error(f"Error processing job {job_offer.job_title} at {job_offer.company_name}: {e}")

if __name__ == "__main__":
    import sys
    from data.database import DatabaseManager

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("AutoApply")

    try:
        user_id = int(sys.argv[1])
        max_applications = int(sys.argv[2]) if len(sys.argv) > 2 else None

        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            auto_apply = AutoApply(session, user_id)
            auto_apply.process_job_offers(max_applications=max_applications)

    except IndexError:
        logger.error("Please provide a user ID as the first argument.")
    except ValueError:
        logger.error("Invalid argument. Please provide a valid user ID and optionally a maximum number of applications.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
