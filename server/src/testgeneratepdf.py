#!/usr/bin/env python3
import random
import logging
from pathlib import Path
from sqlmodel import Session, select
from data.database import DatabaseManager, get_app_data_dir
from data.managers.job_offer_manager import JobOfferManager
from data.managers.cover_letter_manager import CoverLetterManager
from services.generation.generator import CoverLetterGenerator
from services.generation.pdf_builder import PDFCoverLetterGenerator

# Configuration
NUM_LETTERS_TO_GENERATE = 3  # Number of letters to generate
USER_ID = 1  # User ID for whom to generate letters
EXPORT_IMMEDIATELY = True  # Automatically export PDFs after generation

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cover_letter_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_random_job_offers(session: Session, count: int) -> list:
    """Gets a specified number of random job offers."""
    job_manager = JobOfferManager(session)
    all_jobs = job_manager.get_job_offers()

    if not all_jobs:
        logger.error("No job offers found in database")
        return []

    return random.sample(all_jobs, min(count, len(all_jobs)))

def generate_and_export_letters(session: Session):
    """Generates and exports cover letters."""
    try:
        # Initialize managers
        generator = CoverLetterGenerator(session)
        cover_letter_manager = CoverLetterManager(session)
        pdf_builder = PDFCoverLetterGenerator(session)

        # Get random job offers
        job_offers = get_random_job_offers(session, NUM_LETTERS_TO_GENERATE)
        if not job_offers:
            return

        logger.info(f"Generating {len(job_offers)} cover letters...")

        # Generate letters
        for job in job_offers:
            try:
                logger.info(f"Generating letter for: {job.job_title} at {job.company_name}")

                # Generate letter
                cover_letter = generator.generate_cover_letter(
                    user_id=USER_ID,
                    job_id=job.id
                )

                if not cover_letter:
                    logger.error(f"Failed to generate letter for job {job.id}")
                    continue

                pdf_builder.generate_cover_letter_pdf(
                    user_id=USER_ID,
                    job_id=job.id
                )

                if not pdf_builder:
                    logger.error(f"Failed to generate PDF for job {job.id}")
                    continue
                if pdf_builder and cover_letter:
                    # Automatic export if configured
                    if EXPORT_IMMEDIATELY:
                        success, result = cover_letter_manager.extract_pdf_to_export(cover_letter.id)
                        if success:
                            logger.info(f"Letter exported successfully: {result}")
                        else:
                            logger.error(f"Export failed: {result}")

            except Exception as e:
                logger.error(f"Error while processing job {job.id}: {e}")
                continue

        # Display summary of exported files
        if EXPORT_IMMEDIATELY:
            exports_dir = get_app_data_dir() / "exports"
            logger.info("\nFiles generated in exports folder:")
            for file in exports_dir.glob("*.pdf"):
                logger.info(f"- {file.name}")

    except Exception as e:
        logger.error(f"General error: {e}")

def main():
    """Main entry point"""
    try:
        # Database initialization
        logger.info("Initializing database...")
        db = DatabaseManager()

        with db.get_session() as session:
            generate_and_export_letters(session)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()