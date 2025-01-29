from playwright.async_api import async_playwright
from typing import List, Optional
from sqlmodel import Session
from data.managers.job_offer_manager import JobOfferManager
import asyncio
import re
import logging
from collections import deque

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
        self.max_browsers = max_browsers
        self.page_lock = asyncio.Lock()  # Prevent multiple browsers from scraping the same page
        self.scraped_pages = set()  # Track already scraped pages
        self.job_buffer = deque(maxlen=buffer_size)  # Circular buffer for job offers
        self.buffer_lock = asyncio.Lock()
        self.playwright = None
        self.browsers = []
        # Configure logging level
        if hasattr(logging, debug_level.upper()):
            logger.setLevel(getattr(logging, debug_level.upper()))

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for browser in self.browsers:
            await browser.close()
        await self.playwright.stop()

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
        async def _add_to_buffer():
            async with self.buffer_lock:
                self.job_buffer.extend(job_offers_data)
        return _add_to_buffer()

    async def process_buffer(self):
        """
        Processes the job offers stored in the buffer and saves them to the database.
        """
        while True:
            async with self.buffer_lock:
                while self.job_buffer:
                    job_offer_data = self.job_buffer.popleft()
                    if await self.job_offer_manager.add_job_offer(**job_offer_data):
                        logger.info(f"Job offer added to database: {job_offer_data['external_id']}")
            await asyncio.sleep(0.1)  # Reduce delay to process the buffer faster

    async def scrape_page(self, page_number: int):
        browser = await self.playwright.chromium.launch(headless=True)
        self.browsers.append(browser)
        page = await browser.new_page()
        search_params = {**self.search_params, 'page': page_number}
        url = self.build_url(**{k: v for k, v in search_params.items() if v is not None})
        logger.info(f"Navigating to page {page_number}...")

        try:
            await page.goto(url)
            await page.wait_for_load_state("load")
            await page.wait_for_selector("div[data-cy='vacancy-serp-item']", state="attached", timeout=15000)

            job_links = await page.query_selector_all("div[data-cy='vacancy-serp-item-active'], div[data-cy='vacancy-serp-item']")
            total_jobs = len(job_links)
            logger.info(f"Total job panels found on page {page_number}: {total_jobs}")

            job_offers_data = []
            for index in range(total_jobs):
                try:
                    job_link = job_links[index]
                    if not job_link:
                        continue

                    logger.info(f"Clicking on job panel {index + 1} on page {page_number}...")
                    await job_link.click()
                    await page.wait_for_load_state("load")
                    try:
                        # Use short timeouts to avoid slowing down the process
                        await page.wait_for_selector("[data-cy='vacancy-logo']", state="attached", timeout=3000)
                    except Exception:
                        logger.debug("Logo element not found, continuing anyway...")
                    try:
                        await page.wait_for_selector("[data-cy='vacancy-title']", state="attached", timeout=3000)
                    except Exception:
                        logger.debug("Title element not found, continuing anyway...")
                    try:
                        await page.wait_for_selector("[data-cy='vacancy-description']", state="attached", timeout=3000)
                    except Exception:
                        logger.debug("Description element not found, continuing anyway...")

                    # Try to get job description with a more flexible approach
                    description_selectors = [
                        "[data-cy='vacancy-description']"  # Fallback to main article content if specific selectors fail
                    ]

                    job_description = None
                    for selector in description_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                job_description = await element.inner_text()
                                if job_description and len(job_description.strip()) > 0:
                                    break
                        except Exception:
                            continue

                    # If still no description, try getting all visible text from the main content area
                    if not job_description:
                        try:
                            main_content = await page.query_selector("main") or await page.query_selector("article") or await page.query_selector(".content")
                            if main_content:
                                job_description = await main_content.inner_text()
                        except Exception:
                            pass

                    # Flexible element extraction function
                    async def get_element_text(selector):
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                return await element.inner_text()
                            else:
                                return None
                        except Exception:
                            pass
                        return None

                    # Get job details with fallback selectors
                    job_title = await get_element_text("[data-cy='vacancy-title']")
                    company_name = await get_element_text("[data-cy='vacancy-logo']")
                    publication_date = await get_element_text("[data-cy='info-publication']")
                    activity_rate = await get_element_text("[data-cy='info-workload']")
                    contract_type = await get_element_text("[data-cy='info-contract']")
                    work_location = await get_element_text("[data-cy='info-location-link']")

                    try:
                        if work_location:
                            if "Location" in work_location or "Place" in work_location:
                                work_location = work_location.split(":")[-1].strip()
                    except Exception:
                        pass

                    company_info = await get_element_text("[data-cy='vacancy-lead'] p")
                    company_contact = await get_element_text("[data-cy='vacancy-contact']")

                    # Get company URL
                    company_url = "Not specified"
                    try:
                        url_element = await page.query_selector("[data-cy='company-url']")
                        if url_element:
                            company_url = await url_element.get_attribute("href") or "Not specified"
                    except Exception:
                        pass

                    # Get categories
                    categories = []
                    try:
                        category_elements = await page.query_selector_all("[data-cy='vacancy-meta'] a")
                        for el in category_elements:
                            text = await el.inner_text()
                            if text.strip():
                                categories.append(text)
                    except Exception:
                        pass

                    # Check for quick apply
                    quick_apply = False
                    try:
                        quick_apply_element = await page.query_selector("div[data-cy='vacancy-serp-item-active'] [data-cy='quick-apply']")
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

                except Exception as e:
                    logger.error(f"Error scraping job on page {page_number}, index {index}: {str(e)}")
                    continue

            await self.add_job_offers_to_buffer(job_offers_data)

        except Exception as e:
            logger.error(f"Error processing page {page_number}: {str(e)}")
        finally:
            await page.close()
            await browser.close()

    async def start_scraping(self, term: Optional[str] = None, employment_grade_min: Optional[int] = None,
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
        # Start buffer processing task
        asyncio.create_task(self.process_buffer())

        # Initialize playwright if not already done
        if self.playwright is None:
            self.playwright = await async_playwright().start()

        # Scan total number of available pages
        browser = await self.playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        logger.info("Navigating to target URL...")
        initial_url = self.build_url(**{k: v for k, v in self.search_params.items() if v is not None})
        await page.goto(initial_url)
        await page.wait_for_load_state("load")

        try:
            selector = 'div.d_flex.ai_center.gap_s4'

            # Check if element exists
            element = await page.query_selector(selector)
            if not element:
                logger.info("No pagination found, only one page available")
                max_page = 1
            else:
                page_numbers = []
                elements = await page.query_selector_all(selector)

                for element in elements:
                    text_content = await element.inner_text()
                    numbers = [int(num) for num in re.findall(r'\d+', text_content)]
                    page_numbers.extend(numbers)

                max_page = max(page_numbers) if page_numbers else 1
                logger.info(f"Total number of pages found: {max_page}")

        finally:
            await page.close()
            await browser.close()

        # Scrape pages concurrently
        tasks = []
        for current_page in range(1, max_page + 1):
            async with self.page_lock:
                if current_page not in self.scraped_pages:
                    self.scraped_pages.add(current_page)
                    tasks.append(self.scrape_page(current_page))

        await asyncio.gather(*tasks)

        # Cleanup
        await self.playwright.stop()
        self.playwright = None

    async def get_element_text(self, page, selector):
        try:
            element = await page.query_selector(selector)
            return await element.inner_text() if element else None
        except Exception:
            return None

    async def detect_max_pages(self, page):
        try:
            element = await page.query_selector('div.d_flex.ai_center.gap_s4')
            if not element:
                return 1

            text_content = await element.inner_text()
            numbers = [int(num) for num in re.findall(r'\d+', text_content)]
            return max(numbers) if numbers else 1
        except Exception as e:
            logger.error(f"Error detecting max pages: {str(e)}")
            return 1

if __name__ == "__main__":
    # Start scraping
    logger.info("Starting job scraping...")
    scraper = JobScraper(max_browsers=10)  # Set number of browsers to use in parallel
    asyncio.run(scraper.start_scraping())