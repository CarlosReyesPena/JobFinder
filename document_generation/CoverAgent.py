import os
from document_generation.src.agent_cover_letter.crew import AgentCoverLetterCrew
from document_generation.src.agent_cover_letter.tools.JsonMergerTool import JsonMergerTool
from document_generation.src.agent_cover_letter.tools.PDFCoverTool import PDFCoverTool

class CoverLetterGenerator:
    def __init__(self, input_dir='document_generation\input', output_dir='document_generation\output'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.pdf_tool = PDFCoverTool(config_path=input_dir)

    def generate(self, candidate_data, job_offer, output_pdf_path):
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Save input data to files
        self._save_input_data(candidate_data, job_offer)

        # Run the crew to generate cover letter
        inputs = {
            "job_offer_details": job_offer,
            "candidate_cv": candidate_data
        }

        for _ in range(5):  # Try up to 5 times
            try:
                result = AgentCoverLetterCrew().crew().kickoff(inputs=inputs)
                print(result)
                success, message = self._merge_and_generate_pdf(output_pdf_path)
                print(message)
                if success:
                    return True, f"Cover letter generated successfully at {output_pdf_path}"
            except Exception as e:
                print(f"An error occurred while running the crew: {e}")

        return False, "Failed to generate cover letter after 5 attempts."

    def _save_input_data(self, candidate_data, job_offer):
        with open(os.path.join(self.input_dir, 'candidate_cv.txt'), 'w', encoding='utf-8') as f:
            f.write(candidate_data)
        with open(os.path.join(self.input_dir, 'job_offer.txt'), 'w', encoding='utf-8') as f:
            f.write(job_offer)

    def _merge_and_generate_pdf(self, output_pdf_path):
        json_files = [
            os.path.join(self.output_dir, 'cover_letter.json'),
            os.path.join(self.output_dir, 'RecipientAndSubject.json'),
            os.path.join(self.input_dir, 'CandidateAdress.json')
        ]
        json_merger_tool = JsonMergerTool(file_paths=json_files)
        try:
            # Merge JSON files
            merge_result = json_merger_tool._run()
            print(merge_result)

            # Generate PDF
            success, message = self.pdf_tool._run(
                os.path.join(self.output_dir, 'cover_letter.json'), 
                output_pdf_path
            )
            return success, message
        except Exception as e:
            print(f"Error in merge_and_generate_pdf: {str(e)}")
            return False, str(e)

# Usage example:
if __name__ == "__main__":
    generator = CoverLetterGenerator()
    candidate_data = "Your candidate data here..."
    job_offer = "Your job offer details here..."
    output_pdf_path = "path/to/your/output.pdf"
    
    success, message = generator.generate(candidate_data, job_offer, output_pdf_path)
    print(message)