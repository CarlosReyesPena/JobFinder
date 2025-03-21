from typing import Tuple, Optional
from datetime import date
import os
import locale
from io import BytesIO
import asyncio

from babel.dates import format_date
from langdetect import detect
from PyPDF2 import PdfReader

from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Spacer, Image, Frame, PageTemplate, BaseDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from backend.data.managers import UserManager, JobOfferManager, DocumentManager
from backend.data.models import DocumentType


class PDFCoverLetterGenerator:
    def __init__(self):
        self.user_manager = UserManager()
        self.job_offer_manager = JobOfferManager()
        self.document_manager = DocumentManager()

        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Set fonts_dir to be in the same directory as this file
        self.fonts_dir = os.path.join(current_dir, "fonts")

        # Ensure fonts directory exists
        if not os.path.exists(self.fonts_dir):
            os.makedirs(self.fonts_dir)

        self._register_fonts()

    def _register_fonts(self):
        if os.path.exists(self.fonts_dir) and os.path.isfile(os.path.join(self.fonts_dir, 'Helvetica.ttf')):
            pdfmetrics.registerFont(TTFont('Helvetica-Oblique', os.path.join(self.fonts_dir, 'Helvetica.ttf')))
            pdfmetrics.registerFont(TTFont('Helvetica-Bold', os.path.join(self.fonts_dir, 'Helvetica-Bold.ttf')))
            self.font_name = 'Helvetica-Oblique'
            self.bold_font_name = 'Helvetica-Bold'
        else:
            print("Helvetica font not found. Using Times-Roman as default font.")
            pdfmetrics.registerFont(TTFont('Times-Roman', 'times.ttf'))
            pdfmetrics.registerFont(TTFont('Times-Bold', 'timesbd.ttf'))
            self.font_name = 'Times-Roman'
            self.bold_font_name = 'Times-Bold'

    def _create_styles(self, font_size: int = 12) -> dict:
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Normal_LEFT',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=font_size,
            leading=font_size + 2,  # Adjust leading based on font size
            alignment=4  # Justified
        ))
        styles.add(ParagraphStyle(
            name='Indented',
            parent=styles['Normal_LEFT'],
            leftIndent=10 * cm,
            alignment=4  # Justified
        ))
        return styles

    def _format_date(self, lang: str, city: str = None) -> str:
        today = date.today()
        if lang == 'fr':
            try:
                locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
            except locale.Error:
                pass
            date_fr = format_date(today, format='d MMMM yyyy', locale='fr_FR')
            if city:
                return f"À {city}, le {date_fr}"
            return f"Le {date_fr}"
        elif lang == 'de':
            date_de = format_date(today, format='d. MMMM yyyy', locale='de_DE')
            if city:
                return f"{city}, den {date_de}"
            return f"Den {date_de}"
        elif lang == 'it':
            date_it = format_date(today, format='d MMMM yyyy', locale='it_IT')
            if city:
                return f"{city}, {date_it}"
            return f"Il {date_it}"
        else:
            date_en = format_date(today, format='MMMM d, yyyy', locale='en_US')
            if city:
                return f"{city}, {date_en}"
            return date_en

    def _count_pdf_pages(self, pdf_data: bytes) -> int:
        """Count the number of pages in a PDF byte stream."""
        pdf_stream = BytesIO(pdf_data)
        pdf = PdfReader(pdf_stream)
        return len(pdf.pages)

    def _sanitize_filename(self, filename: str) -> str:
        """Cleans the filename of forbidden characters."""
        # Characters forbidden in most file systems
        forbidden_chars = '<>:"/\\|?*'
        # Replace forbidden characters with underscore
        for char in forbidden_chars:
            filename = filename.replace(char, '_')
        # Remove spaces at start and end
        filename = filename.strip()
        # Replace multiple spaces with single underscore
        filename = '_'.join(filter(None, filename.split()))
        return filename

    def _get_sender_info(self, user) -> str:
        """
        Format the sender information from user's data and config.
        The config should contain: address, postal_code, city, phone_number
        """
        # Start with full name
        sender_lines = [f"{user.first_name} {user.last_name}"]

        # Get user configuration for contact details
        config = user.config or {}

        # Add address if available
        if 'address' in config:
            sender_lines.append(config['address'])

        # Add postal code and city if available
        city_line = ""
        if 'postal_code' in config:
            city_line += config['postal_code']
        if 'city' in config:
            if city_line:
                city_line += " "
            city_line += config['city']
        if city_line:
            sender_lines.append(city_line)

        # Add phone number if available
        if 'phone_number' in config:
            sender_lines.append(f"Num. : {config['phone_number']}")

        # Add email
        sender_lines.append(user.email)

        return "\n".join(sender_lines)

    async def _get_signature_path(self, user_id: int) -> Optional[str]:
        """
        Get the path to the user's signature by extracting it from the database.

        Args:
            user_id: ID of the user

        Returns:
            Optional[str]: Path to signature file or None if not found
        """
        success, path = await self.document_manager.extract_latest_document_by_type_to_temp(
            user_id=user_id,
            document_type=DocumentType.SIGNATURE
        )

        if success and os.path.exists(path):
            return path
        return None

    async def generate_cover_letter_pdf(self, user_id: int, job_id: Optional[int] = None, document_id: Optional[int] = None) -> Tuple[bool, str]:
        """Generate a PDF cover letter, ensuring it is exactly one page.

        Args:
            user_id: The ID of the user
            job_id: Optional job offer ID (mutually exclusive with document_id)
            document_id: Optional cover letter document ID (mutually exclusive with job_id)
        """
        if job_id is None and document_id is None:
            return False, "Either job_id or document_id must be provided."

        if job_id is not None and document_id is not None:
            return False, "Only one of job_id or document_id should be provided, not both."

        # Get data from database
        user = await self.user_manager.get_user_by_id(user_id)

        # Get the cover letter document
        if document_id:
            cover_letter = await self.document_manager.get_document_by_id(document_id)
            if cover_letter and cover_letter.job_id:
                job_id = cover_letter.job_id
                job_offer = await self.job_offer_manager.get_job_offer_by_id(job_id)
            else:
                job_offer = None
        else:
            # Get the latest cover letter for the job
            cover_letter = await self.document_manager.get_latest_cover_letter_for_job(job_id, user_id)
            job_offer = await self.job_offer_manager.get_job_offer_by_id(job_id)

        if not user or not cover_letter:
            return False, "Missing data for generating cover letter PDF."

        # Get company name from job offer if available
        company_name = "Unknown"
        if job_offer:
            company_name = job_offer.job_info.get('company_name', 'Unknown')

        # Extract content from the document's json_content
        if not cover_letter.json_content:
            return False, "Cover letter has no content."

        content = cover_letter.json_content

        # Get formatted sender information from user config
        sender_info = self._get_sender_info(user)

        # Prepare letter data
        data = {
            "sender": sender_info,
            "recipient": content.get("recipient_info", ""),
            "subject": content.get("subject", "Application for Position"),
            "body": (
                f"{content.get('greeting', '')}\n\n"
                f"{content.get('introduction', '')}\n\n"
                f"{content.get('skills_experience', '')}\n\n"
                f"{content.get('motivation', '')}\n\n"
                f"{content.get('conclusion', '')}\n\n"
                f"{content.get('closing', '')}"
            ),
            "filename": self._sanitize_filename(f"Cover_Letter_{user.last_name}_{company_name}.pdf")
        }

        # Try different font sizes until the letter fits exactly one page
        for font_size in [12, 11, 10]:
            # Create styles with current font size
            styles = self._create_styles(font_size)

            # Generate PDF content (now with user_id parameter)
            letter_content = await self._create_letter_content(user_id, data, styles)

            # Generate PDF in memory
            buffer = BytesIO()
            self._build_pdf(letter_content, buffer, data["filename"])

            # Get PDF data and check number of pages
            pdf_data = buffer.getvalue()
            num_pages = self._count_pdf_pages(pdf_data)

            if num_pages == 1:
                # PDF is exactly one page, update the document with the PDF content
                updated_document = await self.document_manager.update_document(
                    document_id=cover_letter.id,
                    binary_content=pdf_data,
                    metadata={
                        **(cover_letter.metadata or {}),
                        "pdf_generated": True,
                        "pdf_date": date.today().isoformat(),
                        "pdf_pages": 1
                    }
                )
                buffer.close()

                if updated_document:
                    return True, "Cover letter PDF generated successfully"
                else:
                    return False, "Failed to update document with PDF"

            buffer.close()

        return False, "Could not fit cover letter to exactly one page even with minimum font size"

    async def generate_cover_letters_batch(self, user_id: int, job_ids: list[int], max_concurrent: int = 3):
        """Generate multiple cover letters concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(job_id: int):
            async with semaphore:
                return await self.generate_cover_letter_pdf(user_id, job_id)

        tasks = [generate_with_semaphore(job_id) for job_id in job_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = 0
        failed = 0

        for result in results:
            if isinstance(result, Exception):
                failed += 1
            else:
                success, _ = result
                if success:
                    successful += 1
                else:
                    failed += 1

        return {
            "successful": successful,
            "failed": failed,
            "total": len(job_ids)
        }

    async def _create_letter_content(self, user_id: int, data: dict, styles: dict) -> list:
        """Create the content elements for the PDF."""
        letter_content = []

        # 1. Sender information
        sender_text = data["sender"]
        sender_lines = sender_text.split('\n')
        full_name = sender_lines[0]
        for line in sender_lines:
            letter_content.append(Paragraph(line, styles['Normal_LEFT']))

        # 2. Recipient information
        recipient_text = data["recipient"]
        recipient_lines = recipient_text.split('\n')
        for line in recipient_lines:
            letter_content.append(Paragraph(line, styles['Indented']))
        letter_content.append(Spacer(1, 0.8 * cm))  # Reduced spacing

        # 3. Date
        lang = detect(data["body"])
        # Get city from sender info (line 2 or 3 typically has postal code and city)
        city = None
        if len(sender_lines) >= 3:
            # Try to extract city from the third line which typically has postal code and city
            city_line = sender_lines[2]
            # Try to split by postal code format (assume it's at the beginning of the line)
            parts = city_line.strip().split(' ', 1)
            if len(parts) > 1 and parts[0].isdigit():
                city = parts[1]
            else:
                city = city_line

        date_text = self._format_date(lang, city)
        letter_content.append(Paragraph(date_text, styles['Indented']))
        letter_content.append(Spacer(1, 2.0 * cm))  # Increased spacing between date and subject

        # 4. Subject
        subject_style = ParagraphStyle(
            'Subject',
            parent=styles['Normal_LEFT'],
            fontName=self.bold_font_name,
            alignment=4
        )
        letter_content.append(Paragraph(data["subject"], subject_style))
        letter_content.append(Spacer(1, 0.4 * cm))  # Reduced spacing

        # 5. Body
        paragraphs = [p for p in data["body"].split('\n') if p.strip()]
        for i, paragraph in enumerate(paragraphs):
            letter_content.append(Paragraph(paragraph, styles['Normal_LEFT']))
            if i < len(paragraphs) - 1:
                letter_content.append(Spacer(1, 0.2 * cm))  # Reduced spacing between paragraphs

        # 6. Signature
        letter_content.append(Spacer(1, 0.8 * cm))  # Reduced spacing
        letter_content.append(Paragraph(full_name, styles['Indented']))

        # Get signature path from database
        signature_path = await self._get_signature_path(user_id)
        if signature_path and os.path.exists(signature_path):
            letter_content.append(Spacer(1, 0.8 * cm))  # Reduced spacing
            letter_content.append(Image(signature_path, width=4 * cm, height=1.5 * cm, hAlign='RIGHT'))

        return letter_content

    def _build_pdf(self, letter_content: list, buffer: BytesIO, filename: str):
        """Build the PDF document with proper title metadata."""
        # Increased margins to help content fit on one page
        frame = Frame(
            2.54 * cm,          # left margin
            1.27 * cm,          # bottom margin
            A4[0] - 5.08 * cm,  # width (A4 - margins)
            A4[1] - 2.54 * cm,  # height (A4 - margins) - Increased usable space
            id='normal'
        )

        template = PageTemplate(id='template', frames=[frame])
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            pageTemplates=[template],
            title=filename.replace('.pdf', '')  # Set the document title
        )

        # Build the PDF
        doc.build(letter_content)