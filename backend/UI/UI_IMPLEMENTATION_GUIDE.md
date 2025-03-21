# JobFinder UI Implementation Guide

This guide provides practical instructions for implementing the JobFinder UI, focusing on service integration and essential UI components.

## Development Setup

- **Framework**: PySide6 (Qt for Python)
- **Python Version**: 3.10+
- **Project Structure**: Use existing UITest directory structure

## Service Integration Plan

### 1. Web Extraction Service Integration

The `web_extract/web_extractor.py` service provides job content extraction capabilities:

```python
# Example integration
from backend.services.web_extract.web_extractor import WebExtractor

# In your UI class:
async def extract_job_from_url(self, url):
    self.status_label.setText("Extracting job offer...")
    extractor = WebExtractor()
    try:
        result = await extractor.extract_job_offer_from_url(url)
        if result.success:
            self.display_job_offer(result.extracted_offer)
            return result.job_id
        else:
            self.show_error("Extraction failed: " + result.error)
    except Exception as e:
        self.show_error(f"Error during extraction: {e}")
```

**UI Components Needed**:
- URL input field
- Extract button
- Status label
- Job preview area

### 2. Job Scraping Integration

The `job_automation/jobup/scraper.py` service provides job scraping capabilities:

```python
# Example integration
from backend.services.job_automation.jobup.scraper import JobScraper

# In your UI class:
async def start_scraping(self, search_term, filters):
    self.progress_bar.setVisible(True)
    self.status_label.setText("Scraping in progress...")

    async with JobScraper() as scraper:
        await scraper.start_scraping(
            term=search_term,
            region=filters.get('regions', []),
            category=filters.get('categories', [])
        )

    self.status_label.setText("Scraping completed")
    self.progress_bar.setVisible(False)
    self.refresh_job_list()
```

**UI Components Needed**:
- Search term input
- Filter selectors (regions, categories)
- Start/stop buttons
- Progress indicator
- Status label

### 3. Cover Letter Generation Integration

The `generation/generator.py` service provides cover letter generation:

```python
# Example integration
from backend.services.generation.generator import CoverLetterGenerator

# In your UI class:
async def generate_cover_letter(self, user_id, job_id):
    self.status_label.setText("Generating cover letter...")
    generator = CoverLetterGenerator()

    try:
        document = await generator.generate_cover_letter(user_id, job_id)
        if document:
            self.display_cover_letter(document.text_content)
            return document.id
        else:
            self.show_error("Failed to generate cover letter")
    except Exception as e:
        self.show_error(f"Error during generation: {e}")
```

**UI Components Needed**:
- Job selection dropdown
- Generate button
- Template selection (if applicable)
- Preview area
- Save button

### 4. PDF Generation Integration

The `generation/pdf_builder.py` service provides PDF document generation:

```python
# Example integration
from backend.services.generation.pdf_builder import PDFCoverLetterGenerator

# In your UI class:
async def generate_pdf(self, document_id):
    self.status_label.setText("Generating PDF...")
    pdf_generator = PDFCoverLetterGenerator()

    try:
        pdf_document = await pdf_generator.generate_pdf_from_document(document_id)
        if pdf_document:
            self.preview_pdf(pdf_document.binary_content)
            return pdf_document.id
        else:
            self.show_error("Failed to generate PDF")
    except Exception as e:
        self.show_error(f"Error generating PDF: {e}")
```

**UI Components Needed**:
- Document selection
- Generate PDF button
- PDF preview area
- Save/export options

### 5. Auto-Apply Integration

The `job_automation/jobup/auto_apply.py` service provides automated application:

```python
# Example integration
from backend.services.job_automation.jobup.auto_apply import AutoApply

# In your UI class:
async def run_auto_application(self, user_id, max_applications=5):
    self.status_label.setText("Starting auto-apply process...")
    self.progress_bar.setVisible(True)

    apply_manager = AutoApply(user_id)
    try:
        results = await apply_manager.check_and_process_pending_jobs()

        self.update_application_results(results)
        self.status_label.setText(f"Applied to {len(results['successes'])} jobs")
    except Exception as e:
        self.show_error(f"Auto-apply error: {e}")
    finally:
        self.progress_bar.setVisible(False)
```

**UI Components Needed**:
- Start button
- Configuration options
- Progress tracking
- Results display
- Log/history view

## Implementation Best Practices

### 1. Asynchronous Operations

- Use `asyncio` for all service calls
- Keep UI responsive during long operations
- Show progress indicators

```python
# Example of keeping UI responsive
import asyncio
from PySide6.QtCore import QObject, Signal, Slot

class Worker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, coroutine_func, *args, **kwargs):
        super().__init__()
        self.func = coroutine_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        async def execute():
            try:
                result = await self.func(*self.args, **self.kwargs)
                self.finished.emit(result)
            except Exception as e:
                self.error.emit(str(e))

        asyncio.run(execute())
```

### 2. Error Handling

- Catch exceptions from service calls
- Display user-friendly error messages
- Log detailed errors for debugging

### 3. UI State Management

- Disable controls during operations
- Show appropriate loading states
- Restore UI state after completion/error

## Page Implementation Approach

### 1. Job Scraping Page

Implement a page that allows users to:
- Select job site (JobUp)
- Configure search parameters
- Start/stop scraping
- View scraping progress
- See results summary

### 2. Job Management Page

Implement a page that allows users to:
- View all scraped jobs
- Filter and sort jobs
- View job details
- Take actions (generate cover letter, apply)

### 3. Document Generation Page

Implement a page that allows users to:
- Select a job for document generation
- Generate cover letter
- Preview generated content
- Edit if needed
- Generate PDF

### 4. Auto-Apply Page

Implement a page that allows users to:
- Configure auto-apply settings
- Start the process
- Monitor progress
- View results

## Next Steps

1. Implement the core framework
2. Create one page at a time, starting with job scraping
3. Test service integration with minimal UI
4. Expand UI features as services are integrated
5. Polish UI appearance and usability last