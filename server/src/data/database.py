import platform
from pathlib import Path
import logging
from sqlmodel import Session, create_engine, SQLModel
from threading import Lock

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database initialization, configuration and deletion."""

    _instance = None  # Singleton for unique instance
    _lock = Lock()  # Global lock for concurrent engine access

    def __new__(cls, echo: bool = False):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, echo: bool = False):
        if not self._initialized:
            self.echo = echo
            self.engine = self.init_db()
            self._initialized = True

    def init_db(self):
        """Initializes the database and returns the engine"""
        try:
            db_path = get_db_path()
            db_url = f"sqlite:///{db_path}"

            logger.info(f"Database path: {db_path}")

            if db_path.exists():
                logger.info(f"Existing database found: {db_url}")
                return create_engine(db_url, echo=self.echo)

            logger.info("Creating new database...")

            engine = create_engine(db_url, echo=self.echo)
            SQLModel.metadata.create_all(engine)
            logger.info(f"New database initialized: {db_url}")
            return engine

        except Exception as e:
            logger.error(f"DB initialization error: {e}")
            raise

    def delete_database(self):
        """Deletes the database."""
        try:
            with self._lock:
                if hasattr(self, 'engine'):
                    self.engine.dispose()
                db_path = get_db_path()
                logger.info(f"Deleting database: {db_path}")
                if db_path.exists():
                    db_path.unlink()
                    logger.info("Database deleted.")
                    return True
                else:
                    logger.warning("No database found.")
                    return False
        except Exception as e:
            logger.error(f"Error while deleting database: {e}")
            return False

    def get_session(self):
        """Returns a secure session with locking."""
        with self._lock:
            logger.info("Creating new session with lock.")
            return Session(self.engine)

def get_app_data_dir() -> Path:
    system = platform.system()
    home = Path.home()

    if system == "Windows":
        return home / "AppData" / "Local" / "JobFinder"
    elif system == "Darwin":  # macOS
        return home / "Library" / "Application Support" / "JobFinder"
    else:  # Linux and others
        return home / ".local" / "share" / "jobfinder"


def get_db_path() -> Path:
    app_data = get_app_data_dir()
    for subdir in ["data", "temp", "exports", "cache"]:
        (app_data / subdir).mkdir(parents=True, exist_ok=True)
    db_dir = app_data / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "job_application.db"

