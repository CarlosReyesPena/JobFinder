from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from pathlib import Path
import logging
from typing import Optional, Tuple
from data.managers.browser_cache_manager import BrowserCacheManager
from data.database import get_app_data_dir
from sqlmodel import Session

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserSession:
    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id
        self.cache_manager = BrowserCacheManager(session)
        self.cache_dir = self._get_cache_dir()
        self.login_url = "https://www.jobup.ch"

    def _get_cache_dir(self) -> Path:
        """Returns the cache folder path based on OS"""
        cache_dir = get_app_data_dir() / "cache" / f"user_{self.user_id}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _setup_browser_context(self, playwright):
        """Configure and return browser context"""
        browser = playwright.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-sandbox"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            storage_state=str(self.cache_dir / "state.json") if (self.cache_dir / "state.json").exists() else None
        )

        # Disable WebDriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
        """)

        return browser, context

    def is_logged_in(self, page) -> bool:
        """Check if user is logged in"""
        try:
            # Check for presence of user menu
            page.wait_for_selector("div[data-cy='offcanvas-menu-trigger']", timeout=5000)
            return True
        except PlaywrightTimeout:
            return False

    def get_browser_context(self, playwright, headless=False):
        """Return browser context"""
        browser = playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-sandbox"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            storage_state=str(self.cache_dir / "state.json") if (self.cache_dir / "state.json").exists() else None
        )

        # Disable WebDriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
        """)

        return context

    def save_session(self, context) -> bool:
        """Save session state"""
        try:
            # Save context state
            context.storage_state(path=str(self.cache_dir / "state.json"))

            # Save cache in database
            if self.cache_manager.save_cache_directory(self.user_id, str(self.cache_dir)):
                logger.info("Session saved successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error while saving session: {e}")
            return False

    def restore_session(self) -> bool:
        """Restore previous session"""
        try:
            return self.cache_manager.extract_cache_directory(self.user_id, str(self.cache_dir))
        except Exception as e:
            logger.error(f"Error while restoring session: {e}")
            return False

    def launch_browser_session(self) -> Tuple[bool, str]:
        """Launch browser session and handle login"""
        try:
            # Restore previous session if exists
            self.restore_session()

            with sync_playwright() as p:
                browser, context = self._setup_browser_context(p)
                page = context.new_page()

                # Navigate to login page
                logger.info(f"Navigating to {self.login_url}")
                page.goto(self.login_url)
                page.wait_for_load_state("networkidle")

                # Check if already logged in
                if self.is_logged_in(page):
                    logger.info("User already logged in")
                    self.save_session(context)
                    return True, "Already logged in"

                logger.info("Waiting for manual login...")
                print("Please login manually...")

                # Wait for user to login
                try:
                    page.wait_for_selector("div[data-cy='offcanvas-menu-trigger']", timeout=300000)  # 5 minutes timeout
                    logger.info("Login successful")

                    # Save session
                    if self.save_session(context):
                        return True, "Login successful"
                    return False, "Failed to save session"

                except PlaywrightTimeout:
                    return False, "Login timeout"

                finally:
                    browser.close()

        except Exception as e:
            error_msg = f"Error during browser session: {e}"
            logger.error(error_msg)
            return False, error_msg

def launch_browser_and_save_session(user_id: int, session: Session) -> Tuple[bool, str]:
    """
    Main entry point to launch browser session.

    Args:
        user_id (int): User ID
        session (Session): SQLModel Session

    Returns:
        Tuple[bool, str]: (success, message)
    """
    browser_session = BrowserSession(session, user_id)
    return browser_session.launch_browser_session()

if __name__ == "__main__":
    from sqlmodel import Session, create_engine
    engine = create_engine("sqlite:///job_application.db")
    with Session(engine) as session:
        success, message = launch_browser_and_save_session(user_id=1, session=session)
        print(f"Result: {message}")