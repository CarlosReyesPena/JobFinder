from pydantic import BaseModel
from typing import List, Optional
from sqlmodel import Session
from data.managers.user_manager import UserManager
from data.managers.job_offer_manager import JobOfferManager
from data.managers.cover_letter_manager import CoverLetterManager
from data.models.cover_letter import CoverLetter
from langdetect import detect
from core.llm_manager import LLMManager
from core.settings import settings


MAX_RECIPIENT_LINE_LENGTH = 26
MAX_SUBJECT_LENGTH = 52
MAX_PARAGRAPH_LENGTH = 400
MAX_TOTAL_LENGTH = 2000

# Prompt templates as constants

REFERENCE_LETTER_STYLE_PROMPT = """Study this reference letter carefully to understand the writer's unique style:

{reference_letter}

As you write the new cover letter, embody the following aspects of the original writer's style:
1. Writing personality:
   - Analyze their tone (formal/informal balance)
   - Observe their sentence structure complexity
   - Note their word choice patterns
   - Identify their unique expressions and transitions

2. Thought process:
   - Understand how they structure their arguments
   - Notice how they present achievements
   - Observe how they connect ideas
   - Study their persuasion techniques

3. Style elements to mirror:
   - Rhythm and flow of paragraphs
   - Balance between professional and personal touch
   - Way of expressing enthusiasm
   - Approach to highlighting qualifications

DO NOT:
- Copy exact phrases or sentences
- Use the same examples or experiences
- Replicate specific achievements
- Use identical structure

Instead, write a completely new letter that feels like it was written by the same person,
with their unique voice and thought process, but applied to this new situation and role.
"""

SYSTEM_PROMPT_TEMPLATE = """You are an expert Swiss cover letter writer who creates personalized, professional cover letters.
Your task is to generate a cover letter that follows Swiss business standards and etiquette.

Key requirements:
- Maintain a formal yet engaging tone
- Follow Swiss letter structure (subject, greeting, body, closing)
- Ensure content is specific to the job and company
- Keep total length under 2 pages (approximately {max_total_length} characters)
- Write in {language} following local conventions
- Focus on relevance and conciseness
- Avoid generic phrases and clichés
- Show genuine interest in the position"""

SYSTEM_PROMPT_TEMPLATE_RECIPIENT_INFO = """You are an expert in extracting and formatting recipient information for Swiss business correspondence, especially for cover letters. Your task is to provide accurate, professional, and well-formatted recipient details to be used in formal applications.

Key requirements:
- Extract or determine the recipient information from the job description, adhering to Swiss business standards and ensuring the highest accuracy and relevance for use in a professional cover letter. Any incorrect, assumed, or invented information would negatively impact the quality of the letter.
- Ensure the output is the same output a person would write in a cover letter from what is written in the job description.
- Avoid using things like "not specified" or "not provided" in the output.
- The output must be the same output a person would write in a cover letter from what is written in the job description in {language}.
"""

COVER_LETTER_PROMPT_TEMPLATE = """Create a cover letter based on the following information:

Candidate Profile:
{user_profile}

Job Description:
{job_description}

Requirements:
1. Structure (Swiss format):
   - Clear subject line (max {subject_length} chars)
   - Professional greeting
   - Introduction: Why this position interests the candidate
   - Skills and experience: Match the job requirements
   - Motivation: Value proposition for the company
   - Conclusion: Call to action and availability
   - Professional closing: Include the culturally appropriate closing for Swiss standards in the specified language

2. Length constraints:
   - Each paragraph: Max {paragraph_length} chars
   - Total length: Max {max_total_length} chars
   - Ensure conciseness and clarity.

3. Style guidelines:
   - Be specific about achievements and skills
   - Use active voice
   - Demonstrate knowledge of the company and the role
   - Maintain a professional and confident tone
   - Highlight relevant experience
   - Show enthusiasm without being excessive
   - Avoid generic or repetitive phrases
   - *Closing*: Use a formal, culturally appropriate closing, such as:
     - In French: "Je vous prie d'agréer, Madame, Monsieur, mes salutations distinguées."
     - In German: "Mit freundlichen Grüßen."
     - In English: "Yours sincerely."
     - Ensure no placeholder names or candidate references are included.

4. Cultural considerations:
   - Follow Swiss business etiquette and conventions
   - Use formal language appropriate for {language}
   - Match local business communication standards

**DO NOT:**
- Include any placeholders such as [Your Name] or other personal identifiers. The candidate's name will be introduced externally.

The letter should feel personal, tailored, and professional—avoiding any indications of being AI-generated or overly generic."""

RECIPIENT_INFO_PROMPT = """
Extract or determine the recipient information from the job description, adhering to Swiss business standards and ensuring the highest accuracy and relevance for use in a professional cover letter. Any incorrect, assumed, or invented information would negatively impact the quality of the letter.

**Job Description:**
{job_description}

**Guidelines:**
1. **Company Name:**
   - Extract the company name exactly as mentioned in the job description.
   - If the name is very long (e.g., "Bureau d'ingénieur de prestige"), shorten it appropriately while preserving clarity and professionalism (e.g., "Bureau d'ingénieur").
   - Ensure the name fits within {recipient_line_length} characters and remains suitable for direct use in a cover letter.
   - If the company name is not specified, let the output be empty.

2. **Recipient:**
   - If a specific person is mentioned, include their name using the traditional format of the language of the job description.
     - e.g. In French: "Monsieur Dupont"
     - e.g. In German: "Herr Müller"
     - e.g. In English: "Ms. Smith"
   - Else if there is no specific person mentioned, use a neutral term appropriate to the language of the job description:
     - French: "À qui de droit"
     - German: "An wen es betrifft"
     - English: "To whom it may concern"
   - Avoid any invented names or placeholders under all circumstances.

3. **Address:**
   - Extract the full Swiss address exactly as mentioned, ensuring correct formatting:
     - Street and building number on one line. (e.g. "Rue de la Paix 123")
     - Postal code and city on the next line (e.g., "1009 Pully").
   - If no address is provided in the job description, leave this section blank without making assumptions or adding placeholders.

**Important Notes:**
- **Accuracy is critical:** Ensure that all extracted information is factually correct and directly usable in a professional context.
- **Do not invent or assume missing details:** If any information is unavailable, the output must reflect this by omitting the field entirely.
- Avoid repeating the same information or including placeholders like "[Company Name]" or "[Address]."
- Avoid using things like "not specified" or "not provided" in the output.
- The output must be the same output a person would write in a cover letter from what is written in the job description.

**Critical Reminders:**
- **Output must be optimized for use in a formal cover letter.**
- Do not compromise on accuracy or logic: any false or illogical information would never be written by a person into the recipient info of a cover letter.
- When in doubt, omit information rather than guess.

** expected output example:
- Nettoyeurs SA
- Monsieur Dupont
- Rue de la Paix 123
- 1009 Pully

** expected output example 2:
- À qui de droit

** expected output example 3:
- An wen es betrifft

** expected output example 4:
- Madame Müller
- Rue de l'Industrie 31
- 1000 Lausanne
"""

class RecipientInfoResponse(BaseModel):
    company_name: Optional[str]
    recipient: str
    address: Optional[List[str]]

class CoverLetterResponse(BaseModel):
    subject: str
    greeting: str
    introduction: str
    skills_experience: str
    motivation: str
    conclusion: str
    closing: str

class CoverLetterGenerator:
    def __init__(self, session: Session):
        self.session = session
        self.user_manager = UserManager(self.session)
        self.job_offer_manager = JobOfferManager(self.session)
        self.cover_letter_manager = CoverLetterManager(self.session)
        self.llm_client = LLMManager()

    def detect_language(self, text: str) -> str:
        try:
            return detect(text)
        except Exception as e:
            print(f"Language detection error: {e}")
            return "en"

    def validate_letter_length(self, cover_letter: CoverLetterResponse) -> bool:
        total_length = 0
        for field in cover_letter.__fields__:
            value = getattr(cover_letter, field)
            if isinstance(value, str):
                total_length += len(value)
        return total_length <= MAX_TOTAL_LENGTH

    async def generate_recipient_info(self, job_description: str) -> Optional[RecipientInfoResponse]:
        language = self.detect_language(job_description)

        prompt = RECIPIENT_INFO_PROMPT.format(
            job_description=job_description,
            recipient_line_length=MAX_RECIPIENT_LINE_LENGTH,
            language=language
        )

        try:
            completion = await self.llm_client.create_completion_async(
                response_model=RecipientInfoResponse,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE_RECIPIENT_INFO.format(
                        language=language
                    )},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings.DEFAULT_MAX_TOKENS
            )

            if self.validate_recipient_info(completion):
                return completion

        except Exception as e:
            print(f"Error generating recipient info: {e}")

        return self.get_default_recipient_info(language)

    def validate_recipient_info(self, recipient_info: RecipientInfoResponse) -> bool:
        if not recipient_info.recipient and not recipient_info.address and not recipient_info.company_name:
            return False

        def has_forbidden_chars(text: str) -> bool:
            forbidden_chars = r'[]{}()<>|\\~^°'
            return any(char in text for char in forbidden_chars)

        for info_list in [recipient_info.address,  recipient_info.recipient, recipient_info.company_name]:
            if info_list:
                for line in info_list:
                    if len(line) > MAX_RECIPIENT_LINE_LENGTH or has_forbidden_chars(line):
                        return False
        return True

    def get_default_recipient_info(self, language: str) -> RecipientInfoResponse:
        default_greetings = {
            "fr": "À qui de droit",
            "de": "An wen es betrifft",
            "en": "To whom it may concern",
            "it": "A chi di competenza"
        }
        return RecipientInfoResponse(
            company_name=None,
            recipient=default_greetings.get(language, default_greetings["en"]),
            address=None
        )

    async def generate_cover_letter(self, user_id: int, job_id: int) -> Optional[CoverLetter]:
        user = await self.user_manager.get_user_by_id(user_id)
        job_offer = await self.job_offer_manager.get_job_offer_by_id(job_id)

        if not user or not job_offer:
            print("User or job offer missing.")
            return None

        job_description = (
            f"Company name: {job_offer.company_name}\n"
            f"Company information: {job_offer.company_info}\n"
            f"Job title: {job_offer.job_title}\n"
            f"Job description: {job_offer.job_description}\n"
            f"Job location: {job_offer.work_location}"
        )

        language = self.detect_language(job_description)
        recipient_info = await self.generate_recipient_info(job_description)

        if not recipient_info:
            return None

        messages = self.prepare_messages(user, job_description, language)

        try:
            completion = await self.llm_client.create_completion_async(
                response_model=CoverLetterResponse,
                messages=messages,
                max_tokens=settings.DEFAULT_MAX_TOKENS,
                temperature=settings.DEFAULT_TEMPERATURE
            )

            if not completion or not self.validate_letter_length(completion):
                return None

            recipient_info_str = self.format_recipient_info(recipient_info)

            return await self.save_cover_letter(
                user_id, job_id, completion, recipient_info_str
            )

        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return None

    def prepare_messages(self, user, job_description: str, language: str) -> List[dict]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(
                max_total_length=MAX_TOTAL_LENGTH,
                language=language
            )},
            {"role": "user", "content": COVER_LETTER_PROMPT_TEMPLATE.format(
                user_profile=user.cv_text,
                job_description=job_description,
                subject_length=MAX_SUBJECT_LENGTH,
                paragraph_length=MAX_PARAGRAPH_LENGTH,
                max_total_length=MAX_TOTAL_LENGTH,
                language=language
            )}
        ]

        if user.reference_letter:
            messages.insert(1, {
                "role": "user",
                "content": REFERENCE_LETTER_STYLE_PROMPT.format(
                    reference_letter=user.reference_letter
                )
            })

        return messages

    def format_recipient_info(self, recipient_info: RecipientInfoResponse) -> str:
        lines = []
        if recipient_info.company_name:
            lines.append(recipient_info.company_name)
        if recipient_info.recipient:
            lines.append(recipient_info.recipient)
        if recipient_info.address:
            lines.extend(recipient_info.address)
        return "\n".join(filter(None, lines))

    async def save_cover_letter(self, user_id: int, job_id: int,
                              cover_letter_response: CoverLetterResponse,
                              recipient_info: str) -> CoverLetter:
        return await self.cover_letter_manager.add_cover_letter(
            user_id=user_id,
            job_id=job_id,
            subject=cover_letter_response.subject,
            greeting=cover_letter_response.greeting,
            introduction=cover_letter_response.introduction,
            skills_experience=cover_letter_response.skills_experience,
            motivation=cover_letter_response.motivation,
            conclusion=cover_letter_response.conclusion,
            closing=cover_letter_response.closing,
            recipient_info=recipient_info
        )