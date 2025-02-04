import asyncio
import logging
from typing import List
from sqlmodel import Session

from services.job_automation.jobup.scraper import JobScraper
from services.job_automation.jobup.auto_apply import AutoApply
from local.menus.scraping.config import ScrapingConfig

logger = logging.getLogger(__name__)

class KeywordScrapingScheduler:
    def __init__(self, session: Session, user_id: int, keywords: List[str], interval_seconds: int = 3600, max_browsers: int = 5, scraping_config: ScrapingConfig = None):
        """
        Initialize the scheduler.
        :param session: Database session
        :param user_id: ID of the user for auto-apply
        :param keywords: List of keywords to use for scraping
        :param interval_seconds: Interval between scraping rounds (default: 3600 seconds)
        :param max_browsers: Maximum number of browsers to use in scraping
        :param scraping_config: Optional ScrapingConfig to use for additional parameters
        """
        self.session = session
        self.user_id = user_id
        self.keywords = keywords
        self.interval_seconds = interval_seconds
        self.max_browsers = max_browsers
        self.running = False
        self.auto_apply = AutoApply(session, user_id)
        self.scraping_config = scraping_config or ScrapingConfig()
        self.current_keyword_index = 0

    async def run(self):
        """
        Run the scheduler indefinitely. For each iteration:
        1. Process one keyword per interval
        2. After the keyword is processed, trigger auto-apply for new quick_apply offers
        3. Move to the next keyword in the next interval
        """
        self.running = True
        while self.running:
            try:
                # Get the current keyword to process
                if self.current_keyword_index >= len(self.keywords):
                    self.current_keyword_index = 0

                current_keyword = self.keywords[self.current_keyword_index]
                logger.info(f"Processing keyword {self.current_keyword_index + 1}/{len(self.keywords)}: {current_keyword}")

                # Process the current keyword
                await self.start_scraping_for_keyword(current_keyword)
                logger.info(f"Completed scraping for keyword: {current_keyword}")

                # Process any new quick_apply offers
                if self.running:
                    logger.info("Processing new quick-apply offers")
                    await self.auto_apply.check_and_process_pending_jobs()
                # Move to the next keyword for the next interval
                self.current_keyword_index += 1

            except Exception as e:
                logger.error(f"Error in scheduler cycle: {e}")

            # Sleep until next interval if still running
            if self.running:
                logger.info(f"Scheduler sleeping for {self.interval_seconds} seconds until next keyword")
                await asyncio.sleep(self.interval_seconds)

    async def start_scraping_for_keyword(self, keyword: str):
        """
        Start a scraping process for a single keyword.
        :param keyword: The keyword to use in the scraping search
        """
        try:
            logger.info(f"Starting scraping for keyword: {keyword}")
            async with JobScraper(self.session, max_browsers=self.max_browsers) as scraper:
                # Start scraping with the keyword and additional configuration
                await scraper.start_scraping(
                    term=keyword,
                    employment_grade_min=self.scraping_config.employment_grade_min,
                    employment_grade_max=self.scraping_config.employment_grade_max,
                    publication_date=self.scraping_config.publication_date,
                    category=self.scraping_config.category,
                    region=self.scraping_config.region
                )
                logger.info(f"Scraping completed for keyword: {keyword}")
        except Exception as e:
            logger.error(f"Error scraping for keyword '{keyword}': {e}")

    def stop(self):
        """
        Stop the scheduler loop gracefully.
        """
        logger.info("Stopping keyword scraping scheduler")
        self.running = False