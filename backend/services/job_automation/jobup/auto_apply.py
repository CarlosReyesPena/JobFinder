import logging
from sqlmodel import Session
from data.managers.job_offer_manager import JobOfferManager
from data.managers.cover_letter_manager import CoverLetterManager
from data.managers.application_manager import ApplicationManager
from services.generation.generator import CoverLetterGenerator
from services.generation.pdf_builder import PDFCoverLetterGenerator
from services.job_automation.jobup.form_filler import FormFiller
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ApplicationResult:
    job_id: int
    company_name: str
    job_title: str
    status: str
    error: str = None
    timestamp: datetime = datetime.now()

class AutoApply:
    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id
        self.job_offer_manager = JobOfferManager(session)
        self.cover_letter_manager = CoverLetterManager(session)
        self.pdf_cover_builder = PDFCoverLetterGenerator(session)
        self.application_manager = ApplicationManager(session)
        self.cover_letter_generator = CoverLetterGenerator(session)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_pending_quick_apply_jobs(self) -> List:
        """
        Get all quick_apply jobs that haven't been applied to yet.

        Returns:
            List of job offers that are quick_apply enabled and not yet applied to
        """
        job_offers = await self.job_offer_manager.get_job_offers_by_quick_apply()
        pending_jobs = []

        for job in job_offers:
            existing = await self.application_manager.get_application_by_user_and_job(
                user_id=self.user_id,
                job_id=job.id
            )
            if not existing:
                pending_jobs.append(job)

        return pending_jobs

    async def process_single_job(self, job_offer) -> ApplicationResult:
        """Process a single job offer asynchronously."""
        result = ApplicationResult(
            job_id=job_offer.id,
            company_name=job_offer.company_name,
            job_title=job_offer.job_title,
            status="Started"
        )

        try:
            self.logger.info(f"Processing job: {job_offer.job_title} at {job_offer.company_name}")

            cover_letter = await self.cover_letter_generator.generate_cover_letter(
                user_id=self.user_id,
                job_id=job_offer.id
            )

            if not cover_letter:
                result.status = "Failed"
                result.error = "Cover letter generation failed"
                return result

            success, message = await self.pdf_cover_builder.generate_cover_letter_pdf(
                user_id=self.user_id,
                job_id=job_offer.id
            )

            if not success:
                result.status = "Failed"
                result.error = f"PDF generation failed: {message}"
                return result

            form_filler = FormFiller(self.session, self.user_id)
            try:
                await form_filler.fill_apply_form(job_offer.external_id)
            except Exception as e:
                result.status = "Failed"
                result.error = f"Form filling failed: {str(e)}"
                return result
            finally:
                # Ensure that any threads/resources used by form_filler are closed
                if hasattr(form_filler, "close"):
                    closing = form_filler.close()
                    if asyncio.iscoroutine(closing):
                        await closing

            await self.application_manager.add_application(
                user_id=self.user_id,
                job_id=job_offer.id,
                application_status="Submitted"
            )

            result.status = "Success"
            self.logger.info(f"Successfully applied for: {job_offer.job_title}")
            return result

        except Exception as e:
            error_msg = f"Error processing job: {str(e)}"
            self.logger.error(error_msg)
            result.status = "Error"
            result.error = error_msg
            return result

    async def process_job_offers(self, max_applications: Optional[int] = None, max_concurrent: int = 3) -> Dict:
        """
        Process multiple job offers concurrently with improved error handling and reporting.
        If max_applications is None, process all pending quick_apply jobs.
        """
        # Get all pending quick_apply jobs
        jobs_to_process = await self.get_pending_quick_apply_jobs()

        if max_applications is not None:
            jobs_to_process = jobs_to_process[:max_applications]

        if not jobs_to_process:
            return {
                "status": "completed",
                "message": "No new jobs to process",
                "results": [],
                "summary": {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "errors": 0
                }
            }

        # Process jobs with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(job):
            async with semaphore:
                return await self.process_single_job(job)

        # Execute all tasks
        tasks = [process_with_semaphore(job) for job in jobs_to_process]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        summary = {
            "total": len(jobs_to_process),
            "successful": 0,
            "failed": 0,
            "errors": 0
        }

        for result in results:
            if isinstance(result, Exception):
                summary["errors"] += 1
            else:
                processed_results.append(result)
                if result.status == "Success":
                    summary["successful"] += 1
                else:
                    summary["failed"] += 1

        self.logger.info(
            f"Completed {summary['successful']} applications "
            f"({summary['failed']} failed, {summary['errors']} errors) "
            f"out of {summary['total']} attempts"
        )

        return {
            "status": "completed",
            "message": "Job processing completed",
            "results": processed_results,
            "summary": summary
        }

    async def check_and_process_pending_jobs(self) -> Dict:
        """
        Check how many quick_apply jobs exist, how many have been applied to,
        and process the remaining ones.

        Returns:
            Dict containing:
            - total_quick_apply: Total number of quick_apply jobs
            - already_applied: Number of jobs already applied to
            - pending: Number of jobs that were pending
            - application_results: Results of processing pending applications
        """
        try:
            # Get all quick apply jobs
            all_quick_apply = await self.job_offer_manager.get_job_offers_by_quick_apply()
            total_quick_apply = len(all_quick_apply)

            # Get pending jobs (not yet applied to)
            pending_jobs = await self.get_pending_quick_apply_jobs()
            already_applied = total_quick_apply - len(pending_jobs)

            self.logger.info(f"Found {total_quick_apply} quick_apply jobs total")
            self.logger.info(f"Already applied to {already_applied} jobs")
            self.logger.info(f"Found {len(pending_jobs)} pending jobs to process")

            # Process pending jobs if any
            if pending_jobs:
                application_results = await self.process_job_offers()
            else:
                application_results = {
                    "status": "completed",
                    "message": "No pending jobs to process",
                    "summary": {
                        "total": 0,
                        "successful": 0,
                        "failed": 0,
                        "errors": 0
                    }
                }

            return {
                "total_quick_apply": total_quick_apply,
                "already_applied": already_applied,
                "pending": len(pending_jobs),
                "application_results": application_results
            }

        except Exception as e:
            self.logger.error(f"Error in check_and_process_pending_jobs: {e}")
            return {
                "total_quick_apply": 0,
                "already_applied": 0,
                "pending": 0,
                "application_results": {
                    "status": "error",
                    "message": str(e),
                    "summary": {
                        "total": 0,
                        "successful": 0,
                        "failed": 0,
                        "errors": 1
                    }
                }
            }

async def run_auto_apply(user_id: int, session: Session, max_applications: Optional[int] = None, max_concurrent: int = 3):
    """Utility function to run auto apply process."""
    auto_apply = AutoApply(session, user_id)
    return await auto_apply.process_job_offers(
        max_applications=max_applications,
        max_concurrent=max_concurrent
    )

if __name__ == "__main__":
    import sys
    from data.database import DatabaseManager

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("AutoApply")

    async def main():
        try:
            user_id = int(sys.argv[1])
            max_applications = int(sys.argv[2]) if len(sys.argv) > 2 else None

            db_manager = DatabaseManager()
            async with db_manager.get_session() as session:
                results = await run_auto_apply(
                    user_id=user_id,
                    session=session,
                    max_applications=max_applications
                )

                print("\nApplication Results Summary:")
                print(f"Total Jobs: {results['summary']['total']}")
                print(f"Successful: {results['summary']['successful']}")
                print(f"Failed: {results['summary']['failed']}")
                print(f"Errors: {results['summary']['errors']}")

        except IndexError:
            logger.error("Please provide a user ID as the first argument.")
        except ValueError:
            logger.error("Invalid argument. Please provide a valid user ID and optionally a maximum number of applications.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    asyncio.run(main())
