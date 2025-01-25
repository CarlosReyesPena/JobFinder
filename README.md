# JobFinder

Automated job application platform with AI-powered features. Currently supporting job boards in Switzerland, with more platforms coming soon.

## Features

- Job scraping from multiple platforms (LinkedIn coming soon)
- AI-powered cover letter generation
- Automated PDF creation
- Form auto-filling
- Document management (CV, letters)
- CLI interface

## Requirements

- Python 3.10+
- OpenAI API key
- Groq API key

## Quick Start

```bash
# Clone repository
git clone https://github.com/CarlosReyesPena/JobFinder.git
cd autoapply

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Create .env file
echo "OPENAI_API_KEY=your_key
GROQ_API_KEY=your_key" > .env

# Run application
python src/mainlocal.py
```

## Project Structure

```
server/
├── src/
│   ├── core/           # Configuration
│   ├── data/           # Database
│   ├── services/       # Business logic
│   └── local/          # CLI interface
├── requirements.txt
└── README.md
```

## Built With

- SQLModel - ORM and database
- Playwright - Web automation
- OpenAI/Groq - Content generation
- ReportLab - PDF generation
- FastAPI - REST API (in development)

## Roadmap

- IA job offers seeking optimisation
- LinkedIn integration
- Indeed integration
- Web interface
- Application tracking

## Notes

- First login requires manual authentication
- Applications are stored locally
- Review generated content before sending
- Respect platform terms of service
