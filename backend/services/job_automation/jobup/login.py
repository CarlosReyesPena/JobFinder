from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from pathlib import Path
import logging
from typing import Tuple
from backend.data.managers import DocumentManager
from backend.data.models import DocumentType
from backend.data.database import get_app_data_dir

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.document_manager = DocumentManager()
        self.cache_dir = self._get_cache_dir()
        self.login_url = "https://www.jobup.ch"

    def _get_cache_dir(self) -> Path:
        """Returns the cache folder path based on OS"""
        cache_dir = get_app_data_dir() / "cache" / f"user_{self.user_id}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    async def _setup_browser_context(self, playwright):
        """Configure and return browser context"""
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-sandbox"
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            storage_state=str(self.cache_dir / "state.json") if (self.cache_dir / "state.json").exists() else None
        )

        # Disable WebDriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
        """)

        return browser, context

    async def is_logged_in(self, page) -> bool:
        """Check if user is logged in"""
        try:
            # Check for presence of user menu
            await page.wait_for_selector("div[data-cy='offcanvas-menu-trigger']", timeout=5000)
            return True
        except PlaywrightTimeout:
            return False

    async def get_browser_context(self, playwright, headless=False):
        """Return browser context"""
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-sandbox"
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            storage_state=str(self.cache_dir / "state.json") if (self.cache_dir / "state.json").exists() else None
        )

        # Disable WebDriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
        """)

        return context

    async def save_session(self, context) -> bool:
        """Save session state"""
        try:
            # Save context state
            storage_path = self.cache_dir / "state.json"
            await context.storage_state(path=str(storage_path))

            # Save cache in database
            if storage_path.exists():
                browser_cache = storage_path.read_bytes()

                # Create a document for the cache
                await self.document_manager.create_document(
                    user_id=self.user_id,
                    document_type=DocumentType.BROWSER_CACHE,
                    name="jobup_browser_cache.json",
                    binary_content=browser_cache,
                    metadata={
                        "browser": "chromium",
                        "site": "jobup.ch",
                        "purpose": "login"
                    }
                )

                logger.info("Session saved successfully in database")
                return True
            return False
        except Exception as e:
            logger.error(f"Error while saving session: {e}")
            return False

    async def restore_session(self) -> bool:
        """Restore previous session"""
        try:
            # Get the latest browser cache document
            cache_doc = await self.document_manager.get_last_document_by_type(
                user_id=self.user_id,
                document_type=DocumentType.BROWSER_CACHE
            )

            if not cache_doc or not cache_doc.binary_content:
                logger.info("No browser cache found in database")
                return False

            # Extract the document to the cache directory
            success, path = await self.document_manager.extract_to_temp(cache_doc.id)

            if not success:
                logger.error(f"Failed to extract browser cache: {path}")
                return False

            # Copy the extracted file to the cache directory
            temp_file = Path(path)
            if temp_file.exists():
                state_path = self.cache_dir / "state.json"
                state_path.write_bytes(temp_file.read_bytes())
                logger.info(f"Session restored successfully from {temp_file} to {state_path}")
                return True

            return False
        except Exception as e:
            logger.error(f"Error while restoring session: {e}")
            return False

    async def launch_browser_session(self) -> Tuple[bool, str]:
        """Launch browser session and handle login"""
        try:
            # Restore previous session if exists
            await self.restore_session()

            async with async_playwright() as p:
                browser, context = await self._setup_browser_context(p)
                page = await context.new_page()

                # Navigate to login page
                logger.info(f"Navigating to {self.login_url}")
                await page.goto(self.login_url)
                await page.wait_for_load_state("networkidle")

                # Check if already logged in
                if await self.is_logged_in(page):
                    logger.info("User already logged in")
                    await self.save_session(context)
                    return True, "Already logged in"

                logger.info("Waiting for manual login...")
                print("Please login manually...")

                # Wait for user to login
                try:
                    await page.wait_for_selector(
                        "div[data-cy='offcanvas-menu-trigger']",
                        timeout=300000  # 5 minutes timeout
                    )
                    logger.info("Login successful")

                    # Save session
                    if await self.save_session(context):
                        return True, "Login successful"
                    return False, "Failed to save session"

                except PlaywrightTimeout:
                    return False, "Login timeout"

                finally:
                    await browser.close()

        except Exception as e:
            error_msg = f"Error during browser session: {e}"
            logger.error(error_msg)
            return False, error_msg

async def launch_browser_and_save_session(user_id: int) -> Tuple[bool, str]:
    """
    Main entry point to launch browser session.

    Args:
        user_id (int): User ID
        session (AsyncSession): SQLAlchemy Async Session

    Returns:
        Tuple[bool, str]: (success, message)
    """
    browser_session = BrowserSession( user_id)
    return await browser_session.launch_browser_session()