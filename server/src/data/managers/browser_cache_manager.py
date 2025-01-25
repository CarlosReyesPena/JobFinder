import shutil
from datetime import datetime
from typing import Optional, Tuple
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from sqlmodel import Session, select
from pathlib import Path
import tempfile
import logging
from ..models.browser_cache import BrowserCache
from ..database import get_app_data_dir

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserCacheManager:
    def __init__(self, session: Session):
        """Initialize the manager with a database session."""
        self.session = session
        self.app_cache_dir = get_app_data_dir() / "cache"
        self.app_cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_cache_dir(self, user_id: int) -> Path:
        """Returns the cache directory path for a user."""
        return self.app_cache_dir / f"user_{user_id}"

    def _create_temp_dir(self) -> Path:
        """Creates a temporary directory for cache operations."""
        temp_dir = Path(tempfile.mkdtemp(prefix="jobfinder_cache_"))
        return temp_dir

    def _compress_directory(self, directory_path: Path) -> Optional[bytes]:
        """Compresses a directory in memory."""
        if not directory_path.exists():
            logger.error(f"Directory {directory_path} does not exist")
            return None

        try:
            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, 'w', compression=ZIP_DEFLATED, compresslevel=9) as zip_file:
                for file_path in directory_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(directory_path)
                        zip_file.write(file_path, arcname)
            return zip_buffer.getvalue()
        except Exception as e:
            logger.error(f"Error during compression: {e}")
            return None

    def save_cache_directory(self, user_id: int, cache_dir_path: str) -> Optional[BrowserCache]:
        """Saves a user's cache."""
        try:
            cache_path = Path(cache_dir_path)
            if not cache_path.exists():
                logger.error(f"Cache directory not found: {cache_path}")
                return None

            # Cache compression
            zip_data = self._compress_directory(cache_path)
            if not zip_data:
                return None

            # Update or create cache
            cache_record = self.session.exec(
                select(BrowserCache).where(BrowserCache.user_id == user_id)
            ).first()

            if cache_record:
                cache_record.cache_data = zip_data
                cache_record.last_updated = datetime.now().isoformat()
            else:
                cache_record = BrowserCache(
                    user_id=user_id,
                    cache_data=zip_data,
                    last_updated=datetime.now().isoformat()
                )

            self.session.add(cache_record)
            self.session.commit()

            logger.info(f"Cache saved for user {user_id}")
            return cache_record

        except Exception as e:
            logger.error(f"Error while saving cache: {e}")
            return None

    def extract_cache_directory(self, user_id: int, target_dir: str) -> bool:
        """Extracts the cache to a target directory."""
        try:
            # Retrieve cache
            cache_record = self.session.exec(
                select(BrowserCache).where(BrowserCache.user_id == user_id)
            ).first()

            if not cache_record:
                logger.warning(f"No cache found for user {user_id}")
                return False

            target_path = Path(target_dir)
            target_path.mkdir(parents=True, exist_ok=True)

            # Extract to temporary directory first
            temp_dir = self._create_temp_dir()
            try:
                with BytesIO(cache_record.cache_data) as zip_buffer:
                    with ZipFile(zip_buffer, 'r') as zip_file:
                        zip_file.extractall(temp_dir)

                # Copy to target directory
                for item in temp_dir.iterdir():
                    if item.is_file():
                        shutil.copy2(item, target_path)
                    else:
                        shutil.copytree(item, target_path / item.name, dirs_exist_ok=True)

                logger.info(f"Cache successfully extracted for user {user_id}")
                return True

            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"Error while extracting cache: {e}")
            return False

    def save_and_clear_cache(self, user_id: int, cache_dir_path: str) -> Tuple[bool, bool]:
        """Saves and cleans the cache."""
        try:
            save_success = bool(self.save_cache_directory(user_id, cache_dir_path))
            if not save_success:
                return False, False

            # Clean source cache
            cache_path = Path(cache_dir_path)
            if cache_path.exists():
                shutil.rmtree(cache_path, ignore_errors=True)
                clear_success = not cache_path.exists()
                if clear_success:
                    logger.info(f"Cache cleaned for user {user_id}")
                return save_success, clear_success

            return save_success, True

        except Exception as e:
            logger.error(f"Error while saving and cleaning cache: {e}")
            return False, False

    def get_cache_last_updated(self, user_id: int) -> Optional[str]:
        """Gets the cache's last update date."""
        cache_record = self.session.exec(
            select(BrowserCache).where(BrowserCache.user_id == user_id)
        ).first()

        if cache_record:
            return cache_record.last_updated
        logger.warning(f"No cache history for user {user_id}")
        return None