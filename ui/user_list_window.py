import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLineEdit, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt
from database.JobFinderDatabase import User
from .MainWindow import MainWindow

class UserListWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JobFinder - Connexion")
        self.setGeometry(100, 100, 400, 500)

        self.user_manager = User()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Liste des utilisateurs
        self.user_list = QListWidget()
        self.user_list.itemDoubleClicked.connect(self.on_user_double_clicked)
        main_layout.addWidget(self.user_list)

        # Champs pour ajouter un nouvel utilisateur
        add_user_layout = QHBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe (optionnel)")
        self.password_input.setEchoMode(QLineEdit.Password)
        add_user_layout.addWidget(self.username_input)
        add_user_layout.addWidget(self.email_input)
        add_user_layout.addWidget(self.password_input)
        main_layout.addLayout(add_user_layout)

        # Boutons
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Ajouter utilisateur")
        self.delete_button = QPushButton("Supprimer utilisateur")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        main_layout.addLayout(button_layout)

        # Connexions
        self.add_button.clicked.connect(self.add_user)
        self.delete_button.clicked.connect(self.delete_user)

        # Chargement initial des utilisateurs
        self.load_users()

    def load_users(self):
        self.user_list.clear()
        users = self.user_manager.list_all()
        for user in users:
            self.user_list.addItem(f"{user[1]} - {user[2]}")  # username - email

    def add_user(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        
        if not username or not email:
            QMessageBox.warning(self, "Erreur", "Le nom d'utilisateur et l'email sont obligatoires.")
            return

        try:
            # Si le mot de passe est vide, nous passons None à la méthode create
            self.user_manager.create(username, email, password if password else None)
            self.load_users()
            self.username_input.clear()
            self.email_input.clear()
            self.password_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter l'utilisateur : {str(e)}")

    def delete_user(self):
        current_item = self.user_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un utilisateur à supprimer.")
            return

        username = current_item.text().split(' - ')[0]
        reply = QMessageBox.question(self, "Confirmer la suppression", 
                                     f"Êtes-vous sûr de vouloir supprimer l'utilisateur {username} ?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                user = self.user_manager.get_by_username(username)
                self.user_manager.delete(user[0])  # user[0] est l'ID de l'utilisateur
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer l'utilisateur : {str(e)}")

    def on_user_double_clicked(self, item):
        username = item.text().split(' - ')[0]
        user = self.user_manager.get_by_username(username)
        if user:
            if user[3]:  # Si l'utilisateur a un mot de passe
                password, ok = QInputDialog.getText(self, 'Mot de passe', 'Entrez votre mot de passe:', QLineEdit.Password)
                if ok:
                    if self.user_manager.verify_password(user[0], password):
                        self.open_main_window(user[0], username)
                    else:
                        QMessageBox.warning(self, "Erreur", "Mot de passe incorrect.")
            else:
                self.open_main_window(user[0], username)
        else:
            QMessageBox.warning(self, "Erreur", "Utilisateur non trouvé.")

    def open_main_window(self, user_id, username):
        self.main_window = MainWindow(user_id, username)
        self.main_window.show()
        self.close()  # Ferme la fenêtre de connexion

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserListWindow()
    window.show()
    sys.exit(app.exec_())