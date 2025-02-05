from pydantic import BaseModel
from typing import List
from core.llm_manager import LLMManager
from core.settings import settings
from sqlmodel import Session
from data.managers.user_manager import UserManager

SYSTEM_PROMPT = """You are an expert job title generator. Your task is to analyze a user's CV and preferences to generate the 5 most relevant job titles that match their profile, experience level, and most importantly their career aspirations and preferences.

Key requirements:
- Generate 5 specific job titles based on:
  * The user's desired career direction and goals
  * The type of work they want to do
  * Their technical background and skills
  * Their industry experience and professional level
  * Their stated preferences and interests
- Only output actual job titles used by employers
- Consider regional job market conventions
- Maintain professional terminology
- Prioritize alignment with user's career aspirations
"""

KEYWORD_GENERATION_PROMPT = """Based on the following information, generate 5 relevant job titles:

User Profile:
{user_profile}

User Preferences:
{preferences}

Requirements:
1. Generate exactly 5 job titles that:
   - Strongly align with the type of work they want to do
   - Match their career goals and aspirations
   - Reflect their desired industry focus
   - Consider their stated preferences and interests
   - Leverage their technical skills and experience
   - Align with their career level

2. Format:
   - Return exactly 5 job titles
   - Use standard job titles found in real job postings
   - Consider {language} job market conventions
   - Example format: "Electronics Technician", "Embedded Systems Engineer", etc.

3. Guidelines:
   - Only output actual job titles used by employers
   - Focus on roles matching user's desired career direction
   - Ensure titles match both experience and aspirations
   - Prioritize titles that align with stated preferences and interests
   - Consider both current skills and desired growth areas
"""

class KeywordResponse(BaseModel):
    keywords: List[str]

class KeywordGenerator:
    def __init__(self, session: Session):
        self.session = session
        self.user_manager = UserManager(self.session)
        self.llm_client = LLMManager()


    async def generate_keywords(self, user_id: int, language: str = "en") -> KeywordResponse:
        """
        Generate job search keywords based on user's CV and preferences.

        Args:
            user_id: The ID of the user
            preferences: Additional preferences or focus areas specified by the user

        Returns:
            KeywordResponse containing generated keywords
        """
        user = await self.user_manager.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        prompt = KEYWORD_GENERATION_PROMPT.format(
            user_profile=user.cv_text,
            preferences=user.preferences,
            language=language
        )

        try:
            completion = await self.llm_client.create_completion_async(
                response_model=KeywordResponse,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )

            return completion

        except Exception as e:
            print(f"Error generating keywords: {e}")
            return None