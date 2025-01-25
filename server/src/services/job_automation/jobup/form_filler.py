from playwright.sync_api import sync_playwright
from sqlmodel import Session
from data.managers.apply_form_manager import ApplyFormManager
from data.managers.document_manager import DocumentManager
from data.managers.cover_letter_manager import CoverLetterManager
from data.managers.job_offer_manager import JobOfferManager
from .login import BrowserSession
from langdetect import detect
import tempfile
from pathlib import Path
import os
import time
import logging


class FormChecker:
    def __init__(self, page, log_level=logging.INFO):
        self.page = page
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

    def check_text_field(self, selector, expected_value):
        """Checks (and corrects if needed) the value of a text field."""
        try:
            if self.page.is_visible(selector):
                current_value = self.page.input_value(selector)
                if current_value != expected_value:
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Error while checking field {selector}: {e}")
            return False

    def check_gender_selection(self, expected_gender):
        """Checks if gender is correctly selected."""
        try:
            if not (self.page.is_visible("button[value='male']") or self.page.is_visible("button[value='female']")):
                return True
            # Check if expected button is pressed
            if expected_gender == 'male':
                return self.page.is_visible("button[value='male'][aria-pressed='true']")
            return self.page.is_visible("button[value='female'][aria-pressed='true']")
        except Exception as e:
            self.logger.error(f"Error while checking gender: {e}")
            return False

    def check_availability_selection(self, expected_value: int):
        """Checks selection in availability dropdown."""
        try:
            if not self.page.is_visible("#availability-trigger"):
                return True

            # Open dropdown to read selection
            self.page.click("#availability-trigger")
            expected_index = abs(expected_value - 6)
            selector = f"div[data-cy='select-item-{expected_index}'][aria-selected='true']"
            is_selected = self.page.is_visible(selector, timeout=1000)
            # Close dropdown
            self.page.click("#availability-trigger")
            return is_selected
        except Exception as e:
            self.logger.error(f"Error while checking availability: {e}")
            return False

    def check_work_permit(self, expected_index: int):
        """Checks work permit selection."""
        try:
            if not self.page.is_visible("#workPermit-trigger"):
                return True

            self.page.click("#workPermit-trigger")
            selector = f"div[aria-posinset='{expected_index}'][aria-selected='true']"
            is_selected = self.page.is_visible(selector, timeout=1000)
            # Close dropdown
            self.page.click("#workPermit-trigger")
            return is_selected
        except Exception as e:
            self.logger.error(f"Error while checking work permit: {e}")
            return False

    def check_requirements_answered(self):
        """Checks if all requirements have been answered."""
        try:
            if not self.page.is_visible("div[data-cy='requirements-input']"):
                return True

            requirement_items = self.page.query_selector_all("div[data-cy^='requirement-']")
            for index, _ in enumerate(requirement_items):
                yes_button = self.page.query_selector(
                    f"div[data-cy='requirement-{index}'] button[value='true'][aria-pressed='true']"
                )
                no_button = self.page.query_selector(
                    f"div[data-cy='requirement-{index}'] button[value='false'][aria-pressed='true']"
                )
                # If neither "yes" nor "no" is selected, it's missing
                if not (yes_button or no_button):
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Error while checking requirements: {e}")
            return False

    def check_document_uploaded(self, doc_name: str):
        """Checks if a document is present (visible) on the page."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=30000)
            return self.page.is_visible(f"text={doc_name}")
        except Exception as e:
            self.logger.error(f"Error while checking document {doc_name}: {e}")
            return False

    def wait_for_all_uploads(self, uploaded_files, timeout=5000):
        """
        Waits and checks that all files are uploaded.

        Args:
            page: The Playwright Page object
            uploaded_files: Dict with expected files by type:
                        {"cv": [cv_name], "motivation": [letter_name], "other": [other_doc_names]}
            timeout: Maximum wait time in milliseconds

        Returns:
            tuple: (bool, list) - (success, list of missing files)
        """
        progress_selector = "div.bg_brand\\.30[style*='--progress']"
        start_time = time.time()
        missing_files = []

        try:
            # While there's an upload in progress or timeout not reached
            while (time.time() - start_time) * 1000 < timeout:
                missing_files = []

                # Check if there's an upload in progress
                upload_in_progress = self.page.is_visible(progress_selector)
                if upload_in_progress:
                    self.page.wait_for_timeout(500)
                    continue

                # Check uploaded files in page
                for file in uploaded_files:
                    if (file["name"] or file["bytes"]) == None:
                        raise ValueError("File name or bytes is None")
                    elif file["type"] == None:
                        file["type"] = "other"
                    if not self.check_document_uploaded(file["name"]):
                        missing_files.append(file)

                # If all files present and no upload in progress, we can exit
                if not missing_files and not upload_in_progress:
                    return True, []

                # Otherwise, keep waiting
                self.page.wait_for_timeout(500)


            return False, missing_files

        except Exception as e:
            print(f"Error while waiting for uploads: {e}")
            return False, missing_files

    def verify_all_fields(self, expected_data, expected_files):
        """
        Checks all fields (text, dropdown, etc.) and presence of files.

        Returns:
           - missing_fields (list): list of missing fields
           - missing_files (list): list of missing (document_type, filename) tuples
        """
        missing_fields = []
        missing_files = []

        # Basic fields
        base_fields = {
            "input[name='firstname']": expected_data.get("firstname", ""),
            "input[name='lastname']":  expected_data.get("lastname", ""),
            "input[name='email']":     expected_data.get("email", ""),
            "input[name='phone']":     expected_data.get("phone", ""),
            "input[name='zipCode']":   expected_data.get("zipcode", "")
        }

        # Check each text field
        for selector, value in base_fields.items():
            if self.page.is_visible(selector) and not self.check_text_field(selector, value):
                missing_fields.append(selector)

        # Gender
        if (self.page.is_visible("button[value='male']") or self.page.is_visible("button[value='female']")):
            if not self.check_gender_selection(expected_data.get("gender", "")):
                missing_fields.append("gender")

        # Availability
        if self.page.is_visible("#availability-trigger"):
            availability = int(expected_data.get("availability", 0))
            if not self.check_availability_selection(availability):
                missing_fields.append("availability")

        # Work permit
        if self.page.is_visible("#workPermit-trigger"):
            work_permit = int(expected_data.get("work_permit", 1))
            if not self.check_work_permit(work_permit):
                missing_fields.append("work_permit")

        # Requirements
        if self.page.is_visible("div[data-cy='requirements-input']"):
            if not self.check_requirements_answered():
                missing_fields.append("requirements")

        # Check uploaded files in page
        for file in expected_files:
            if (file["name"] or file["bytes"]) == None:
                raise ValueError("File name or bytes is None")
            elif file["type"] == None:
                file["type"] = "other"
            if not self.check_document_uploaded(file["name"]):
                missing_files.append(file)

        return missing_fields, missing_files


class FormFiller:
    def __init__(self, session: Session, user_id, log_level=logging.INFO):
        self.user_id = user_id
        self.session = session
        self.browser_session = BrowserSession(session, user_id)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

    def _sanitize_filename(self, filename: str) -> str:
        """Cleans filename of forbidden characters."""
        # Characters forbidden in most filesystems
        forbidden_chars = ' <>:"/\\|?*'
        # Replace forbidden chars with underscore
        for char in forbidden_chars:
            filename = filename.replace(char, '_')
        # Remove spaces at start and end
        filename = filename.strip()
        # Replace multiple spaces with single underscore
        filename = '_'.join(filter(None, filename.split()))
        return filename

    def safe_click(self, page, selector, timeout=5000):
        """Click with error handling."""
        try:
            page.wait_for_selector(selector, timeout=timeout)
            page.click(selector)
        except Exception as e:
            self.logger.error(f"Unable to click on {selector}: {e}")

    def safe_file_cleanup(self, temp_file, max_attempts=3, delay=1):
        """Attempts to delete a temporary file."""
        for attempt in range(max_attempts):
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    return True
            except PermissionError:
                self.logger.warning(f"File {temp_file} still in use, attempt {attempt + 1}/{max_attempts}")
                time.sleep(delay)
        return False

    def create_form_data(self, firstname, lastname, email, phone, zipcode, gender, availability, work_permit, auto_answer_requirements):
        """
        Creates a new form_data record for the user in database.
        Example of form_data:
            {
                "firstname": "Carlos",
                "lastname": "Doe",
                "email": "carlos@example.com",
                "phone": "123456789",
                "zipcode": "1000",
                "gender": "male",
                "availability": "0",
                "work_permit": "1",
                "auto_answer_requirements": "true"
            }
        """
        apply_manager = ApplyFormManager(self.session)
        form_data = {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "phone": phone,
            "zipcode": zipcode,
            "gender": gender,
            "availability": availability,
            "work_permit": work_permit,
            "auto_answer_requirements": auto_answer_requirements
        }
        apply_manager.add_apply_form(user_id=self.user_id, site_name="JobUp", form_data=form_data)

    def check_and_handle_login(self, page) -> bool:
        """
        Checks if login is needed and handles login if necessary.
        Returns True if session is valid, False otherwise.
        """
        try:
            if page.is_visible("button[data-cy='login-teaser-trigger']"):
                self.logger.info("Login button detected (teaser), login required...")
                self.safe_click(page, "button[data-cy='login-teaser-trigger']")
                return True

            if page.is_visible("button[data-cy='login-link']"):
                self.logger.info("Login button detected (navbar), restarting session...")
                success, message = self.browser_session.launch_browser_session()
                if not success:
                    self.logger.error(f"Login failed: {message}")
                    return False
                return True

            self.logger.info("No login button detected, session already active.")
            return True

        except Exception as e:
            self.logger.error(f"Error while checking login: {e}")
            return False

    def select_gender(self, page, gender):
        """Selects gender if field is present."""
        try:
            if page.is_visible("button[value='male']") or page.is_visible("button[value='female']"):
                if gender == 'male':
                    self.safe_click(page, "button[value='male']")
                elif gender == 'female':
                    self.safe_click(page, "button[value='female']")
        except Exception as e:
            self.logger.error(f"Error while selecting gender: {e}")

    def select_availability(self, page, availability: int):
        """Selects availability from list if possible."""
        try:
            if page.is_visible("#availability-trigger"):
                if availability < 0 or availability > 6:
                    raise ValueError("Availability out of range (0-6)")
                item_availability = abs(availability - 6)

                self.safe_click(page, "#availability-trigger")
                selector = f"div[data-cy='select-item-{item_availability}']"
                self.safe_click(page, selector)
        except Exception as e:
            self.logger.error(f"Error while selecting availability: {e}")

    def select_work_permit(self, page, permit_index: int):
        """Selects work permit from list if possible."""
        try:
            if page.is_visible("#workPermit-trigger"):
                if permit_index < 1 or permit_index > 10:
                    raise ValueError("Work permit index out of range (1-10)")
                self.safe_click(page, "#workPermit-trigger")
                selector = f"#workPermit div[aria-posinset='{permit_index}']"
                self.safe_click(page, selector)
        except Exception as e:
            self.logger.error(f"Error while selecting work permit: {e}")

    def handle_requirements(self, page, auto_answer: bool = True):
        """
        Automatically (or not) answers form requirements.
        """
        try:
            if page.is_visible("div[data-cy='requirements-input']"):
                requirement_items = page.query_selector_all("div[data-cy^='requirement-']")
                for index, _ in enumerate(requirement_items):
                    if auto_answer:
                        # Click "yes" button
                        btn_selector = f"div[data-cy='requirement-{index}'] button[value='true']"
                        self.safe_click(page, btn_selector)
        except Exception as e:
            self.logger.error(f"Error while handling requirements: {e}")

    def fill_missing_fields(self, page, form_data, missing_fields):
        """Fills still missing or incorrect fields."""
        for field in missing_fields:
            try:
                # Gender
                if field == "gender":
                    self.select_gender(page, form_data.get("gender"))

                # Availability
                elif field == "availability":
                    self.select_availability(page, int(form_data.get("availability", 0)))

                # Work permit
                elif field == "work_permit":
                    self.select_work_permit(page, int(form_data.get("work_permit", 1)))

                # Requirements
                elif field == "requirements":
                    auto_answer = form_data.get("auto_answer_requirements") in ["True", "true"]
                    self.handle_requirements(page, auto_answer)

                # Text fields
                elif field.startswith("input[name="):
                    # ex: "input[name='firstname']"
                    field_name = field.split("'")[1]
                    value = form_data.get(field_name, "")
                    page.fill(field, value)

                page.wait_for_load_state("networkidle", timeout=5000)

            except Exception as e:
                self.logger.error(f"Error while filling {field}: {e}")

    def fill_missing_files(self, page, files_to_upload) -> list:
        """
        Handles upload of missing files.

        Args:
            page: The Playwright page
            files_to_upload: List of tuples (file_type, filename, content)

        Returns:
            list: List of created temporary file paths
        """
        tempfiles = []
        try:
            # Determine available document sections
            available_sections = {
                "cv": page.is_visible("div[data-cy='document-section-head-cv']"),
                "motivation": page.is_visible("div[data-cy='document-section-head-motivation']"),
                "other": page.is_visible("div[data-cy='document-section-head-other']")
            }

            # Reorganize files according to available sections
            for file in files_to_upload:
                if file["type"] == "cv":
                    if not available_sections["cv"]:
                        file["type"] = "other"
                elif file["type"] == "motivation":
                    if not available_sections["motivation"]:
                        file["type"] = "other"

            # Upload reorganized files
            for file in files_to_upload:
                section_head = f"div[data-cy='document-section-head-{file["type"]}']"
                section_input = f"div[data-cy='document-section-{file["type"]}'] input[type='file']"

                temp_path = self.upload_bytes_to_field(
                    page, file["name"], file["bytes"],
                    section_head,
                    section_input
                )
                tempfiles.append(temp_path)

            return tempfiles

        except Exception as e:
            self.logger.error(f"Error while uploading files: {e}")
            # Cleanup temporary files in case of error
            for temp_file in tempfiles:
                self.safe_file_cleanup(temp_file)
            raise

    def upload_bytes_to_field(self, page, filename: str, file_bytes: bytes, selector_button: str, selector_file: str):
        """
        Uploads a file from bytes to an input[type='file'] field.
        Returns created temporary file path.
        """
        temp_dir = Path(tempfile.gettempdir())
        temp_file_path = temp_dir / filename

        try:
            try:
                if temp_file_path.exists():
                    self.logger.info(f"Temporary file {temp_file_path} already exists, deleting it.")
                    temp_file_path.unlink()
            except Exception as e:
                self.logger.error(f"Error while deleting temporary file {temp_file_path}: {e}")

            with open(temp_file_path, 'wb') as f:
                f.write(file_bytes)
                f.flush()
                os.fsync(f.fileno())

            page.wait_for_selector(selector_button, state="visible", timeout=10000)
            self.safe_click(page, selector_button)

            page.wait_for_selector(selector_file, state="attached", timeout=10000)
            page.set_input_files(selector_file, str(temp_file_path))

            # Wait for upload to complete (progress bar)
            #progress_selector = "div.bg_brand\\.30[style*='--progress']"
            #page.wait_for_selector(progress_selector, state="detached", timeout=30000)

            self.logger.info(f"Upload completed: {filename}")
            return temp_file_path

        except Exception as e:
            self.logger.error(f"Error while uploading {filename}: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise

    def click_submit_button(self, page, direct_apply: bool = False):
        """
        Clicks submit button (direct_apply = True => "Apply" button,
        otherwise "Save" button for example).
        """
        try:
            if direct_apply:
                page.click(".ml_s0 > .ai_center")  # selector for "apply" button (example)
                self.logger.info("Click on application submit button.")
            else:
                page.click(".d_inline-flex > .ai_center")  # selector for "save" button (example)
                self.logger.info("Click on application save button.")
            page.wait_for_timeout(1000)
        except Exception as e:
            self.logger.error(f"Error while clicking submit button: {e}")
            raise

    def fill_apply_form(self, external_id, direct_apply: bool = False):
        """
        Loads form from database (via ApplyFormManager),
        fills fields, checks what's missing and uploads documents.
        Retries up to max_attempts before raising exception.
        """
        apply_manager = ApplyFormManager(self.session)
        apply_form = apply_manager.get_apply_form_by_user_and_site(self.user_id, "JobUp")

        if not apply_form:
            raise ValueError("No form found for this user.")

        # Get data from database
        form_data = apply_form.form_data
        doc_manager = DocumentManager(self.session)
        cover_letter_manager = CoverLetterManager(self.session)
        job_offer_manager = JobOfferManager(self.session)

        cv = doc_manager.get_user_documents(self.user_id, "CV")
        other_docs = doc_manager.get_user_documents(self.user_id, "others")

        job_id = job_offer_manager.get_id_by_external_id(external_id)
        cover_letter = cover_letter_manager.get_cover_letter_by_user_and_job_id(self.user_id, job_id)
        letter_bytes = cover_letter.pdf_data if cover_letter else None

        job_offer = job_offer_manager.get_job_offer_by_external_id(external_id)

        letter_prefixes = {
            'fr': 'Lettre',
            'de': 'Bewerbungsschreiben',
            'it': 'Lettera',
            'rm': 'Brev'
        }
        prefix_letter = letter_prefixes.get(detect(job_offer.job_description), 'Letter')

        # Prepare list of files to upload with their bytes
        files_to_upload = []

        # Add CV if exists
        if cv:
            files_to_upload.append({
                "type": "cv",
                "name": self._sanitize_filename(cv[0].name),
                "bytes": cv[0].content
            })


        if letter_bytes:
            if job_offer.company_name:
                files_to_upload.append({
                    "type": "motivation",
                    "name": f"{prefix_letter}_{self._sanitize_filename(job_offer.company_name)}.pdf",
                    "bytes": letter_bytes
                })
            else:
                files_to_upload.append({
                    "type": "motivation",
                    "name": f"{prefix_letter}_{self._sanitize_filename(form_data.get('firstname'))}_{self._sanitize_filename(form_data.get('lastname'))}.pdf",
                    "bytes": letter_bytes
                })

        # Add other documents if they exist
        if other_docs:
            for doc in other_docs:
                files_to_upload.append({
                    "type": "other",
                    "name": self._sanitize_filename(doc.name),
                    "bytes": doc.content
                })

        max_attempts = 3
        current_attempt = 0

        with sync_playwright() as p:
            context = self.browser_session.get_browser_context(p, headless=True)
            page = context.new_page()
            form_checker = FormChecker(page)

            while current_attempt < max_attempts:
                current_attempt += 1
                self.logger.info(f"Attempt {current_attempt}/{max_attempts} to fill JobUp form.")
                tempfiles = []

                try:
                    page.goto(f"https://www.jobup.ch/fr/application/create/{external_id}/", wait_until="load")
                    self.logger.info("Navigation to JobUp form.")

                    # Check if job posting has expired
                    if page.is_visible("img[data-cy='application-expired-vacancy']"):
                        self.logger.info("Job posting has expired, deleting offer and associated documents")
                        if job_offer:
                            job_offer_manager.delete_job_offer(job_offer.external_id)
                            if cover_letter:
                                cover_letter_manager.delete_cover_letter(cover_letter.id)
                        return

                    # Check login
                    if not self.check_and_handle_login(page):
                        self.logger.warning("Login failed, retrying...")
                        continue

                    # Accept cookies if needed
                    if page.is_visible("button[data-cy='cookie-consent-modal-primary']"):
                        self.safe_click(page, "button[data-cy='cookie-consent-modal-primary']")

                    missing_fields, missing_files = form_checker.verify_all_fields(form_data, files_to_upload)


                    if missing_files:
                        tempfiles = self.fill_missing_files(page, missing_files)

                    if missing_fields:
                        self.fill_missing_fields(page, form_data, missing_fields)

                    # Wait for all uploads to complete
                    form_checker.wait_for_all_uploads(files_to_upload)

                    missing_fields, missing_files = form_checker.verify_all_fields(form_data, files_to_upload)

                    if not missing_fields and not missing_files:
                        self.logger.info("Form completed successfully, submitting application.")
                        self.click_submit_button(page, direct_apply)
                        page.wait_for_load_state("networkidle", timeout=30000)

                        for temp_file in tempfiles:
                            if not self.safe_file_cleanup(temp_file):
                                self.logger.error(f"Unable to delete {temp_file}")

                        break

                except Exception as e:
                    self.logger.error(f"Error during attempt {current_attempt}: {str(e)}")
                    # If it's the last attempt, raise the exception
                    if current_attempt >= max_attempts:
                        raise
                    # Otherwise, retry
                finally:
                    # Cleanup if exiting due to error
                    for temp_file in tempfiles:
                        self.safe_file_cleanup(temp_file)
