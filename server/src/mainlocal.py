# Entrypoint
import logging
import sys
from local.local import LocalApp

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('jobfinder.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point of the application."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting JobFinder application")
        app = LocalApp()
        app.run()
        logger.info("Application terminated normally")
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        print("\nApplication terminated by user")
    except Exception as e:
        logger.critical(f"Fatal error occurred: {e}", exc_info=True)
        print(f"\nA fatal error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
