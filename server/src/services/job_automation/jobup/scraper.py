from playwright.async_api import async_playwright
from typing import List, Optional
from sqlmodel import Session
from data.managers.job_offer_manager import JobOfferManager
import asyncio
import re
import logging
from collections import deque
import uuid

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
    def __init__(self, session: Session, language: str = "fr",
                 max_browsers: int = 10, debug_level: str = "INFO"):
        """
        Initializes the scraper with a database session and managers.

        Args:
            session (Session): SQLModel session for database operations.
            base_url (str): Base URL for job listings.
            max_browsers (int): Maximum number of browsers to run in parallel.
        """
        self.session = session
        self.job_offer_manager = JobOfferManager(self.session)

        self.language = language
        if language.lower() == "en":
            self.base_url = "https://www.jobup.ch/en/jobs/"
        else:
            self.base_url = "https://www.jobup.ch/fr/emplois/"

        # Store initial search parameters
        self.search_params = {}
        self.max_browsers = max_browsers
        self.scraped_pages = set()  # Track already scraped pages
        self.job_ids_buffer = deque()
        self.job_ids_lock = asyncio.Lock()
        self.listing_pages_finished = False
        self.playwright = None
        self.browsers = []
        self.browser_sem = asyncio.Semaphore(self.max_browsers)
        # Configure logging level
        if hasattr(logging, debug_level.upper()):
            logger.setLevel(getattr(logging, debug_level.upper()))

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.playwright.stop()
        self.playwright = None

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

    async def scrape_page(self, page_number: int):
        async with self.browser_sem:
            browser = await self.playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            search_params = {**self.search_params, 'page': page_number}
            url = self.build_url(**{k: v for k, v in search_params.items() if v is not None})
            logger.info(f"Navigating to page {page_number}...")

            try:
                await page.goto(url)
                await page.wait_for_load_state("load")
                await page.wait_for_selector("div[data-cy='vacancy-serp-item']", state="attached", timeout=15000)

                job_elements = await page.query_selector_all("[data-cy^='serp-item-']")
                job_ids = []
                for elem in job_elements:
                    data_cy = await elem.get_attribute("data-cy")
                    if data_cy and data_cy.startswith("serp-item-"):
                        candidate = data_cy[len("serp-item-"):]
                        if self.is_valid_job_id(candidate):
                            job_ids.append(candidate)
                        else:
                            logger.debug(f"Ignored invalid job id candidate: {candidate}")
                logger.info(f"Job IDs found on page {page_number}: {job_ids}")
                await self.add_job_ids_to_buffer(job_ids)

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

        # Start detail workers before scraping pages
        detail_workers = [asyncio.create_task(self.job_detail_worker()) for _ in range(5)]

        # Scrape pages concurrently
        tasks = []
        for current_page in range(1, max_page + 1):
            if current_page not in self.scraped_pages:
                self.scraped_pages.add(current_page)
                tasks.append(self.scrape_page(current_page))

        await asyncio.gather(*tasks)
        self.listing_pages_finished = True

        # Wait for detail workers to finish
        await asyncio.gather(*detail_workers)

    async def get_element_text(self, page, selector):
        try:
            element = await page.query_selector(selector)
            return await element.inner_text() if element else None
        except Exception:
            return None

    # Method to check if a candidate job ID is a valid UUID
    def is_valid_job_id(self, candidate: str) -> bool:
        try:
            uuid.UUID(candidate)
            return True
        except ValueError:
            return False

    async def add_job_ids_to_buffer(self, job_ids: list):
        async with self.job_ids_lock:
            self.job_ids_buffer.extend(job_ids)

    async def job_detail_worker(self):
        while True:
            async with self.job_ids_lock:
                if not self.job_ids_buffer:
                    if self.listing_pages_finished:
                        break
                    else:
                        await asyncio.sleep(0.1)
                        continue
                job_id = self.job_ids_buffer.popleft()
            if await self.job_offer_manager.external_id_exists(job_id):
                logger.info(f"Job offer already exists for job_id: {job_id}")
                continue
            async with self.browser_sem:
                browser = await self.playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                detail_url = f"{self.base_url}detail/{job_id}/"
                logger.info(f"Scraping detail page: {detail_url}")
                try:
                    await page.goto(detail_url)
                    await page.wait_for_load_state("load")
                    job_description = await self.get_element_text(page, "[data-cy='vacancy-description']")
                    if not job_description:
                        try:
                            main_content = await page.query_selector("main") or await page.query_selector("article") or await page.query_selector(".content")
                            if main_content:
                                job_description = await main_content.inner_text()
                        except Exception:
                            pass
                    job_title = await self.get_element_text(page, "[data-cy='vacancy-title']")
                    company_name = await self.get_element_text(page, "[data-cy='vacancy-logo']") or await self.get_element_text(page, ".grid-area_company")
                    publication_date = await self.get_element_text(page, "[data-cy='info-publication']")
                    activity_rate = await self.get_element_text(page, "[data-cy='info-workload']")
                    contract_type = await self.get_element_text(page, "[data-cy='info-contract']")
                    work_location = await self.get_element_text(page, "[data-cy='info-location-link']") or await self.get_element_text(page, "li:has(svg path[d^='M12 12c']) .fw_semibold + span")
                    if work_location:
                        if "Location" in work_location or "Place" in work_location:
                            work_location = work_location.split(":")[-1].strip()
                    company_info = await self.get_element_text(page, "[data-cy='vacancy-lead'] p")
                    company_contact = await self.get_element_text(page, "[data-cy='vacancy-contact']")
                    company_url = "Not specified"
                    try:
                        url_element = await page.query_selector("[data-cy='company-url']")
                        if url_element:
                            company_url = await url_element.get_attribute("href") or "Not specified"
                    except Exception:
                        pass
                    categories = []
                    try:
                        category_elements = await page.query_selector_all("[data-cy='vacancy-meta'] a")
                        for el in category_elements:
                            text = await el.inner_text()
                            if text.strip():
                                categories.append(text)
                    except Exception:
                        pass
                    quick_apply = False
                    try:
                        quick_apply_element = await page.query_selector("[data-cy='quick-apply']")
                        quick_apply = bool(quick_apply_element)
                    except Exception:
                        pass
                    job_offer_data = {
                        "external_id": job_id,
                        "company_name": company_name,
                        "job_title": job_title,
                        "job_description": job_description,
                        "job_link": detail_url,
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
                    if await self.job_offer_manager.add_job_offer(**job_offer_data):
                        logger.info(f"Job offer added from detail page: {job_id}")
                except Exception as e:
                    logger.error(f"Error scraping job detail for {job_id}: {str(e)}")
                finally:
                    await page.close()
                    await browser.close()
        logger.info("Job detail worker finished processing.")