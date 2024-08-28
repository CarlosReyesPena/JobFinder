from crewai_tools import BaseTool
from typing import Any

class WordCountTool(BaseTool):
    name: str = "Word Count Tool"
    description: str = (
        "A tool to count the number of words in a given text. "
    )

    def _run(self, text: str) -> Any:
        # Split the text into words and count them
        word_count = len(text.split())
        
        # Prepare the response
        response = f"The provided text contains {word_count} words."
        
        return response