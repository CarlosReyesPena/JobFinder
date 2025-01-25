from playwright.sync_api import sync_playwright
from typing import List, Optional
from sqlmodel import Session
from data.managers.job_offer_manager import JobOfferManager
import time
import re
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import deque
import logging

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self, session: Session, base_url: str = "https://www.jobup.ch/fr/emplois/",
             max_browsers: int = 5, buffer_size: int = 50, debug_level: str = "INFO"):
        """
        Initializes the scraper with a database session and managers.

        Args:
            session (Session): SQLModel session for database operations.
            base_url (str): Base URL for job listings.
            max_browsers (int): Maximum number of browsers to run in parallel.
            buffer_size (int): Size of the buffer for storing job offers temporarily.
        """
        self.session = session
        self.job_offer_manager = JobOfferManager(self.session)

        self.base_url = base_url
        self.search_params = {}  # Store initial search parameters
        self.executor = ThreadPoolExecutor(max_workers=max_browsers)  # Thread pool for scraping
        self.max_browsers = max_browsers
        self.page_lock = threading.Lock()  # Prevent multiple browsers from scraping the same page
        self.scraped_pages = set()  # Track already scraped pages
        self.job_buffer = deque(maxlen=buffer_size)  # Circular buffer for job offers
        self.playwright = sync_playwright().start()
        self.buffer_lock = threading.Lock()
        # Configure logging level
        if hasattr(logging, debug_level.upper()):
            logger.setLevel(getattr(logging, debug_level.upper()))

    def build_url(self, page: Optional[int] = None, jobid: Optional[str] = None, term: Optional[str] = None,
                  employment_grade_min: Optional[int] = None, employment_grade_max: Optional[int] = None,
                  publication_date: Optional[int] = None, category: Optional[List[int]] = None,
                  benefit: Optional[int] = None, region: Optional[List[int]] = None) -> str:
        params = []
        if page:
            params.append(f"page={page}")
        if jobid:
            params.append(f"jobid={jobid}")
        if term:
            params.append(f"term={term}")
        if employment_grade_min is not None:
            params.append(f"employment-grade-min={employment_grade_min}")
        if employment_grade_max is not None:
            params.append(f"employment-grade-max={employment_grade_max}")
        if publication_date:
            params.append(f"publication-date={publication_date}")
        if category:
            params.extend([f"category={cat}" for cat in category])
        if benefit:
            params.append(f"benefit={benefit}")
        if region:
            params.extend([f"region={reg}" for reg in region])

        if params:
            return f"{self.base_url}?{'&'.join(params)}"
        return self.base_url

    def add_job_offers_to_buffer(self, job_offers_data):
        with self.buffer_lock:
            self.job_buffer.extend(job_offers_data)

    def process_buffer(self):
        """
        Processes the job offers stored in the buffer and saves them to the database.
        """
        while True:
            with self.buffer_lock:
                while self.job_buffer:
                    job_offer_data = self.job_buffer.popleft()
                    self.job_offer_manager.add_job_offer(**job_offer_data)
            time.sleep(0.1)  # Reduce delay to process the buffer faster


    def scrape_page(self, page_number: int):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            search_params = {**self.search_params, 'page': page_number}
            url = self.build_url(**{k: v for k, v in search_params.items() if v is not None})
            logger.info(f"Navigating to page {page_number}...")

            try:
                page.goto(url)
                page.wait_for_load_state("load")
                page.wait_for_selector("div[data-cy='vacancy-serp-item']", state="attached", timeout=15000)

                job_links = page.query_selector_all("div[data-cy='vacancy-serp-item-active'], div[data-cy='vacancy-serp-item']")
                total_jobs = len(job_links)
                logger.info(f"Total job panels found on page {page_number}: {total_jobs}")

                job_offers_data = []
                for index in range(total_jobs):
                    try:
                        job_link = job_links[index]
                        if not job_link:
                            continue

                        logger.info(f"Clicking on job panel {index + 1} on page {page_number}...")
                        job_link.click()
                        page.wait_for_load_state("load")
                        try:
                        # Use short timeouts to avoid slowing down the process
                            page.wait_for_selector("[data-cy='vacancy-logo']", state="attached", timeout=3000)
                        except Exception:
                            logger.debug("Logo element not found, continuing anyway...")
                        try:
                            page.wait_for_selector("[data-cy='vacancy-title']", state="attached", timeout=3000)
                        except Exception:
                            logger.debug("Title element not found, continuing anyway...")
                        try:
                            page.wait_for_selector("[data-cy='vacancy-description']", state="attached", timeout=3000)
                        except Exception:
                            logger.debug("Description element not found, continuing anyway...")

                        # Try to get job description with a more flexible approach
                        description_selectors = [
                            "[data-cy='vacancy-description']"  # Fallback to main article content if specific selectors fail
                        ]

                        job_description = None
                        for selector in description_selectors:
                            try:
                                element = page.query_selector(selector)
                                if element:
                                    job_description = element.inner_text()
                                    if job_description and len(job_description.strip()) > 0:
                                        break
                            except Exception:
                                continue

                        # If still no description, try getting all visible text from the main content area
                        if not job_description:
                            try:
                                main_content = page.query_selector("main") or page.query_selector("article") or page.query_selector(".content")
                                if main_content:
                                    job_description = main_content.inner_text()
                            except Exception:
                                pass

                        # Flexible element extraction function
                        def get_element_text(selector):
                            try:
                                element = page.query_selector(selector)
                                if element:
                                    return element.inner_text()
                                else:
                                    return None
                            except Exception:
                                pass
                            return None

                        # Get job details with fallback selectors
                        job_title = get_element_text("[data-cy='vacancy-title']")
                        company_name = get_element_text("[data-cy='vacancy-logo']")
                        publication_date = get_element_text("[data-cy='info-publication']")
                        activity_rate = get_element_text("[data-cy='info-workload']")
                        contract_type = get_element_text("[data-cy='info-contract']")
                        work_location = get_element_text("[data-cy='info-location-link']")

                        try:
                            if work_location:
                                if "Location" in work_location or "Place" in work_location:
                                    work_location = work_location.split(":")[-1].strip()
                        except Exception:
                            pass

                        company_info = get_element_text("[data-cy='vacancy-lead'] p")
                        company_contact = get_element_text("[data-cy='vacancy-contact']")

                        # Get company URL
                        company_url = "Not specified"
                        try:
                            url_element = page.query_selector("[data-cy='company-url']")
                            if url_element:
                                company_url = url_element.get_attribute("href") or "Not specified"
                        except Exception:
                            pass

                        # Get categories
                        categories = []
                        try:
                            category_elements = page.query_selector_all("[data-cy='vacancy-meta'] a")
                            categories = [el.inner_text() for el in category_elements if el.inner_text().strip()]
                        except Exception:
                            pass

                        # Check for quick apply
                        quick_apply = False
                        try:
                            quick_apply_element = page.query_selector("div[data-cy='vacancy-serp-item-active'] [data-cy='quick-apply']")
                            quick_apply = bool(quick_apply_element)
                        except Exception:
                            pass

                        # Get job ID from URL
                        external_id = None
                        try:
                            if "jobid=" in page.url:
                                external_id = page.url.split("jobid=")[-1]
                        except Exception:
                            continue

                        if external_id and job_description:
                            job_offer_data = {
                                "external_id": external_id,
                                "company_name": company_name,
                                "job_title": job_title,
                                "job_description": job_description,
                                "job_link": page.url,
                                "posted_date": publication_date,
                                "work_location": work_location,
                                "contract_type": contract_type,
                                "activity_rate": activity_rate,
                                "company_info": company_info,
                                "company_contact": company_contact,
                                "company_url": company_url,
                                "categories": ", ".join(categories) if categories else None,
                                "quick_apply": quick_apply
                            }
                            job_offers_data.append(job_offer_data)
                            logger.info(f"Added job offer with ID: {external_id}")

                    except Exception as e:
                        logger.error(f"Error scraping job on page {page_number}, index {index}: {str(e)}")
                        continue

                self.add_job_offers_to_buffer(job_offers_data)

            except Exception as e:
                logger.error(f"Error processing page {page_number}: {str(e)}")

            finally:
                try:
                    page.close()
                    browser.close()
                except Exception:
                    pass


    def start_scraping(self, term: Optional[str] = None, employment_grade_min: Optional[int] = None,
                      employment_grade_max: Optional[int] = None, publication_date: Optional[int] = None,
                      category: Optional[List[int]] = None, benefit: Optional[int] = None,
                      region: Optional[List[int]] = None):
        """
        Starts the scraping process with optional search parameters.
        """
        # Save search parameters
        self.search_params = {
            'term': term,
            'employment_grade_min': employment_grade_min,
            'employment_grade_max': employment_grade_max,
            'publication_date': publication_date,
            'category': category,
            'benefit': benefit,
            'region': region
        }
        # Start buffer processing thread
        threading.Thread(target=self.process_buffer, daemon=True).start()

        # Scan total number of available pages
        browser = self.playwright.chromium.launch(headless=True)
        page = browser.new_page()
        logger.info("Navigating to target URL...")
        initial_url = self.build_url(**{k: v for k, v in self.search_params.items() if v is not None})
        page.goto(initial_url)
        page.wait_for_load_state("load")

        try:
            selector = 'div.d_flex.ai_center.gap_s4'

            # Check if element exists
            element = page.query_selector(selector)
            if not element:
                logger.info("No pagination found, only one page available")
                max_page = 1
            else:
                page_numbers = []
                elements = page.query_selector_all(selector)

                for element in elements:
                    text_content = element.inner_text()
                    numbers = [int(num) for num in re.findall(r'\d+', text_content)]
                    page_numbers.extend(numbers)

                max_page = max(page_numbers) if page_numbers else 1
                logger.info(f"Total number of pages found: {max_page}")

        finally:
            page.close()
            browser.close()

        # Scrape pages in parallel
        futures = []
        for current_page in range(1, max_page + 1):
            with self.page_lock:
                if current_page not in self.scraped_pages:
                    self.scraped_pages.add(current_page)
                    futures.append(self.executor.submit(self.scrape_page, current_page))

        for future in futures:
            future.result()
        self.executor.shutdown(wait=True)

    def __del__(self):
        # Close Playwright at the end
        self.playwright.stop()

if __name__ == "__main__":
    # Start scraping
    logger.info("Starting job scraping...")
    scraper = JobScraper(max_browsers=10)  # Set number of browsers to use in parallel
    scraper.start_scraping()