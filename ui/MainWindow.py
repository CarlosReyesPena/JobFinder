from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel

class MainWindow(QMainWindow):
    def __init__(self, user_id, username):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.setWindowTitle(f"JobFinder - Bienvenue {username}")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        welcome_label = QLabel(f"Bienvenue, {username}!")
        layout.addWidget(welcome_label)

        # Ajoutez ici les autres widgets et fonctionnalités de votre application principale
        # Par exemple :
        # self.job_list_view = JobListView()
        # layout.addWidget(self.job_list_view)
        # 
        # self.application_status_view = ApplicationStatusView()
        # layout.addWidget(self.application_status_view)
        # 
        # etc.

    # Ajoutez ici les méthodes nécessaires pour gérer les fonctionnalités de l'application