from typing import Tuple
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

from sqlmodel import Session
from data.managers.user_manager import UserManager
from data.managers.job_offer_manager import JobOfferManager
from data.managers.cover_letter_manager import CoverLetterManager
from data.database import get_app_data_dir


class PDFCoverLetterGenerator:
    def __init__(self, session: Session):
        self.session = session
        self.user_manager = UserManager(self.session)
        self.job_offer_manager = JobOfferManager(self.session)
        self.cover_letter_manager = CoverLetterManager(self.session)

        self.config_path = get_app_data_dir() / "config"
        if not os.path.exists(self.config_path / "fonts"):
            os.makedirs(self.config_path)
        self.fonts_dir = os.path.join(self.config_path, "fonts")
        if os.path.exists(self.config_path / "fonts"):
            self.signature_path = os.path.join(self.config_path, "signature.png")
        else:
            self.signature_path = None
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

    async def generate_cover_letter_pdf(self, user_id: int, job_id: int) -> Tuple[bool, str]:
        """Generate a PDF cover letter, ensuring it is exactly one page."""
        # Get data from database
        user = await self.user_manager.get_user_by_id(user_id)
        job_offer = await self.job_offer_manager.get_job_offer_by_id(job_id)
        cover_letter = await self.cover_letter_manager.get_cover_letter_by_user_and_job_id(user_id, job_id)

        if not user or not job_offer or not cover_letter:
            return False, "Missing data for generating cover letter PDF."

        # Prepare letter data
        data = {
            "sender": f"{user.contact_info}",
            "recipient": cover_letter.recipient_info,
            "subject": cover_letter.subject,
            "body": (
                f"{cover_letter.greeting}\n\n"
                f"{cover_letter.introduction}\n\n"
                f"{cover_letter.skills_experience}\n\n"
                f"{cover_letter.motivation}\n\n"
                f"{cover_letter.conclusion}\n\n"
                f"{cover_letter.closing}"
            ),
            "filename": self._sanitize_filename(f"Cover_Letter_{user.last_name}_{job_offer.company_name}.pdf")
        }

        # Try different font sizes until the letter fits exactly one page
        for font_size in [12, 11, 10]:
            # Create styles with current font size
            styles = self._create_styles(font_size)

            # Generate PDF content
            letter_content = self._create_letter_content(data, styles)

            # Generate PDF in memory
            buffer = BytesIO()
            self._build_pdf(letter_content, buffer, data["filename"])

            # Get PDF data and check number of pages
            pdf_data = buffer.getvalue()
            num_pages = self._count_pdf_pages(pdf_data)

            if num_pages == 1:
                # PDF is exactly one page, save it
                await self.cover_letter_manager.add_pdf_to_cover_letter(cover_letter.id, pdf_data)
                buffer.close()
                return True, "Cover letter generated successfully"

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

    def _create_letter_content(self, data: dict, styles: dict) -> list:
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
        city = sender_lines[2].split(' ', 1)[1] if len(sender_lines) > 2 else None
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

        if os.path.exists(self.signature_path):
            letter_content.append(Spacer(1, 0.8 * cm))  # Reduced spacing
            letter_content.append(Image(self.signature_path, width=4 * cm, height=1.5 * cm, hAlign='RIGHT'))

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