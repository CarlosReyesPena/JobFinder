from typing import Optional, Type, Any
from pydantic import BaseModel, Field
from crewai_tools import BaseTool
import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import date
from reportlab.pdfbase.pdfmetrics import stringWidth
from langdetect import detect
from babel.dates import format_date
import locale

class CoverLetterGenerator:
    def __init__(self, config_path="config"):
        self.config_path = config_path
        self.fonts_dir = os.path.join(self.config_path, "fonts")
        self.signature_path = os.path.join(self.config_path, "signature.png")
        self._register_fonts()
        self.styles = self._create_styles()

    def _register_fonts(self):
        if os.path.exists(self.fonts_dir) and os.path.isfile(os.path.join(self.fonts_dir, 'Helvetica.ttf')):
            pdfmetrics.registerFont(TTFont('Helvetica-Oblique', os.path.join(self.fonts_dir, 'Helvetica.ttf')))
            pdfmetrics.registerFont(TTFont('Helvetica-Bold', os.path.join(self.fonts_dir, 'Helvetica-Bold.ttf')))
            self.font_name = 'Helvetica-Oblique'
            self.bold_font_name = 'Helvetica-Bold'
        else:
            # Use a default font if Helvetica is not available
            print("Helvetica font not found. Using Times-Roman as default font.")
            pdfmetrics.registerFont(TTFont('Times-Roman', 'times.ttf'))
            pdfmetrics.registerFont(TTFont('Times-Bold', 'timesbd.ttf'))
            self.font_name = 'Times-Roman'
            self.bold_font_name = 'Times-Bold'

    def _create_styles(self, font_size=11):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Normal_LEFT',
                                  parent=styles['Normal'],
                                  fontName=self.font_name,
                                  fontSize=font_size,
                                  leading=14,
                                  alignment=0))
        styles.add(ParagraphStyle(name='Indented',
                                  parent=styles['Normal_LEFT'],
                                  leftIndent=10*cm))
        return styles

    def _verify_line_length(self, text, max_width, font_name, font_size):
        lines = text.split('\n')
        for line in lines:
            if stringWidth(line, font_name, font_size) > max_width:
                return False
        return True

    def merge_dict_lines(self, data):
        """
        Merges the lines of a dictionary into a single string with each value on a new line.
        """
        merged_text = []

        for value in data.values():
            if isinstance(value, dict):
                # If the value is another dictionary, recursively merge it
                merged_text.append(self.merge_dict_lines(value))
            elif isinstance(value, list):
                # If the value is a list, join its elements with a newline
                merged_text.append(", ".join(str(item) for item in value))
            else:
                # Otherwise, just add the value
                merged_text.append(str(value))

        return "\n".join(merged_text)

    def generate_cover_letter(self, data, filename):
        #max_width = A4[0] - 2.54*cm - 2.54*cm - 9*cm
        recipient_text = data["recipient"] if isinstance(data["recipient"], str) else self.merge_dict_lines(data["recipient"])
        #if not self._verify_line_length(recipient_text, max_width, self.font_name, 11):
         #   return False, "Error: The recipient text is too long for the specified format."

        doc = SimpleDocTemplate(filename, pagesize=A4,
                                leftMargin=2.54*cm, rightMargin=2.54*cm,
                                topMargin=2.54*cm, bottomMargin=1.27*cm)

        letter_content = self._create_letter_content(data)

        try:
            doc.build(letter_content, onFirstPage=self._page_counter, onLaterPages=self._page_counter)
            return True, f"The cover letter has been generated in the file {filename}"
        except ValueError as e:
            try:
                print("Error: The letter content exceeds one page. Trying with font size 10")
                self.styles = self._create_styles(font_size=10)
                letter_content = self._create_letter_content(data)
                doc.build(letter_content, onFirstPage=self._page_counter, onLaterPages=self._page_counter)
            except ValueError as e:
                return False, "Error: The letter content exceeds one page with font size 10"
            return True, f"The cover letter has been generated in the file {filename}"
        
    def _format_date(self, lang):
        today = date.today()
        if lang == 'fr':
            try:
                locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
            except locale.Error:
                pass  # If the locale is not available, continue with the default locale
            
            # Using babel's format_date for French
            date_fr = format_date(today, format='d MMMM yyyy', locale='fr_FR')
            
            # Manual correction for "août" if necessary
            date_fr = date_fr.replace("août", "août")
            
            return f"À Pully, le {date_fr}"
        elif lang == 'de':
            return f"Pully, den {format_date(today, format='d. MMMM yyyy', locale='de_DE')}"
        elif lang == 'it':
            return f"Pully, {format_date(today, format='d MMMM yyyy', locale='it_IT')}"
        else:  # Default to English
            return f"Pully, {format_date(today, format='MMMM d, yyyy', locale='en_US')}"

    def _create_letter_content(self, data):
        letter_content = []

        # Merge lines for sender and recipient if they are dicts
        sender_text = data["sender"] if isinstance(data["sender"], str) else self.merge_dict_lines(data["sender"])
        recipient_text = data["recipient"] if isinstance(data["recipient"], str) else self.merge_dict_lines(data["recipient"])

        # Sender information
        sender_lines = sender_text.split('\n')
        full_name = sender_lines[0]
        for line in sender_lines:
            letter_content.append(Paragraph(line, self.styles['Normal_LEFT']))

        # Recipient information
        for line in recipient_text.split('\n'):
            letter_content.append(Paragraph(line, self.styles['Indented']))
        letter_content.append(Spacer(1, 1*cm))

        # Date
        lang = detect(data["body"])
        date_text = self._format_date(lang)
        letter_content.append(Paragraph(date_text, self.styles['Indented']))
        letter_content.append(Spacer(1, 2*cm))

        # Subject
        subject_style = ParagraphStyle('Subject', parent=self.styles['Normal_LEFT'], fontName=self.bold_font_name)
        letter_content.append(Paragraph(data["subject"], subject_style))
        letter_content.append(Spacer(1, 0.5*cm))

        # Letter body
        paragraphs = [p for p in data["body"].split('\n') if p.strip()]
        for i, paragraph in enumerate(paragraphs):
            letter_content.append(Paragraph(paragraph, self.styles['Normal_LEFT']))
            if i < len(paragraphs) - 1:
                letter_content.append(Spacer(1, 0.25*cm))

        # Add sender's full name with indentation
        letter_content.append(Spacer(1, 1*cm))
        letter_content.append(Paragraph(full_name, self.styles['Indented']))

        # Add signature if it exists
        if os.path.exists(self.signature_path):
            letter_content.append(Spacer(3, 1*cm))
            signature_container = Paragraph(f'<img src="{self.signature_path}" width="4cm" height="1.5cm"/>', self.styles['Indented'])
            letter_content.append(signature_container)

        return letter_content

    def _page_counter(self, doc):
        if doc.page > 1:
            raise ValueError("The content exceeds one page")


class PDFCoverToolInput(BaseModel):
    """Input schema for PDFCoverTool."""
    json_file_path: str = Field(
        ...,
        description="Full path to the JSON file containing cover letter data."
    )
    output_file_path: str = Field(
        ...,
        description="Full path where the generated PDF should be saved."
    )

class PDFCoverTool(BaseTool):
    name: str = "PDF Cover Letter Generation Tool"
    description: str = "A tool to generate PDF cover letters from JSON data using a custom template."
    args_schema: Type[BaseModel] = PDFCoverToolInput
    config_path: str = Field(default="config", description="Path to the configuration directory")

    def _run(self, json_file_path: str, output_file_path: str) -> Any:
        try:
            # Load JSON data
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Initialize CoverLetterGenerator with the specified config path
            generator = CoverLetterGenerator(config_path=self.config_path)

            # Generate the PDF
            success, message = generator.generate_cover_letter(data, output_file_path)

            if success:
                return success, f"PDF cover letter generated successfully: {output_file_path}"
            else:
                return success, f"Failed to generate PDF cover letter: {message}"

        except Exception as e:
            return False, f"Error generating PDF cover letter: {str(e)}"
