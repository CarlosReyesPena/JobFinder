import platform
from pathlib import Path
import logging
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
import asyncio

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database initialization, configuration and deletion."""

    _instance = None  # Singleton for unique instance
    _lock = asyncio.Lock()  # Remplacer threading.Lock par asyncio.Lock

    def __new__(cls, echo: bool = False):
        if cls._instance is None:
            instance = super(DatabaseManager, cls).__new__(cls)
            instance.echo = echo
            instance._initialized = False
            cls._instance = instance
        return cls._instance

    def __init__(self, echo: bool = False):
        if not self._initialized:
            self.echo = echo
            self.engine: AsyncEngine = None
            self._initialized = True
            self.session_factory: SessionFactory = None
            self.connection_pool: ConnectionPool = None
            # Initialize database engine
            asyncio.create_task(self.init_db())

    async def init_db(self):
        try:
            if self.engine is not None:
                return  # Engine is already initialized

            db_path = get_db_path()
            db_url = f"sqlite+aiosqlite:///{db_path}"

            # Simple SQLite configuration
            self.engine = create_async_engine(
                db_url,
                echo=self.echo,
                connect_args={"check_same_thread": False}
            )

            # Create tables only if they don't exist
            async with self.engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)

            # Initialize components
            self.session_factory = SessionFactory(self.engine)
            self.connection_pool = ConnectionPool(self.engine)
            await self.connection_pool.initialize()

        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            raise DatabaseInitializationError("Database initialization failed")

    async def delete_database(self):
        """Deletes the database."""
        try:
            async with self._lock: # Lock to prevent multiple instances from deleting the database
                if self.engine:
                    await self.engine.dispose()
                db_path = get_db_path()
                logger.info(f"Deleting database: {db_path}")
                if db_path.exists():
                    db_path.unlink(missing_ok=True)
                    logger.info("Database deleted.")
                    return True
                else:
                    logger.warning("No database found.")
                    return False
        except Exception as e:
            logger.error(f"Échec suppression BDD: {str(e)}")
            raise DatabaseError("Erreur lors de la suppression de la base")

    async def get_session(self) -> AsyncSession:
        """Secure asynchronous session context"""
        async with self._lock:
            if not self.engine:
                await self.init_db()
            return AsyncSession(self.engine, expire_on_commit=False)

    async def get_connection(self):
        """Asynchronous connection acquisition"""
        if not self.engine:
            await self.init_db()
        return await self.engine.connect()

    async def release_connection(self, conn):
        """Asynchronous connection release"""
        await conn.close()

    async def get_scoped_session(self):
        """Session with automatic transaction scope management"""
        if not self.engine:
            await self.init_db()
        session = AsyncSession(self.engine, expire_on_commit=False)
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()


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


# Simplified connection management class
class ConnectionPool:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def initialize(self):
        pass  # SQLite doesn't need pool initialization

    async def get_connection(self):
        return await self.engine.connect()

    async def release_connection(self, conn):
        await conn.close()


# Classe simplifiée pour la gestion des sessions
class SessionFactory:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_session(self) -> AsyncSession:
        return AsyncSession(self.engine, expire_on_commit=False)


class DatabaseError(Exception):
    """Base exception for database errors"""
    pass


class DatabaseInitializationError(DatabaseError):
    pass


class ConnectionPoolExhaustedError(DatabaseError):
    pass
