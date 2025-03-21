import logging
import asyncio
import platform
from pathlib import Path
import contextlib
from typing import Optional, AsyncGenerator, Dict
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy import text

# Configuration of logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =====================
# Exceptions
# =====================
class DatabaseError(Exception):
    """Base exception for database errors"""
    pass


class DatabaseInitializationError(DatabaseError):
    """Raised when database initialization fails"""
    pass


class ConnectionPoolExhaustedError(DatabaseError):
    """Raised when the connection pool is exhausted"""
    pass


class SessionLockTimeoutError(DatabaseError):
    """Raised when session lock acquisition times out"""
    pass


# =====================
# Read-Write Lock Implementation
# =====================
class AsyncRWLock:
    """
    Asynchronous Read-Write Lock implementation.

    Allows:
    - Multiple readers to access the resource simultaneously
    - Only one writer to access the resource at a time
    - No readers can access the resource when a writer has the lock
    """

    def __init__(self):
        self._read_ready = asyncio.Event()
        self._read_ready.set()
        self._write_ready = asyncio.Event()
        self._write_ready.set()
        self._reader_count = 0
        self._writer_count = 0
        self._write_waiting = 0
        self._read_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()

    async def acquire_read(self, timeout: Optional[float] = None):
        """
        Acquire a read lock. Multiple readers can hold the lock simultaneously.

        Args:
            timeout: Maximum time to wait for the lock in seconds

        Returns:
            bool: True if the lock was acquired, False otherwise

        Raises:
            SessionLockTimeoutError: If lock acquisition times out
        """
        try:
            # First check if a writer is active or waiting
            if timeout is not None:
                if not await asyncio.wait_for(self._write_ready.wait(), timeout):
                    raise SessionLockTimeoutError(f"Read lock acquisition timed out after {timeout} seconds")
            else:
                await self._write_ready.wait()

            # Now acquire the read lock to increment the reader count
            if timeout is not None:
                if not await asyncio.wait_for(self._read_lock.acquire(), timeout):
                    raise SessionLockTimeoutError(f"Read lock counter acquisition timed out after {timeout} seconds")
            else:
                await self._read_lock.acquire()

            try:
                self._reader_count += 1
                if self._reader_count == 1:
                    # First reader will clear the read_ready flag for writers
                    self._read_ready.clear()
            finally:
                self._read_lock.release()

            return True

        except asyncio.TimeoutError:
            raise SessionLockTimeoutError(f"Read lock acquisition timed out after {timeout} seconds")

    def release_read(self):
        """Release a read lock."""
        asyncio.create_task(self._release_read())

    async def _release_read(self):
        """Internal method to release a read lock."""
        async with self._read_lock:
            self._reader_count -= 1
            if self._reader_count == 0:
                # Last reader will set the read_ready flag for writers
                self._read_ready.set()

    async def acquire_write(self, timeout: Optional[float] = None):
        """
        Acquire a write lock. Only one writer can hold the lock at a time.

        Args:
            timeout: Maximum time to wait for the lock in seconds

        Returns:
            bool: True if the lock was acquired, False otherwise

        Raises:
            SessionLockTimeoutError: If lock acquisition times out
        """
        try:
            # First acquire the write lock to increment the waiting count
            if timeout is not None:
                if not await asyncio.wait_for(self._write_lock.acquire(), timeout):
                    raise SessionLockTimeoutError(f"Write lock counter acquisition timed out after {timeout} seconds")
            else:
                await self._write_lock.acquire()

            self._write_waiting += 1

            if self._write_waiting == 1:
                # First waiting writer will clear the write_ready flag
                self._write_ready.clear()

            self._write_lock.release()

            # Now wait for both read and write to be ready
            remaining_timeout = timeout
            start_time = asyncio.get_event_loop().time() if timeout is not None else None

            # Wait for read lock to be available
            if timeout is not None:
                if not await asyncio.wait_for(self._read_ready.wait(), remaining_timeout):
                    async with self._write_lock:
                        self._write_waiting -= 1
                        if self._write_waiting == 0:
                            self._write_ready.set()
                    raise SessionLockTimeoutError(f"Write lock acquisition timed out waiting for readers after {timeout} seconds")
            else:
                await self._read_ready.wait()

            # Update remaining timeout
            if timeout is not None:
                elapsed = asyncio.get_event_loop().time() - start_time
                remaining_timeout = max(0.0, timeout - elapsed)

            # Wait for other writers to finish
            if timeout is not None:
                if not await asyncio.wait_for(self._write_lock.acquire(), remaining_timeout):
                    raise SessionLockTimeoutError(f"Write lock acquisition timed out waiting for other writers after {timeout} seconds")
            else:
                await self._write_lock.acquire()

            # Veiller à ce que tous les lecteurs aient terminé
            # C'est crucial pour éviter des problèmes de concurrence
            if self._reader_count > 0:
                # Attendre que tous les lecteurs aient terminé
                await asyncio.sleep(0.1)  # Délai pour s'assurer que les lecteurs terminent

            self._write_waiting -= 1
            self._writer_count += 1

            return True

        except asyncio.TimeoutError:
            async with self._write_lock:
                self._write_waiting -= 1
                if self._write_waiting == 0:
                    self._write_ready.set()
            raise SessionLockTimeoutError(f"Write lock acquisition timed out after {timeout} seconds")

    def release_write(self):
        """Release a write lock."""
        self._writer_count -= 1
        self._write_lock.release()

        if self._write_waiting == 0:
            self._write_ready.set()


# =====================
# Utility Functions
# =====================
def get_app_data_dir() -> Path:
    """Get the application data directory based on the operating system."""
    system = platform.system()
    home = Path.home()

    if system == "Windows":
        return home / "AppData" / "Local" / "JobFinder"
    elif system == "Darwin":  # macOS
        return home / "Library" / "Application Support" / "JobFinder"
    else:  # Linux and others
        return home / ".local" / "share" / "jobfinder"


def get_db_path() -> Path:
    """Get the database file path and ensure directories exist."""
    app_data = get_app_data_dir()
    for subdir in ["data", "temp", "exports", "cache"]:
        (app_data / subdir).mkdir(parents=True, exist_ok=True)
    db_dir = app_data / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "job_application.db"


# =====================
# Database Management Classes
# =====================
class ConnectionPool:
    """Manages database connections."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def initialize(self):
        """Initialize the connection pool."""
        pass  # SQLite doesn't need pool initialization

    async def get_connection(self):
        """Get a connection from the pool."""
        return await self.engine.connect()

    async def release_connection(self, conn):
        """Release a connection back to the pool."""
        await conn.close()


class SessionFactory:
    """Factory for creating database sessions."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_session(self) -> AsyncSession:
        """Create a new session."""
        return AsyncSession(self.engine, expire_on_commit=False)


class DatabaseManager:
    """Manages database initialization, configuration and deletion."""

    _instance = None
    _lock = asyncio.Lock()
    _rwlock = None  # Will be initialized in __init__
    _shared_session: Optional[AsyncSession] = None
    _active_sessions: Dict[int, AsyncSession] = {}  # Track active sessions
    _session_counter = 0

    def __init__(self, echo: bool = False):
        self.echo = echo
        self.engine: AsyncEngine = None
        self.session_factory: SessionFactory = None
        self.connection_pool: ConnectionPool = None
        self._rwlock = AsyncRWLock()

    @classmethod
    async def get_instance(cls, echo: bool = False) -> 'DatabaseManager':
        """Get the singleton instance of DatabaseManager."""
        async with cls._lock:
            if not cls._instance:
                cls._instance = cls(echo)
                await cls._instance.init_db()
            return cls._instance

    async def init_db(self):
        """Initialize the database engine and create tables."""
        try:
            if self.engine is not None:
                return

            db_path = get_db_path()
            db_url = f"sqlite+aiosqlite:///{db_path}"

            self.engine = create_async_engine(
                db_url,
                echo=self.echo,
                connect_args={"check_same_thread": False}
            )

            try:
                # Create tables with checkfirst=True to avoid errors if they already exist
                async with self.engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)
                
                # Create indexes for applications table
                await self._create_indexes_if_not_exist()
                
            except Exception as e:
                # Log the error but continue if it's just about existing indexes
                if "already exists" in str(e):
                    logger.warning(f"Some indexes already exist: {str(e)}")
                else:
                    # Re-raise if it's a more serious error
                    raise

            self.session_factory = SessionFactory(self.engine)
            self.connection_pool = ConnectionPool(self.engine)
            await self.connection_pool.initialize()

        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            raise DatabaseInitializationError(f"Database initialization failed: {str(e)}")
            
    async def _create_indexes_if_not_exist(self):
        """Create indexes if they don't already exist."""
        try:
            # Simplification : plutôt que de vérifier si l'index existe, 
            # on utilise IF NOT EXISTS dans la requête directement
            async with self.engine.begin() as conn:
                await conn.execute(
                    text("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications (status)")
                )
                # Autres index si nécessaire
                await conn.execute(
                    text("CREATE INDEX IF NOT EXISTS idx_documents_user ON documents (user_id)")
                )
                await conn.execute(
                    text("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents (document_type)")
                )
        except Exception as e:
            logger.warning(f"Error creating indexes: {str(e)}")
            # Continue même si une erreur se produit, car ce n'est pas critique

    async def get_session(self) -> AsyncSession:
        """Create a new session."""
        if not self.engine:
            await self.init_db()
        return AsyncSession(self.engine, expire_on_commit=False)

    async def get_shared_session(self) -> AsyncSession:
        """Get the shared session, creating it if necessary."""
        if not self._shared_session:
            self._shared_session = await self.get_session()
        return self._shared_session

    async def close_shared_session(self):
        """Close the shared session if it exists."""
        if self._shared_session:
            await self._shared_session.close()
            self._shared_session = None

    async def get_read_session(self, timeout: float = 10.0) -> AsyncSession:
        """
        Get a session for read operations with a shared read lock.

        Args:
            timeout: Maximum time to wait for the lock in seconds

        Returns:
            AsyncSession: A SQLAlchemy async session with read lock

        Raises:
            SessionLockTimeoutError: If lock acquisition times out
        """
        # Get a shared read lock
        await self._rwlock.acquire_read(timeout)

        # Track this session
        session_id = self._get_next_session_id()
        session = await self.get_shared_session()
        self._active_sessions[session_id] = session

        return session, session_id

    async def release_read_session(self, session_id: int):
        """
        Release a read session.

        Args:
            session_id: ID of the session to release
        """
        if session_id in self._active_sessions:
            # Remove from tracking
            del self._active_sessions[session_id]

            # Release the read lock
            self._rwlock.release_read()

    async def get_write_session(self, timeout: float = 10.0) -> AsyncSession:
        """
        Get a session for write operations with an exclusive write lock.

        Args:
            timeout: Maximum time to wait for the lock in seconds

        Returns:
            AsyncSession: A SQLAlchemy async session with write lock

        Raises:
            SessionLockTimeoutError: If lock acquisition times out
        """
        # Get an exclusive write lock
        await self._rwlock.acquire_write(timeout)

        # Track this session
        session_id = self._get_next_session_id()
        session = await self.get_shared_session()
        self._active_sessions[session_id] = session

        return session, session_id

    async def release_write_session(self, session_id: int):
        """
        Release a write session.

        Args:
            session_id: ID of the session to release
        """
        if session_id in self._active_sessions:
            # Remove from tracking
            del self._active_sessions[session_id]

            # Release the write lock
            self._rwlock.release_write()

    def _get_next_session_id(self) -> int:
        """Get the next unique session ID."""
        self._session_counter += 1
        return self._session_counter

    async def delete_database(self):
        """Deletes the database."""
        try:
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
            logger.error(f"Database deletion failed: {str(e)}")
            raise DatabaseError(f"Error while deleting the database: {str(e)}")

    async def get_connection(self):
        """Get a connection from the pool."""
        if not self.engine:
            await self.init_db()
        return await self.connection_pool.get_connection()

    async def release_connection(self, conn):
        """Release a connection back to the pool."""
        await self.connection_pool.release_connection(conn)

    async def cleanup(self):
        """Clean up all database resources."""
        # Close all active sessions
        for session_id in list(self._active_sessions.keys()):
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]

        # Close shared session
        await self.close_shared_session()

        # Dispose engine
        if self.engine:
            await self.engine.dispose()

    # Make sure this method is called when the program exits
    def __del__(self):
        """Destructor to ensure resources are cleaned up."""
        # We can't use await in __del__, so create a task
        if self.engine:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.cleanup())
            except:
                # Ignore errors during shutdown
                pass


# =====================
# Session Context Managers
# =====================
@contextlib.asynccontextmanager
async def read_session_context(timeout: float = 10.0) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for getting a read-only database session.

    Usage:
        async with read_session_context() as session:
            # Use session here for reading operations

    Args:
        timeout: Maximum time to wait for the lock in seconds

    Yields:
        AsyncSession: A SQLAlchemy async session with read lock
    """
    manager = await DatabaseManager.get_instance()
    session, session_id = await manager.get_read_session(timeout)
    try:
        yield session
    finally:
        await manager.release_read_session(session_id)


@contextlib.asynccontextmanager
async def write_session_context(timeout: float = 10.0) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for getting a write database session.

    Usage:
        async with write_session_context() as session:
            # Use session here for writing operations
            await session.commit()

    Args:
        timeout: Maximum time to wait for the lock in seconds

    Yields:
        AsyncSession: A SQLAlchemy async session with write lock
    """
    manager = await DatabaseManager.get_instance()
    session, session_id = await manager.get_write_session(timeout)
    try:
        yield session
    finally:
        await manager.release_write_session(session_id)


# =====================
# Session Utility Functions
# =====================
async def get_session() -> AsyncSession:
    """
    Get a database session without explicit locking.
    For basic usage or when managing locks explicitly.

    Usage:
        session = await get_session()
        try:
            # Use session here
            await session.commit()
        finally:
            await session.close()

    Returns:
        AsyncSession: A SQLAlchemy async session
    """
    manager = await DatabaseManager.get_instance()
    return await manager.get_session()


# Exports
__all__ = [
    'get_session',
    'read_session_context',
    'write_session_context',
    'get_app_data_dir',
    'get_db_path',
    'DatabaseError',
    'DatabaseInitializationError',
    'ConnectionPoolExhaustedError',
    'SessionLockTimeoutError',
    'DatabaseManager'
]