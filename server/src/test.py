from data.database import DatabaseManager
from services.job_automation.jobup.form_filler import FormFiller




def test_form_filler():
    db_manager = DatabaseManager()
    with db_manager.get_session() as session:

        # Step 6: Test FormFiller
        form_filler = FormFiller(session, user_id=2)
        try:
            form_filler.fill_apply_form("ebb2e551-3615-4353-ab72-eccd3cbbc61e")
            print("✅ Test successful: Form filled successfully.")
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_form_filler()
