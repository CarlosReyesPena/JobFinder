import sys
from PyQt5.QtWidgets import QApplication
from ui.user_list_window import UserListWindow

def main():
    # Créer l'application PyQt
    app = QApplication(sys.argv)

    # Créer et afficher la fenêtre de connexion
    login_window = UserListWindow()
    login_window.show()

    # Exécuter la boucle d'événements de l'application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()