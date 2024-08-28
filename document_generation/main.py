#!/usr/bin/env python
import sys
import os
from agent_cover_letter.crew import AgentCoverLetterCrew
from agent_cover_letter.tools.JsonMergerTool import JsonMergerTool
from agent_cover_letter.tools.PDFCoverTool import PDFCoverTool


def load_file_content(file_path):
    """
    Load content from a text file using UTF-8 encoding.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def merge_and_generate_pdf(file_paths=["output/cover_letter.json","output/RecipientAndSubject.json","output/sender.json"]):
    pdf_tool = PDFCoverTool(config_path="input")
    json_merger_tool = JsonMergerTool(file_paths=file_paths)
    try:
        # Merge JSON files
        merge_result = json_merger_tool._run()
        print(merge_result)

        # Generate PDF
        success, message = pdf_tool._run("output/cover_letter.json", "output/cover_letter.pdf")
        return success, message
    except Exception as e:
        print(f"Error in merge_and_generate_pdf: {str(e)}")
        return False, str(e)

def main():

    job_offer_details = load_file_content('input/job_offer.txt')
    candidate_cv = load_file_content('input/candidate_cv.txt')

    inputs = {
        "job_offer_details": job_offer_details,
        "candidate_cv": candidate_cv
    }

    # for loop that try 5 times to run the crew
    for i in range(5):
        try:
            result = AgentCoverLetterCrew().crew().kickoff(inputs=inputs)
            print(result)
            success, message = merge_and_generate_pdf()
            print(message)
            if success:
                break
        except Exception as e:
            print(f"An error occurred while running the crew: {e}")
            if i == 4:
                print("Failed to run the crew after 5 attempts.")
                break
        input("Press Enter to continue...")

if __name__ == "__main__":
    main()