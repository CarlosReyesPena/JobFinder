import logging
from backend.data.managers import JobOfferManager, DocumentManager, ApplicationManager
from backend.services.generation.generator import CoverLetterGenerator
from backend.services.generation.pdf_builder import PDFCoverLetterGenerator
from backend.services.job_automation.jobup.form_filler import FormFiller
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
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.job_offer_manager = JobOfferManager()
        self.document_manager = DocumentManager()
        self.pdf_cover_builder = PDFCoverLetterGenerator()
        self.application_manager = ApplicationManager()
        self.cover_letter_generator = CoverLetterGenerator()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_pending_quick_apply_jobs(self) -> List:
        """
        Get all quick_apply jobs that haven't been applied to yet.

        Returns:
            List of job offers that are quick_apply enabled and not yet applied to
        """
        job_offers = await self.job_offer_manager.get_quick_apply_job_offers()
        pending_jobs = []

        for job in job_offers:
            # Check if there's already an application for this job
            applications = await self.application_manager.get_job_applications(job.id)
            user_applications = [app for app in applications if app.user_id == self.user_id]
            
            if not user_applications:
                pending_jobs.append(job)

        return pending_jobs

    async def process_single_job(self, job_offer) -> ApplicationResult:
        """Process a single job offer asynchronously."""
        company_name = job_offer.job_info.get('company_name', 'Unknown Company')
        job_title = job_offer.job_info.get('job_title', 'Unknown Position')
        
        result = ApplicationResult(
            job_id=job_offer.id,
            company_name=company_name,
            job_title=job_title,
            status="Started"
        )

        try:
            self.logger.info(f"Processing job: {job_title} at {company_name}")

            # Generate cover letter content
            cover_letter = await self.cover_letter_generator.generate_cover_letter(
                user_id=self.user_id,
                job_id=job_offer.id
            )

            if not cover_letter:
                result.status = "Failed"
                result.error = "Cover letter generation failed"
                return result

            # Generate PDF version of the cover letter
            success, message = await self.pdf_cover_builder.generate_cover_letter_pdf(
                user_id=self.user_id,
                document_id=cover_letter.id
            )

            if not success:
                result.status = "Failed"
                result.error = f"PDF generation failed: {message}"
                return result

            # Fill application form
            form_filler = FormFiller(self.user_id)
            try:
                await form_filler.fill_apply_form(job_offer.job_link, direct_apply=True)
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

            # Create application record in database
            await self.application_manager.create_application(
                user_id=self.user_id,
                job_id=job_offer.id,
                status="submitted"
            )

            result.status = "Success"
            self.logger.info(f"Successfully applied for: {job_title}")
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
            all_quick_apply = await self.job_offer_manager.get_quick_apply_job_offers()
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

async def run_auto_apply(user_id: int, max_applications: Optional[int] = None, max_concurrent: int = 3):
    """Utility function to run auto apply process."""
    auto_apply = AutoApply( user_id)
    return await auto_apply.process_job_offers(
        max_applications=max_applications,
        max_concurrent=max_concurrent
    )