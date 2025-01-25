from sqlmodel import create_engine, Session
from data.database import DatabaseManager, get_app_data_dir
from data.managers.cover_letter_manager import CoverLetterManager
import logging
import sys
from pathlib import Path

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extract_cover_letter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        # Database initialization
        logger.info("Initializing database connection...")
        db = DatabaseManager()
        session = db.get_session()

        # Cover letter manager initialization
        cover_letter_manager = CoverLetterManager(session)

        # Ask for letter ID to extract
        cover_letter_id = int(input("Enter the ID of the cover letter to extract: "))

        # PDF extraction
        logger.info(f"Attempting to extract letter ID {cover_letter_id}...")
        success, result = cover_letter_manager.extract_pdf_to_export(cover_letter_id)

        if success:
            logger.info(f"Cover letter successfully extracted to: {result}")
            print(f"\nPDF has been successfully extracted to: {result}")

            # Display exports folder path
            exports_dir = get_app_data_dir() / "exports"
            print(f"\nExports folder: {exports_dir}")

            # List all files in exports folder
            print("\nFiles in exports folder:")
            for file in exports_dir.glob("*.pdf"):
                print(f"- {file.name}")
        else:
            logger.error(f"Extraction failed: {result}")
            print(f"\nError during extraction: {result}")

    except ValueError as ve:
        logger.error(f"Format error: {ve}")
        print("\nError: Please enter a valid number for the ID")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        if 'session' in locals():
            session.close()
            logger.info("Database session closed")

if __name__ == "__main__":
    main()