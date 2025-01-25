from .base_menu import BaseMenu
from data.managers.job_offer_manager import JobOfferManager
from data.managers.cover_letter_manager import CoverLetterManager
from data.managers.application_manager import ApplicationManager
from data.managers.apply_form_manager import ApplyFormManager
from services.job_automation.jobup.login import launch_browser_and_save_session
from services.job_automation.jobup.auto_apply import AutoApply
from services.job_automation.jobup.form_filler import FormFiller
from .scraping.menu import ScrapingMenu

class JobUpMenu(BaseMenu):
    def __init__(self, session):
        super().__init__(session)
        self.job_manager = JobOfferManager(session)
        self.apply_form_manager = ApplyFormManager(session)
        self.scraping_menu = ScrapingMenu(session)
        self.application_manager = ApplicationManager(session)
        self.cover_letter_manager = CoverLetterManager(session)

    def display(self):
        while True:
            self.print_header("JobUp Operations")
            print("1. Configure and Start Scraping")
            print("2. Login to JobUp")
            print("3. Create apply form")
            print("4. Delete all apply form")
            print("5. Apply to Job")
            print("6. List Job Offers")
            print("7. Delete Job Offers")
            print("8. Reset postulation data")
            print("9. Back to Main Menu")

            choice = input("\nEnter your choice (1-5): ")

            if choice == '1':
                self.scraping_menu.display()
            elif choice == '2':
                self.login_jobup()
            elif choice == '3':
                self.create_apply_form()
            elif choice == '4':
                self.delete_apply_forms()
            elif choice == '5':
                self.apply_to_job()
            elif choice == '6':
                self.list_jobs()
            elif choice == '7':
                self.delete_job_offers()
            elif choice == '8':
                self.reset_postulation_data()
            elif choice == '9':
                break
            else:
                print("\nInvalid choice!")
                self.wait_for_user()

    def login_jobup(self):
        try:
            user_id = int(input("\nEnter user ID for login: "))
            print(f"\nLaunching browser for user {user_id}...")
            message = launch_browser_and_save_session(user_id, self.session)
            print(f"Login result: {message}")
        except ValueError:
            print("Invalid user ID")
        self.wait_for_user()

    def delete_job_offers(self):
        self.job_manager.delete_all_job_offers()
        print("\nAll job offers have been deleted.")
        self.wait_for_user()

    def delete_apply_forms(self):
        self.apply_form_manager.delete_all_apply_forms()
        print("\nAll apply form have been deleted.")
        self.wait_for_user()

    def reset_postulation_data(self):
        self.application_manager.delete_all_applications()
        self.cover_letter_manager.delete_all_cover_letters()
        print("\nAll postulation data has been reset.")
        self.wait_for_user()

    def apply_to_job(self):
        try:
            user_id = int(input("\nEnter user ID: "))
            apply_number = int(input("Enter the number of applications to process: "))
            AutoApply(self.session, user_id).process_job_offers(apply_number)
        except ValueError:
            print("Invalid ID format")
        except Exception as e:
            print(f"Error during application: {e}")
        self.wait_for_user()
    def create_apply_form(self):
        user_id = int(input("\nEnter user ID: "))
        form_filler = FormFiller(self.session, user_id)
        # Form data dictionary structure:
        # form_data = {
        #     "firstname": "Carlos",        # User's first name
        #     "lastname": "Doe",            # User's last name
        #     "email": "carlos@example.com",# User's email address
        #     "phone": "123456789",         # User's phone number
        #     "zipcode": "1000",            # Postal code
        #     "gender": "male",             # Gender ('male' or 'female')
        #     "availability": "0",          # Waiting months, maximum 6
        #     "work_permit": "1",           # Work permit index (1-10)
        #     "auto_answer_requirements": "true"  # Boolean as string for JSON compatibility
        # }

        # Work permit index correspondence
                # 1 - Swiss Nationality
                # 2 - Residence Permit - B Permit
                # 3 - Settlement Permit - C Permit
                # 4 - Cross-border Commuter Permit - G Permit
                # 5 - Provisionally Admitted Foreigners - F Permit
                # 6 - Asylum Seekers - N Permit
                # 7 - Short-term Residence Permit - L Permit
                # 8 - EU Citizen
                # 9 - Protection Status - S Permit
                # 10 - No Authorization
        firstname = input("Enter your first name: ")
        lastname = input("Enter your last name: ")
        email = input("Enter your email: ")
        phone = input("Enter your phone number: ")
        zipcode = input("Enter your zipcode: ")
        gender = input("Enter your gender: ")
        availability = input("Enter your availability (months, max 6): ")
        print("""
                Available Work Permits:
                --------------------
                1 - Swiss Nationality
                2 - Residence Permit - B Permit
                3 - Settlement Permit - C Permit
                4 - Cross-border Commuter Permit - G Permit
                5 - Provisionally Admitted Foreigners - F Permit
                6 - Asylum Seekers - N Permit
                7 - Short-term Residence Permit - L Permit
                8 - EU Citizen
                9 - Protection Status - S Permit
                10 - No Authorization
    """)
        work_permit = input("Enter your work permit index: ")
        auto_answer_requirements = "true"
        form_filler.create_form_data(firstname=firstname, lastname=lastname, email=email, phone=phone,
                                     zipcode=zipcode, gender=gender, availability=availability, work_permit=work_permit,
                                     auto_answer_requirements=auto_answer_requirements)
    def list_jobs(self):
        jobs = self.job_manager.get_job_offers()
        print("\nJob Offers:")
        for job in jobs:
            print(f"\nID: {job.id}")
            print(f"Title: {job.job_title}")
            print(f"Company: {job.company_name}")
            print(f"Location: {job.work_location}")
            print(f"Quick Apply: {'Yes' if job.quick_apply else 'No'}")
            print("-" * 50)
        self.wait_for_user()