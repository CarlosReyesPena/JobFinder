import os
import sqlite3
import time
import gc
from datetime import datetime

from database.JobFinderDatabase import User, UserDocument, CoverLetter, JobOffer, SavedJob, UserSiteCredentials, UserApplication, UserJobPreference

def setup_test_database(test_db_path):
    """Initialize the test database by ensuring it's clean."""
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def teardown_test_database(test_db_path, test_files):
    """Clean up the test database and any test files."""
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
    # Ensure all database operations have completed before deleting
    time.sleep(1)
    gc.collect()
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except PermissionError as e:
            print(f"Error: Could not delete test database file: {e}")

def test_user_creation(user):
    """Test user creation and fetching."""
    print("\nTesting User Creation:")
    user_ids = []
    for i in range(3):
        user_id = user.create(f"user{i}", f"user{i}@example.com", f"password_hash{i}")
        assert user_id is not None, f"Failed to create user {i}"
        user_ids.append(user_id)
        print(f"User {i} created with ID: {user_id}")

    # Fetch and verify users
    for user_id in user_ids:
        fetched_user = user.get(user_id)
        assert fetched_user is not None, f"Failed to fetch user with ID {user_id}"
        print(f"Fetched user: {fetched_user}")

    return user_ids

def test_user_update(user, user_ids):
    """Test updating a user's email."""
    print("\nTesting User Update:")
    user.update(user_ids[0], email="updated_email@example.com")
    updated_user = user.get(user_ids[0])
    assert updated_user[2] == "updated_email@example.com", "User email update failed"
    print(f"User updated: {updated_user}")

def test_user_list_all(user):
    """Test listing all users."""
    print("\nTesting User List All:")
    all_users = user.list_all()
    assert len(all_users) == 3, "User list count mismatch"
    print(f"All users: {all_users}")

def test_document_creation(user_document, user_ids):
    """Test document creation for users."""
    print("\nTesting Document Creation:")
    doc_ids = {user_id: [] for user_id in user_ids}
    test_files = []
    for user_id in user_ids:
        for j in range(3):
            file_name = f"test_doc_{user_id}_{j}.txt"
            test_files.append(file_name)
            with open(file_name, "w") as f:
                f.write(f"Ceci est le document {j} de l'utilisateur {user_id}")
            doc_id = user_document.create_from_file(user_id, f"Document{j}", file_name)
            assert doc_id is not None, f"Failed to create document {j} for user {user_id}"
            doc_ids[user_id].append(doc_id)
            print(f"Document {j} created for user {user_id} with ID: {doc_id}")

    return doc_ids, test_files

def test_document_fetch_and_update(user_document, user_ids, doc_ids):
    """Test fetching and updating documents."""
    print("\nTesting Document Fetch and Update:")
    for user_id in user_ids:
        all_docs = user_document.get_all_for_user(user_id)
        assert len(all_docs) == 3, f"Document count mismatch for user {user_id}"
        print(f"User {user_id} has {len(all_docs)} documents")
        for doc in all_docs:
            print(f"Document ID: {doc[0]}, Type: {doc[2]}, Name: {doc[4]}, Content: {doc[3].decode('utf-8')}")

    # Update a document
    first_doc_id = doc_ids[user_ids[0]][0]
    user_document.update(first_doc_id, document_type="UpdatedType")
    updated_doc = user_document.get(first_doc_id)
    assert updated_doc[2] == "UpdatedType", "Document type update failed"
    print(f"Updated document: {updated_doc}")

def test_cover_letter_creation_and_update(cover_letter, user_ids, job_offer_ids):
    """Test cover letter creation and updates."""
    print("\nTesting Cover Letter Creation and Update:")
    cover_letter_ids = []
    for i, user_id in enumerate(user_ids):
        job_offer_id = job_offer_ids[i % len(job_offer_ids)]  # Cycle through job offers
        letter_id = cover_letter.create_from_file(user_id, job_offer_id, f"test_doc_{user_id}_0.txt", "v1")
        assert letter_id is not None, f"Failed to create cover letter for user {user_id}"
        cover_letter_ids.append(letter_id)
        fetched_letter = cover_letter.get(letter_id)
        assert fetched_letter is not None, f"Failed to fetch cover letter with ID {letter_id}"
        print(f"Fetched letter: {fetched_letter}")
        print(f"Letter content: {fetched_letter[3].decode('utf-8')}")

    # Update a cover letter
    cover_letter_id_to_update = cover_letter_ids[0]
    print(f"Before update: {cover_letter.get(cover_letter_id_to_update)}")

    # Perform the update
    cover_letter.update(cover_letter_id_to_update, version="v2")

    # Fetch the updated letter
    updated_letter = cover_letter.get(cover_letter_id_to_update)
    print(f"After update: {updated_letter}")

    assert updated_letter[5] == "v2", f"Cover letter version update failed, expected 'v2' but got {updated_letter[5]}"

    return cover_letter_ids

def test_saved_job_creation(saved_job, user_ids, job_offer_ids):
    """Test saved job creation and fetching."""
    print("\nTesting Saved Job Creation:")
    saved_job_ids = []
    for i, user_id in enumerate(user_ids):
        job_offer_id = job_offer_ids[i % len(job_offer_ids)]  # Cycle through job offers
        saved_job_id = saved_job.create(user_id, job_offer_id)
        assert saved_job_id is not None, f"Failed to create saved job for user {user_id}"
        saved_job_ids.append(saved_job_id)
        print(f"Saved job created with ID: {saved_job_id}")

    # Fetch and verify saved jobs
    for saved_job_id in saved_job_ids:
        fetched_saved_job = saved_job.get(saved_job_id)
        assert fetched_saved_job is not None, f"Failed to fetch saved job with ID {saved_job_id}"
        print(f"Fetched saved job: {fetched_saved_job}")

    return saved_job_ids

def test_user_deletion_with_cascade(user, user_document, cover_letter, job_offer, saved_job, user_site_credentials, user_application, user_job_preference, user_ids, doc_ids, cover_letter_ids, job_offer_ids, saved_job_ids, credential_ids, application_ids, preference_ids):
    """Test deletion of all users and cascading effects."""
    print("\nTesting User Deletion with Cascade:")
    
    for user_id in user_ids:
        print(f"\nDeleting User {user_id}")
        user.delete(user_id)
        
        # Verify user deletion
        try:
            user.get(user_id)
            print(f"Error: User {user_id} was not deleted")
        except ValueError as e:
            print(f"User {user_id} deleted successfully: {str(e)}")
        
        # Verify cascading document deletion
        for doc_id in doc_ids[user_id]:
            try:
                user_document.get(doc_id)
                print(f"Error: Document {doc_id} was not deleted in cascade")
            except ValueError as e:
                print(f"Document {doc_id} successfully deleted in cascade: {str(e)}")
        
        # Verify cascading cover letter deletion
        for letter_id in cover_letter_ids:
            try:
                letter = cover_letter.get(letter_id)
                if letter[1] == user_id:
                    print(f"Error: Cover letter {letter_id} was not deleted in cascade")
                else:
                    print(f"Cover letter {letter_id} correctly retained (belongs to a different user)")
            except ValueError as e:
                print(f"Cover letter {letter_id} successfully deleted in cascade: {str(e)}")
        
        # Verify cascading saved job deletion
        for saved_job_id in saved_job_ids:
            try:
                saved_job_item = saved_job.get(saved_job_id)
                if saved_job_item[1] == user_id:
                    print(f"Error: Saved job {saved_job_id} was not deleted in cascade")
                else:
                    print(f"Saved job {saved_job_id} correctly retained (belongs to a different user)")
            except ValueError as e:
                print(f"Saved job {saved_job_id} successfully deleted in cascade: {str(e)}")
        
        # Verify cascading site credentials deletion
        for cred_id in credential_ids:
            try:
                cred = user_site_credentials.get(cred_id)
                if cred[1] == user_id:
                    print(f"Error: Site credential {cred_id} was not deleted in cascade")
                else:
                    print(f"Site credential {cred_id} correctly retained (belongs to a different user)")
            except ValueError as e:
                print(f"Site credential {cred_id} successfully deleted in cascade: {str(e)}")
        
        # Verify cascading application deletion
        for app_id in application_ids:
            try:
                app = user_application.get(app_id)
                if app[1] == user_id:
                    print(f"Error: Application {app_id} was not deleted in cascade")
                else:
                    print(f"Application {app_id} correctly retained (belongs to a different user)")
            except ValueError as e:
                print(f"Application {app_id} successfully deleted in cascade: {str(e)}")
        
        # Verify cascading job preference deletion
        for pref_id in preference_ids:
            try:
                pref = user_job_preference.get(pref_id)
                if pref[1] == user_id:
                    print(f"Error: Job preference {pref_id} was not deleted in cascade")
                else:
                    print(f"Job preference {pref_id} correctly retained (belongs to a different user)")
            except ValueError as e:
                print(f"Job preference {pref_id} successfully deleted in cascade: {str(e)}")
    
    # Final verification
    final_users = user.list_all()
    assert len(final_users) == 0, "All users should have been deleted"
    print("\nAll users have been successfully deleted.")

    # Verify all related data is deleted
    all_docs = user_document.fetch_all("SELECT * FROM user_documents")
    all_letters = cover_letter.fetch_all("SELECT * FROM cover_letters")
    all_saved_jobs = saved_job.fetch_all("SELECT * FROM saved_jobs")
    all_credentials = user_site_credentials.fetch_all("SELECT * FROM user_site_credentials")
    all_applications = user_application.fetch_all("SELECT * FROM user_applications")
    all_preferences = user_job_preference.fetch_all("SELECT * FROM user_job_preferences")

    assert len(all_docs) == 0, "All documents should have been deleted"
    assert len(all_letters) == 0, "All cover letters should have been deleted"
    assert len(all_saved_jobs) == 0, "All saved jobs should have been deleted"
    assert len(all_credentials) == 0, "All site credentials should have been deleted"
    assert len(all_applications) == 0, "All applications should have been deleted"
    assert len(all_preferences) == 0, "All job preferences should have been deleted"

    print("All related user data has been successfully deleted.")

    # Verify job offers are not deleted (they should be independent of users)
    remaining_job_offers = job_offer.list_all()
    assert len(remaining_job_offers) == len(job_offer_ids), "Job offers should not have been deleted"
    print(f"All job offers ({len(remaining_job_offers)}) have been correctly retained.")


def test_job_offer_creation(job_offer):
    """Test job offer creation and fetching."""
    print("\nTesting Job Offer Creation:")
    job_offer_ids = []
    for i in range(3):
        job_offer_id = job_offer.create(
            title=f"Job {i}",
            company=f"Company {i}",
            location=f"Location {i}",
            description=f"Description for job {i}",
            url=f"http://example.com/job{i}",
            date_posted=datetime.now().isoformat(),
            source="Test Source"
        )
        assert job_offer_id is not None, f"Failed to create job offer {i}"
        job_offer_ids.append(job_offer_id)
        print(f"Job offer {i} created with ID: {job_offer_id}")

    # Fetch and verify job offers
    for job_offer_id in job_offer_ids:
        fetched_job_offer = job_offer.get(job_offer_id)
        assert fetched_job_offer is not None, f"Failed to fetch job offer with ID {job_offer_id}"
        print(f"Fetched job offer: {fetched_job_offer}")

    return job_offer_ids

# Ajouter ces nouvelles fonctions de test

def test_user_site_credentials(user_site_credentials, user_ids):
    print("\nTesting User Site Credentials:")
    credential_ids = []
    for user_id in user_ids:
        cred_id = user_site_credentials.create(user_id, "TestSite", f"user{user_id}@testsite.com", "encrypted_password")
        assert cred_id is not None, f"Failed to create credentials for user {user_id}"
        credential_ids.append(cred_id)
        print(f"Credentials created for user {user_id} with ID: {cred_id}")

    for cred_id in credential_ids:
        fetched_cred = user_site_credentials.get(cred_id)
        assert fetched_cred is not None, f"Failed to fetch credentials with ID {cred_id}"
        print(f"Fetched credentials: {fetched_cred}")

    return credential_ids

def test_user_application(user_application, user_ids, job_offer_ids):
    print("\nTesting User Application:")
    application_ids = []
    for i, user_id in enumerate(user_ids):
        job_offer_id = job_offer_ids[i % len(job_offer_ids)]
        app_id = user_application.create(user_id, job_offer_id, "Applied")
        assert app_id is not None, f"Failed to create application for user {user_id}"
        application_ids.append(app_id)
        print(f"Application created for user {user_id} with ID: {app_id}")

    for app_id in application_ids:
        fetched_app = user_application.get(app_id)
        assert fetched_app is not None, f"Failed to fetch application with ID {app_id}"
        print(f"Fetched application: {fetched_app}")

    return application_ids

def test_user_job_preference(user_job_preference, user_ids):
    print("\nTesting User Job Preference:")
    preference_ids = []
    for user_id in user_ids:
        pref_id = user_job_preference.create(user_id, "Full-time", "Python,SQL", "Remote")
        assert pref_id is not None, f"Failed to create job preference for user {user_id}"
        preference_ids.append(pref_id)
        print(f"Job preference created for user {user_id} with ID: {pref_id}")

    for pref_id in preference_ids:
        fetched_pref = user_job_preference.get(pref_id)
        assert fetched_pref is not None, f"Failed to fetch job preference with ID {pref_id}"
        print(f"Fetched job preference: {fetched_pref}")

    return preference_ids

def test_database():
    """Run all database tests."""
    test_db_path = 'test_jobfinder.db'
    setup_test_database(test_db_path)

    user = User(test_db_path)
    user_document = UserDocument(test_db_path)
    job_offer = JobOffer(test_db_path)
    cover_letter = CoverLetter(test_db_path)
    saved_job = SavedJob(test_db_path)
    user_site_credentials = UserSiteCredentials(test_db_path)
    user_application = UserApplication(test_db_path)
    user_job_preference = UserJobPreference(test_db_path)

    print("Starting complete JobFinder database tests")

    try:
        user_ids = test_user_creation(user)
        test_user_update(user, user_ids)
        test_user_list_all(user)
        
        doc_ids, test_files = test_document_creation(user_document, user_ids)
        test_document_fetch_and_update(user_document, user_ids, doc_ids)
        
        job_offer_ids = test_job_offer_creation(job_offer)
        
        cover_letter_ids = test_cover_letter_creation_and_update(cover_letter, user_ids, job_offer_ids)
        
        saved_job_ids = test_saved_job_creation(saved_job, user_ids, job_offer_ids)
        
        credential_ids = test_user_site_credentials(user_site_credentials, user_ids)
        
        application_ids = test_user_application(user_application, user_ids, job_offer_ids)
        
        preference_ids = test_user_job_preference(user_job_preference, user_ids)
        
        test_user_deletion_with_cascade(
            user, user_document, cover_letter, job_offer, saved_job, 
            user_site_credentials, user_application, user_job_preference,
            user_ids, doc_ids, cover_letter_ids, job_offer_ids, saved_job_ids, 
            credential_ids, application_ids, preference_ids
            )
        
    except (sqlite3.Error, IOError, ValueError) as e:
        print(f"Error during tests: {str(e)}")
    finally:
        teardown_test_database(test_db_path, test_files)

    print("\nJobFinder database tests completed")

if __name__ == "__main__":
    test_database()
