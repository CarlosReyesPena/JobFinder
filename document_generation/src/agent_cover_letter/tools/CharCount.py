from crewai_tools import BaseTool
from typing import Any

class CharacterCountTool(BaseTool):
    name: str = "Character Count Tool"
    description: str = (
        "A tool to count the number of characters in a given text."
    )

    def _run(self, text: str) -> Any:
        # Count the number of characters in the text
        character_count = len(text)
        
        # Prepare the response
        response = f"The provided text contains {character_count} characters."
        
        return response
