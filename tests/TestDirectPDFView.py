import os
import fitz
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

from database.JobFinderDatabase import User, UserDocument, DatabaseManager

# Chemins des fichiers
DB_PATH = 'jobfinder.db'
PDF_PATH = "CV.pdf"

def create_user_and_import_pdf():
    user = User(DB_PATH)
    user_document = UserDocument(DB_PATH)

    try:
        # Créer un utilisateur
        user_id = user.create("John Doe", "john@example.com", "password_hash")
        print(f"Utilisateur créé avec l'ID: {user_id}")

        # Importer le PDF
        if not os.path.exists(PDF_PATH):
            raise FileNotFoundError(f"Le fichier {PDF_PATH} n'existe pas.")

        with open(PDF_PATH, 'rb') as file:
            pdf_content = file.read()

        document_id = user_document.create(user_id, "CV", pdf_content, PDF_PATH)
        print(f"Document importé avec l'ID: {document_id}")

        # Supprimer le fichier original
        os.remove(PDF_PATH)
        print(f"Fichier original {PDF_PATH} supprimé.")

        return document_id
    finally:
        user.close_connection()
        user_document.close_connection()

class PDFViewer(QWidget):
    closed = pyqtSignal()

    def __init__(self, db_path, document_id):
        super().__init__()
        self.user_document = UserDocument(db_path)
        self.document_id = document_id
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.display_pdf()

    def display_pdf(self):
        try:
            document = self.user_document.get(self.document_id)
            if document:
                pdf_content = document[3]  # Le contenu binaire est à l'index 3
                pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    pix = page.get_pixmap()
                    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                    label = QLabel()
                    label.setPixmap(QPixmap.fromImage(img))
                    self.layout.addWidget(label)
                pdf_document.close()
        finally:
            self.user_document.close_connection()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

def recreate_pdf(db_path, document_id):
    user_document = UserDocument(db_path)
    try:
        document = user_document.get(document_id)
        if document:
            pdf_content = document[3]  # Le contenu binaire est à l'index 3
            with open(PDF_PATH, 'wb') as file:
                file.write(pdf_content)
            print(f"Fichier {PDF_PATH} recréé.")
    finally:
        user_document.close_connection()

def cleanup(db_path):
    # Supprimer la base de données
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Base de données {db_path} supprimée.")
        except PermissionError:
            print(f"Impossible de supprimer la base de données {db_path}. Elle pourrait être encore utilisée.")

if __name__ == '__main__':
    app = QApplication([])

    try:
        document_id = create_user_and_import_pdf()
    except Exception as e:
        print(f"Erreur lors de l'importation du PDF: {str(e)}")
        cleanup(DB_PATH)
        exit(1)

    viewer = PDFViewer(DB_PATH, document_id)
    viewer.show()

    def on_close():
        recreate_pdf(DB_PATH, document_id)
        cleanup(DB_PATH)
        app.quit()

    viewer.closed.connect(on_close)

    app.exec_()