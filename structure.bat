@echo off
setlocal enabledelayedexpansion

REM Vérifier si nous sommes dans un dépôt Git
if not exist ".git" (
    echo Ce script doit être exécuté dans un dépôt Git cloné.
    exit /b 1
)

REM Créer la structure de dossiers
mkdir config database scraping job_title_generator document_generation automation ui utils integrations user_profiles tests data logs
mkdir scraping\jobup scraping\indeed scraping\linkedin
mkdir data\job_descriptions

REM Créer les fichiers
type nul > main.py
type nul > config\__init__.py
type nul > config\settings.py
type nul > config\logging_config.py
type nul > database\__init__.py
type nul > database\jobup_database.py
type nul > scraping\__init__.py
type nul > scraping\base_scraper.py
type nul > scraping\base_applicator.py
type nul > scraping\jobup\__init__.py
type nul > scraping\jobup\jobup_scraper.py
type nul > scraping\jobup\jobup_applicator.py
type nul > scraping\indeed\__init__.py
type nul > scraping\indeed\indeed_scraper.py
type nul > scraping\indeed\indeed_applicator.py
type nul > scraping\linkedin\__init__.py
type nul > scraping\linkedin\linkedin_scraper.py
type nul > scraping\linkedin\linkedin_applicator.py
type nul > job_title_generator\__init__.py
type nul > job_title_generator\generate_search_terms.py
type nul > document_generation\__init__.py
type nul > document_generation\cover_letter_generator.py
type nul > automation\__init__.py
type nul > automation\job_application_automator.py
type nul > ui\__init__.py
type nul > ui\main_window.py
type nul > ui\job_list_view.py
type nul > ui\application_status_view.py
type nul > ui\document_viewer.py
type nul > ui\settings_panel.py
type nul > ui\region_selector.py
type nul > utils\__init__.py
type nul > utils\pdf_extractor.py
type nul > utils\file_operations.py
type nul > utils\error_handler.py
type nul > integrations\__init__.py
type nul > integrations\groq_api.py
type nul > user_profiles\__init__.py
type nul > user_profiles\profile_manager.py
type nul > user_profiles\user_preferences.py
type nul > tests\__init__.py
type nul > tests\test_scraping.py
type nul > tests\test_document_generation.py
type nul > tests\test_automation.py
type nul > tests\test_integrations.py
type nul > requirements.txt
type nul > README.md
type nul > .gitignore

REM Ajouter tous les fichiers au dépôt
git add .

REM Faire le commit
git commit -m "Add initial project structure"

REM Pousser les changements
git push

echo Structure du projet créée et poussée vers GitHub avec succès.
pause