import sqlite3
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path='database/jobfinder.db'):
        self.db_path = db_path
        self._create_database()

    def _create_database(self):
        # Create the database file if it doesn't exist and enable foreign key constraints
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.close()

    def execute_query(self, query, params=None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints for each connection
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                if query.strip().upper().startswith("INSERT"):
                    return cursor.lastrowid
                else:
                    return cursor.rowcount
            except sqlite3.Error as e:
                raise sqlite3.Error(f"Erreur lors de l'exécution de la requête: {str(e)}")

    def fetch_one(self, query, params=None):
        # Fetch a single record from the database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchone()
            except sqlite3.Error as e:
                raise sqlite3.Error(f"Erreur lors de la récupération d'un enregistrement: {str(e)}")

    def fetch_all(self, query, params=None):
        # Fetch all records from the database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            except sqlite3.Error as e:
                raise sqlite3.Error(f"Erreur lors de la récupération de plusieurs enregistrements: {str(e)}")


class User(DatabaseManager):
    def __init__(self, db_path='database/jobfinder.db'):
        super().__init__(db_path)
        self._create_table()

    def _create_table(self):
        # Create the users table with a primary key and unique constraints
        query = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            registration_date TEXT NOT NULL
        )
        '''
        self.execute_query(query)

    def create(self, username, email, password_hash):
        # Insert a new user into the users table
        query = '''
        INSERT INTO users (username, email, password_hash, registration_date)
        VALUES (?, ?, ?, ?)
        '''
        params = (username, email, password_hash, datetime.now().isoformat())
        return self.execute_query(query, params)

    def get(self, user_id):
        # Retrieve a user by ID
        query = 'SELECT * FROM users WHERE id = ?'
        result = self.fetch_one(query, (user_id,))
        if result is None:
            raise ValueError(f"Aucun utilisateur trouvé avec l'ID {user_id}")
        return result

    def get_by_username(self, username):
        # Retrieve a user by username
        query = 'SELECT * FROM users WHERE username = ?'
        return self.fetch_one(query, (username,))

    def get_by_email(self, email):
        # Retrieve a user by email
        query = 'SELECT * FROM users WHERE email = ?'
        return self.fetch_one(query, (email,))

    def update(self, user_id, username=None, email=None, password_hash=None):
        # Update user details with optional fields
        updates = []
        params = []
        if username:
            updates.append('username = ?')
            params.append(username)
        if email:
            updates.append('email = ?')
            params.append(email)
        if password_hash:
            updates.append('password_hash = ?')
            params.append(password_hash)
        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(user_id)
            return self.execute_query(query, tuple(params))

    def delete(self, user_id):
        # Delete a user by ID
        query = 'DELETE FROM users WHERE id = ?'
        result = self.execute_query(query, (user_id,))
        if result == 0:
            raise ValueError(f"Aucun utilisateur trouvé avec l'ID {user_id}")
        return result

    def list_all(self):
        # List all users
        query = 'SELECT * FROM users'
        return self.fetch_all(query)


class BinaryFileManager(DatabaseManager):
    def __init__(self, db_path='database/jobfinder.db'):
        super().__init__(db_path)

    def _read_file(self, file_path):
        # Read a binary file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")
        with open(file_path, 'rb') as file:
            return file.read()

    def _save_file(self, content, file_name, output_directory):
        # Save binary content to a file
        output_path = os.path.join(output_directory, file_name)
        with open(output_path, 'wb') as file:
            file.write(content)
        return output_path


class UserDocument(BinaryFileManager):
    def __init__(self, db_path='database/jobfinder.db'):
        try:
            super().__init__(db_path)
            self._create_table()
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Erreur lors de l'initialisation de UserDocument: {str(e)}")

    def _create_table(self):
        # Create the user_documents table with a foreign key constraint for cascading delete
        query = '''
        CREATE TABLE IF NOT EXISTS user_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            content BLOB NOT NULL,
            file_name TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        '''
        self.execute_query(query)

    def create(self, user_id, document_type, content, file_name):
        # Insert a new document into the user_documents table
        query = '''
        INSERT INTO user_documents (user_id, document_type, content, file_name, upload_date)
        VALUES (?, ?, ?, ?, ?)
        '''
        params = (user_id, document_type, content, file_name, datetime.now().isoformat())
        return self.execute_query(query, params)

    def create_from_file(self, user_id, document_type, file_path):
        # Create a document entry from a file
        try:
            content = self._read_file(file_path)
            file_name = os.path.basename(file_path)
            return self.create(user_id, document_type, content, file_name)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Le fichier {file_path} n'a pas été trouvé: {str(e)}")
        except IOError as e:
            raise IOError(f"Erreur lors de la lecture du fichier {file_path}: {str(e)}")

    def get(self, document_id):
        # Retrieve a document by ID
        query = 'SELECT * FROM user_documents WHERE id = ?'
        result = self.fetch_one(query, (document_id,))
        if result is None:
            raise ValueError(f"Aucun document trouvé avec l'ID {document_id}")
        return result

    def get_all_for_user(self, user_id):
        # Retrieve all documents for a specific user
        query = 'SELECT * FROM user_documents WHERE user_id = ?'
        return self.fetch_all(query, (user_id,))

    def get_by_type(self, user_id, document_type):
        # Retrieve documents by type for a specific user
        query = 'SELECT * FROM user_documents WHERE user_id = ? AND document_type = ?'
        return self.fetch_all(query, (user_id, document_type))

    def update(self, document_id, document_type=None, content=None, file_name=None):
        # Update document details with optional fields
        updates = []
        params = []
        if document_type:
            updates.append('document_type = ?')
            params.append(document_type)
        if content:
            updates.append('content = ?')
            params.append(content)
        if file_name:
            updates.append('file_name = ?')
            params.append(file_name)
        if updates:
            updates.append('upload_date = ?')
            params.append(datetime.now().isoformat())
            query = f"UPDATE user_documents SET {', '.join(updates)} WHERE id = ?"
            params.append(document_id)
            result = self.execute_query(query, tuple(params))
            if result == 0:
                raise ValueError(f"Aucun document trouvé avec l'ID {document_id}")
            return result
        else:
            raise ValueError("Aucun champ à mettre à jour n'a été spécifié")

    def delete(self, document_id):
        # Delete a document by ID
        query = 'DELETE FROM user_documents WHERE id = ?'
        result = self.execute_query(query, (document_id,))
        if result == 0:
            raise ValueError(f"Aucun document trouvé avec l'ID {document_id}")
        return result

    def delete_all_for_user(self, user_id):
        # Delete all documents for a specific user
        query = 'DELETE FROM user_documents WHERE user_id = ?'
        return self.execute_query(query, (user_id,))

    def save_to_file(self, document_id, output_directory):
        # Save document content to a file
        result = self.get(document_id)
        content = result[3]  # Assuming content is the 4th column
        file_name = result[4]  # Assuming file_name is the 5th column
        return self._save_file(content, file_name, output_directory)


class CoverLetter(BinaryFileManager):
    def __init__(self, db_path='database/jobfinder.db'):
        try:
            super().__init__(db_path)
            self._create_table()
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Erreur lors de l'initialisation de CoverLetter: {str(e)}")

    def _create_table(self):
        # Create the cover_letters table with foreign key constraints
        query = '''
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_offer_id INTEGER NOT NULL,
            content BLOB NOT NULL,
            creation_date TEXT NOT NULL,
            version TEXT NOT NULL,
            file_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (job_offer_id) REFERENCES job_offers (id) ON DELETE CASCADE
        )
        '''
        self.execute_query(query)

    def create(self, user_id, job_offer_id, content, version, file_name):
        # Insert a new cover letter into the cover_letters table
        query = '''
        INSERT INTO cover_letters (user_id, job_offer_id, content, creation_date, version, file_name)
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        params = (user_id, job_offer_id, content, datetime.now().isoformat(), version, file_name)
        return self.execute_query(query, params)

    def create_from_file(self, user_id, job_offer_id, file_path, version):
        # Create a cover letter entry from a file
        try:
            content = self._read_file(file_path)
            file_name = os.path.basename(file_path)
            return self.create(user_id, job_offer_id, content, version, file_name)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Le fichier {file_path} n'a pas été trouvé: {str(e)}")
        except IOError as e:
            raise IOError(f"Erreur lors de la lecture du fichier {file_path}: {str(e)}")

    def get(self, cover_letter_id):
        # Retrieve a cover letter by ID
        query = 'SELECT * FROM cover_letters WHERE id = ?'
        result = self.fetch_one(query, (cover_letter_id,))
        if result is None:
            raise ValueError(f"Aucune lettre de motivation trouvée avec l'ID {cover_letter_id}")
        return result

    def get_all_for_user(self, user_id):
        # Retrieve all cover letters for a specific user
        query = 'SELECT * FROM cover_letters WHERE user_id = ?'
        return self.fetch_all(query, (user_id,))

    def get_for_job_offer(self, user_id, job_offer_id):
        # Retrieve cover letters for a specific job offer
        query = 'SELECT * FROM cover_letters WHERE user_id = ? AND job_offer_id = ?'
        return self.fetch_all(query, (user_id, job_offer_id))

    def update(self, cover_letter_id, content=None, version=None, file_name=None):
        # Update cover letter details with optional fields
        updates = []
        params = []
        if content:
            updates.append('content = ?')
            params.append(content)
        if version:
            updates.append('version = ?')
            params.append(version)
        if file_name:
            updates.append('file_name = ?')
            params.append(file_name)
        if updates:
            updates.append('creation_date = ?')
            params.append(datetime.now().isoformat())
            query = f"UPDATE cover_letters SET {', '.join(updates)} WHERE id = ?"
            params.append(cover_letter_id)
            result = self.execute_query(query, tuple(params))
            if result == 0:
                raise ValueError(f"Aucune lettre de motivation trouvée avec l'ID {cover_letter_id}")
            return result
        else:
            raise ValueError("Aucun champ à mettre à jour n'a été spécifié")

    def delete(self, cover_letter_id):
        # Delete a cover letter by ID
        query = 'DELETE FROM cover_letters WHERE id = ?'
        result = self.execute_query(query, (cover_letter_id,))
        if result == 0:
            raise ValueError(f"Aucune lettre de motivation trouvée avec l'ID {cover_letter_id}")
        return result

    def delete_all_for_user(self, user_id):
        # Delete all cover letters for a specific user
        query = 'DELETE FROM cover_letters WHERE user_id = ?'
        return self.execute_query(query, (user_id,))

    def save_to_file(self, cover_letter_id, output_directory):
        # Save cover letter content to a file
        result = self.get(cover_letter_id)
        content = result[3]  # Assuming content is the 4th column
        file_name = result[6]  # Assuming file_name is the 7th column
        return self._save_file(content, file_name, output_directory)

    def get_latest_version(self, user_id, job_offer_id):
        # Retrieve the latest version of a cover letter for a specific user and job offer
        query = '''
        SELECT * FROM cover_letters 
        WHERE user_id = ? AND job_offer_id = ? 
        ORDER BY creation_date DESC 
        LIMIT 1
        '''
        result = self.fetch_one(query, (user_id, job_offer_id))
        if result is None:
            raise ValueError(f"Aucune lettre de motivation trouvée pour l'utilisateur {user_id} et l'offre d'emploi {job_offer_id}")
        return result
    
class JobOffer(DatabaseManager):
    def __init__(self, db_path='database/jobfinder.db'):
        super().__init__(db_path)
        self._create_table()

    def _create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS job_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            url TEXT NOT NULL,
            date_posted TEXT NOT NULL,
            source TEXT NOT NULL
        )
        '''
        self.execute_query(query)

    def create(self, title, company, location, description, url, date_posted, source):
        query = '''
        INSERT INTO job_offers (title, company, location, description, url, date_posted, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (title, company, location, description, url, date_posted, source)
        return self.execute_query(query, params)

    def get(self, job_offer_id):
        query = 'SELECT * FROM job_offers WHERE id = ?'
        result = self.fetch_one(query, (job_offer_id,))
        if result is None:
            raise ValueError(f"Aucune offre d'emploi trouvée avec l'ID {job_offer_id}")
        return result

    def update(self, job_offer_id, title=None, company=None, location=None, description=None, url=None, date_posted=None, source=None):
        updates = []
        params = []
        for field in ['title', 'company', 'location', 'description', 'url', 'date_posted', 'source']:
            value = locals()[field]
            if value is not None:
                updates.append(f'{field} = ?')
                params.append(value)
        if updates:
            query = f"UPDATE job_offers SET {', '.join(updates)} WHERE id = ?"
            params.append(job_offer_id)
            result = self.execute_query(query, tuple(params))
            if result == 0:
                raise ValueError(f"Aucune offre d'emploi trouvée avec l'ID {job_offer_id}")
            return result
        else:
            raise ValueError("Aucun champ à mettre à jour n'a été spécifié")

    def delete(self, job_offer_id):
        query = 'DELETE FROM job_offers WHERE id = ?'
        result = self.execute_query(query, (job_offer_id,))
        if result == 0:
            raise ValueError(f"Aucune offre d'emploi trouvée avec l'ID {job_offer_id}")
        return result

    def list_all(self):
        query = 'SELECT * FROM job_offers'
        return self.fetch_all(query)

class SavedJob(DatabaseManager):
    def __init__(self, db_path='database/jobfinder.db'):
        super().__init__(db_path)
        self._create_table()

    def _create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_offer_id INTEGER NOT NULL,
            saved_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (job_offer_id) REFERENCES job_offers (id) ON DELETE CASCADE
        )
        '''
        self.execute_query(query)

    def create(self, user_id, job_offer_id):
        query = '''
        INSERT INTO saved_jobs (user_id, job_offer_id, saved_date)
        VALUES (?, ?, ?)
        '''
        params = (user_id, job_offer_id, datetime.now().isoformat())
        return self.execute_query(query, params)

    def get(self, saved_job_id):
        query = 'SELECT * FROM saved_jobs WHERE id = ?'
        result = self.fetch_one(query, (saved_job_id,))
        if result is None:
            raise ValueError(f"Aucun emploi sauvegardé trouvé avec l'ID {saved_job_id}")
        return result

    def get_all_for_user(self, user_id):
        query = 'SELECT * FROM saved_jobs WHERE user_id = ?'
        return self.fetch_all(query, (user_id,))

    def delete(self, saved_job_id):
        query = 'DELETE FROM saved_jobs WHERE id = ?'
        result = self.execute_query(query, (saved_job_id,))
        if result == 0:
            raise ValueError(f"Aucun emploi sauvegardé trouvé avec l'ID {saved_job_id}")
        return result

    def delete_all_for_user(self, user_id):
        query = 'DELETE FROM saved_jobs WHERE user_id = ?'
        return self.execute_query(query, (user_id,))

class UserSiteCredentials(DatabaseManager):
    def __init__(self, db_path='database/jobfinder.db'):
        super().__init__(db_path)
        self._create_table()

    def _create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS user_site_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            site_name TEXT NOT NULL,
            email TEXT NOT NULL,
            password_encrypted TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        '''
        self.execute_query(query)

    def create(self, user_id, site_name, email, password_encrypted):
        query = '''
        INSERT INTO user_site_credentials (user_id, site_name, email, password_encrypted)
        VALUES (?, ?, ?, ?)
        '''
        params = (user_id, site_name, email, password_encrypted)
        return self.execute_query(query, params)

    def get(self, credential_id):
        query = 'SELECT * FROM user_site_credentials WHERE id = ?'
        result = self.fetch_one(query, (credential_id,))
        if result is None:
            raise ValueError(f"Aucune donnée d'identification trouvée avec l'ID {credential_id}")
        return result

    def get_all_for_user(self, user_id):
        query = 'SELECT * FROM user_site_credentials WHERE user_id = ?'
        return self.fetch_all(query, (user_id,))

    def update(self, credential_id, site_name=None, email=None, password_encrypted=None):
        updates = []
        params = []
        if site_name:
            updates.append('site_name = ?')
            params.append(site_name)
        if email:
            updates.append('email = ?')
            params.append(email)
        if password_encrypted:
            updates.append('password_encrypted = ?')
            params.append(password_encrypted)
        if updates:
            query = f"UPDATE user_site_credentials SET {', '.join(updates)} WHERE id = ?"
            params.append(credential_id)
            result = self.execute_query(query, tuple(params))
            if result == 0:
                raise ValueError(f"Aucune donnée d'identification trouvée avec l'ID {credential_id}")
            return result
        else:
            raise ValueError("Aucun champ à mettre à jour n'a été spécifié")

    def delete(self, credential_id):
        query = 'DELETE FROM user_site_credentials WHERE id = ?'
        result = self.execute_query(query, (credential_id,))
        if result == 0:
            raise ValueError(f"Aucune donnée d'identification trouvée avec l'ID {credential_id}")
        return result

class UserApplication(DatabaseManager):
    def __init__(self, db_path='database/jobfinder.db'):
        super().__init__(db_path)
        self._create_table()

    def _create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS user_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_offer_id INTEGER NOT NULL,
            application_date TEXT NOT NULL,
            status TEXT NOT NULL,
            cover_letter_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (job_offer_id) REFERENCES job_offers (id) ON DELETE CASCADE,
            FOREIGN KEY (cover_letter_id) REFERENCES cover_letters (id) ON DELETE SET NULL
        )
        '''
        self.execute_query(query)

    def create(self, user_id, job_offer_id, status, cover_letter_id=None):
        query = '''
        INSERT INTO user_applications (user_id, job_offer_id, application_date, status, cover_letter_id)
        VALUES (?, ?, ?, ?, ?)
        '''
        params = (user_id, job_offer_id, datetime.now().isoformat(), status, cover_letter_id)
        return self.execute_query(query, params)

    def get(self, application_id):
        query = 'SELECT * FROM user_applications WHERE id = ?'
        result = self.fetch_one(query, (application_id,))
        if result is None:
            raise ValueError(f"Aucune candidature trouvée avec l'ID {application_id}")
        return result

    def get_all_for_user(self, user_id):
        query = 'SELECT * FROM user_applications WHERE user_id = ?'
        return self.fetch_all(query, (user_id,))

    def update(self, application_id, status=None, cover_letter_id=None):
        updates = []
        params = []
        if status:
            updates.append('status = ?')
            params.append(status)
        if cover_letter_id is not None:
            updates.append('cover_letter_id = ?')
            params.append(cover_letter_id)
        if updates:
            query = f"UPDATE user_applications SET {', '.join(updates)} WHERE id = ?"
            params.append(application_id)
            result = self.execute_query(query, tuple(params))
            if result == 0:
                raise ValueError(f"Aucune candidature trouvée avec l'ID {application_id}")
            return result
        else:
            raise ValueError("Aucun champ à mettre à jour n'a été spécifié")

    def delete(self, application_id):
        query = 'DELETE FROM user_applications WHERE id = ?'
        result = self.execute_query(query, (application_id,))
        if result == 0:
            raise ValueError(f"Aucune candidature trouvée avec l'ID {application_id}")
        return result

class UserJobPreference(DatabaseManager):
    def __init__(self, db_path='database/jobfinder.db'):
        super().__init__(db_path)
        self._create_table()

    def _create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS user_job_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_type TEXT NOT NULL,
            keywords TEXT NOT NULL,
            location_preference TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        '''
        self.execute_query(query)

    def create(self, user_id, job_type, keywords, location_preference):
        query = '''
        INSERT INTO user_job_preferences (user_id, job_type, keywords, location_preference)
        VALUES (?, ?, ?, ?)
        '''
        keywords_str = ','.join(keywords) if isinstance(keywords, list) else keywords
        params = (user_id, job_type, keywords_str, location_preference)
        return self.execute_query(query, params)

    def get(self, preference_id):
        query = 'SELECT * FROM user_job_preferences WHERE id = ?'
        result = self.fetch_one(query, (preference_id,))
        if result is None:
            raise ValueError(f"Aucune préférence d'emploi trouvée avec l'ID {preference_id}")
        return result

    def get_for_user(self, user_id):
        query = 'SELECT * FROM user_job_preferences WHERE user_id = ?'
        return self.fetch_one(query, (user_id,))

    def update(self, preference_id, job_type=None, keywords=None, location_preference=None):
        updates = []
        params = []
        if job_type:
            updates.append('job_type = ?')
            params.append(job_type)
        if keywords:
            updates.append('keywords = ?')
            keywords_str = ','.join(keywords) if isinstance(keywords, list) else keywords
            params.append(keywords_str)
        if location_preference:
            updates.append('location_preference = ?')
            params.append(location_preference)
        if updates:
            query = f"UPDATE user_job_preferences SET {', '.join(updates)} WHERE id = ?"
            params.append(preference_id)
            result = self.execute_query(query, tuple(params))
            if result == 0:
                raise ValueError(f"Aucune préférence d'emploi trouvée avec l'ID {preference_id}")
            return result
        else:
            raise ValueError("Aucun champ à mettre à jour n'a été spécifié")

    def delete(self, preference_id):
        query = 'DELETE FROM user_job_preferences WHERE id = ?'
        result = self.execute_query(query, (preference_id,))
        if result == 0:
            raise ValueError(f"Aucune préférence d'emploi trouvée avec l'ID {preference_id}")
        return result