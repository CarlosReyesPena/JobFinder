from typing import List, Optional, Type, Any, Dict
from pydantic import BaseModel, Field
from crewai_tools import BaseTool
import json

class JsonMergerToolInput(BaseModel):
    """Input schema for JsonMergerTool."""
    file_paths: List[str] = Field(
        ...,
        description="List of full paths to the JSON files to be merged. The first file will be the target for merging."
    )

class JsonMergerTool(BaseTool):
    name: str = "JSON Merger Tool"
    description: str = "A tool to merge multiple JSON files into the first file without modifying existing sections."
    args_schema: Type[BaseModel] = JsonMergerToolInput
    file_paths: List[str] = Field(..., description="List of full paths to the JSON files to be merged.")

    def _run(self) -> Any:
        if len(self.file_paths) < 2:
            return "Error: At least two file paths are required for merging."

        target_file = self.file_paths[0]
        source_files = self.file_paths[1:]

        try:
            # Read the target JSON file
            with open(target_file, 'r', encoding='utf-8') as file:
                target_data = json.load(file)

            # Merge data from source files
            for source_file in source_files:
                with open(source_file, 'r', encoding='utf-8') as file:
                    source_data = json.load(file)
                
                for key, value in source_data.items():
                    if key not in target_data:
                        target_data[key] = value

            # Write the merged data back to the target file
            with open(target_file, 'w', encoding='utf-8') as file:
                json.dump(target_data, file, indent=4, ensure_ascii=False)

            return f"Successfully merged JSON files into {target_file}"

        except json.JSONDecodeError as e:
            return f"Error: One of the files is not a valid JSON file. {str(e)}"
        except Exception as e:
            return f"Error processing the files: {str(e)}"