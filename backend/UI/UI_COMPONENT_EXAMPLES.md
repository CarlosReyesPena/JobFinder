# UI Component Examples for JobFinder

This document provides practical code examples for common UI components and patterns used in the JobFinder application.

## 1. Form Controls

### Job Search Form

```python
from PySide6.QtWidgets import (QWidget, QFormLayout, QLineEdit,
                               QComboBox, QPushButton, QVBoxLayout)

class JobSearchForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # Controls
        self.search_term = QLineEdit()
        self.search_term.setPlaceholderText("Job title, keywords, or company")

        self.region_combo = QComboBox()
        self.region_combo.addItems(["All Regions", "Zürich", "Geneva", "Basel"])

        self.category_combo = QComboBox()
        self.category_combo.addItems(["All Categories", "IT", "Finance", "Engineering"])

        # Add to form
        form_layout.addRow("Search term:", self.search_term)
        form_layout.addRow("Region:", self.region_combo)
        form_layout.addRow("Category:", self.category_combo)

        # Button
        self.search_button = QPushButton("Search")

        # Add to main layout
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.search_button)

        # Connect signals
        self.search_button.clicked.connect(self.on_search)

    def on_search(self):
        # Get values
        term = self.search_term.text()
        region = self.region_combo.currentText()
        category = self.category_combo.currentText()

        # Emit signal or call parent method
        print(f"Searching for {term} in {region}, category: {category}")
```

## 2. Data Display Components

### Job Offers List

```python
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget,
                              QTableWidgetItem, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt

class JobOffersList(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Header with count
        header_layout = QHBoxLayout()
        self.count_label = QLabel("0 jobs found")
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()

        # Table
        self.table = QTableWidget(0, 4)  # rows, columns
        self.table.setHorizontalHeaderLabels(["Title", "Company", "Location", "Date"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Add to layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.table)

        # Connect signals
        self.table.itemDoubleClicked.connect(self.on_job_selected)

    def set_jobs(self, jobs):
        # Clear table
        self.table.setRowCount(0)

        # Update count
        self.count_label.setText(f"{len(jobs)} jobs found")

        # Add jobs to table
        for i, job in enumerate(jobs):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(job.get('title', '')))
            self.table.setItem(i, 1, QTableWidgetItem(job.get('company', '')))
            self.table.setItem(i, 2, QTableWidgetItem(job.get('location', '')))
            self.table.setItem(i, 3, QTableWidgetItem(job.get('date', '')))

        # Resize columns
        self.table.resizeColumnsToContents()

    def on_job_selected(self, item):
        row = item.row()
        # Get job ID from data (could be stored in item data or tracked separately)
        job_id = row  # This is just a placeholder
        print(f"Job selected: {job_id}")
```

## 3. Status and Progress Components

### Operation Progress Panel

```python
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QProgressBar,
                              QLabel, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt

class OperationProgressPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Status label
        self.status_label = QLabel("Ready")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        # Buttons layout
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()

        # Add to main layout
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(button_layout)

        # Connect signals
        self.start_button.clicked.connect(self.on_start)
        self.cancel_button.clicked.connect(self.on_cancel)

    def on_start(self):
        self.progress_bar.setVisible(True)
        self.status_label.setText("Operation in progress...")
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        # Start the actual operation here

    def on_cancel(self):
        self.status_label.setText("Cancelling...")
        self.cancel_button.setEnabled(False)

        # Cancel the operation here

    def update_progress(self, value, max_value=100):
        self.progress_bar.setRange(0, max_value)
        self.progress_bar.setValue(value)

    def operation_complete(self, success=True, message=None):
        self.progress_bar.setVisible(False)
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        if success:
            self.status_label.setText(message or "Operation completed successfully")
        else:
            self.status_label.setText(message or "Operation failed")
```

## 4. Dialog Examples

### Document Preview Dialog

```python
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit,
                              QDialogButtonBox, QLabel)
from PySide6.QtCore import Qt

class DocumentPreviewDialog(QDialog):
    def __init__(self, document_title, document_content, parent=None):
        super().__init__(parent)

        # Window settings
        self.setWindowTitle(f"Preview: {document_title}")
        self.resize(600, 400)

        # Main layout
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(document_title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Document content
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(document_content)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # Add to layout
        layout.addWidget(title_label)
        layout.addWidget(self.text_edit)
        layout.addWidget(buttons)
```

## 5. Loading and Error Handling

### Async Operation Wrapper

```python
import asyncio
from PySide6.QtCore import QObject, Signal, QThread

class AsyncOperationWorker(QObject):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(int, int)  # value, max_value

    def __init__(self, coro_func, *args, **kwargs):
        super().__init__()
        self.coro_func = coro_func
        self.args = args
        self.kwargs = kwargs
        self.running = False

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            self.running = True
            result = loop.run_until_complete(self.coro_func(*self.args, **self.kwargs))
            if self.running:  # Check if cancelled
                self.finished.emit(result)
        except Exception as e:
            if self.running:  # Check if cancelled
                self.error.emit(str(e))
        finally:
            self.running = False
            loop.close()

    def cancel(self):
        self.running = False

class AsyncOperationHandler:
    def __init__(self, parent_widget=None):
        self.parent = parent_widget
        self.thread = None
        self.worker = None

    def run(self, coro_func, *args, on_finished=None, on_error=None, **kwargs):
        """
        Run an asynchronous operation in a separate thread

        Args:
            coro_func: The coroutine function to execute
            *args: Arguments to pass to the function
            on_finished: Callback for when operation completes
            on_error: Callback for when operation fails
            **kwargs: Keyword arguments to pass to the function
        """
        # Create worker and thread
        self.worker = AsyncOperationWorker(coro_func, *args, **kwargs)
        self.thread = QThread()

        # Move worker to thread
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)

        self.worker.finished.connect(lambda result: on_finished(result) if on_finished else None)
        self.worker.error.connect(lambda error: on_error(error) if on_error else None)

        # Clean up
        self.thread.finished.connect(self.thread.deleteLater)

        # Start thread
        self.thread.start()

    def cancel(self):
        if self.worker and self.thread:
            self.worker.cancel()
            self.thread.quit()
            self.thread.wait()
```

## 6. Navigation Components

### Sidebar Navigation

```python
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                              QLabel, QFrame, QSizePolicy)
from PySide6.QtCore import Signal, Qt

class SidebarNavigation(QWidget):
    page_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setMinimumWidth(180)
        self.setMaximumWidth(220)

        # Style
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #d0d0d0;
                font-weight: bold;
            }
        """)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)

        # App name
        app_name = QLabel("JobFinder")
        app_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(app_name)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        layout.addSpacing(10)

        # Navigation buttons
        self.buttons = {}

        # Add navigation buttons
        self.add_button("dashboard", "Dashboard")
        self.add_button("scraping", "Job Scraping")
        self.add_button("job_offers", "Job Offers")
        self.add_button("extract_job", "Extract Job")
        self.add_button("documents", "Documents")
        self.add_button("auto_apply", "Auto Apply")
        self.add_button("settings", "Settings")

        # Add stretch at the end
        layout.addStretch()

        # Set the initial active button
        self.set_active_page("dashboard")

    def add_button(self, page_id, text):
        button = QPushButton(text)
        button.setCheckable(True)

        # Store button reference
        self.buttons[page_id] = button

        # Add to layout
        self.layout().addWidget(button)

        # Connect click signal
        button.clicked.connect(lambda: self.on_button_clicked(page_id))

    def on_button_clicked(self, page_id):
        # Update buttons
        self.set_active_page(page_id)

        # Emit signal
        self.page_changed.emit(page_id)

    def set_active_page(self, page_id):
        # Update button states
        for id, button in self.buttons.items():
            button.setChecked(id == page_id)
```

## 7. Data Input Validation

### Input Validator

```python
from PySide6.QtWidgets import QLineEdit, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class InputValidator:
    """Helper class for validating input fields"""

    @staticmethod
    def validate_required(input_field, error_label=None):
        """Validate that an input field is not empty"""
        text = input_field.text().strip()

        if not text:
            input_field.setStyleSheet("border: 1px solid red;")
            if error_label:
                error_label.setText("This field is required")
                error_label.setVisible(True)
            return False
        else:
            input_field.setStyleSheet("")
            if error_label:
                error_label.setVisible(False)
            return True

    @staticmethod
    def validate_email(input_field, error_label=None):
        """Validate that an input field contains a valid email"""
        import re

        email = input_field.text().strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not email:
            input_field.setStyleSheet("border: 1px solid red;")
            if error_label:
                error_label.setText("Email is required")
                error_label.setVisible(True)
            return False
        elif not re.match(pattern, email):
            input_field.setStyleSheet("border: 1px solid red;")
            if error_label:
                error_label.setText("Invalid email format")
                error_label.setVisible(True)
            return False
        else:
            input_field.setStyleSheet("")
            if error_label:
                error_label.setVisible(False)
            return True

    @staticmethod
    def create_error_label():
        """Create a styled error label"""
        label = QLabel()
        label.setStyleSheet("color: red; font-size: 10px;")
        label.setVisible(False)
        return label
```

## 8. Settings and Configuration

### Settings Panel

```python
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout,
                              QLineEdit, QPushButton, QComboBox,
                              QLabel, QGroupBox)

class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        main_layout = QVBoxLayout(self)

        # API Settings group
        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout()

        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.Password)
        self.openai_api_key.setPlaceholderText("Enter your OpenAI API key")

        self.groq_api_key = QLineEdit()
        self.groq_api_key.setEchoMode(QLineEdit.Password)
        self.groq_api_key.setPlaceholderText("Enter your Groq API key")

        api_layout.addRow("OpenAI API Key:", self.openai_api_key)
        api_layout.addRow("Groq API Key:", self.groq_api_key)
        api_group.setLayout(api_layout)

        # User interface settings
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout()

        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "French", "German"])

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])

        ui_layout.addRow("Language:", self.language_combo)
        ui_layout.addRow("Theme:", self.theme_combo)
        ui_group.setLayout(ui_layout)

        # Button
        self.save_button = QPushButton("Save Settings")

        # Add to main layout
        main_layout.addWidget(api_group)
        main_layout.addWidget(ui_group)
        main_layout.addStretch()
        main_layout.addWidget(self.save_button)

        # Connect signals
        self.save_button.clicked.connect(self.save_settings)

    def load_settings(self, settings):
        """Load settings from a settings object or dictionary"""
        self.openai_api_key.setText(settings.get('openai_api_key', ''))
        self.groq_api_key.setText(settings.get('groq_api_key', ''))

        # Set language
        language = settings.get('language', 'English')
        index = self.language_combo.findText(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        # Set theme
        theme = settings.get('theme', 'Light')
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

    def save_settings(self):
        """Save settings to config or emit signal"""
        settings = {
            'openai_api_key': self.openai_api_key.text(),
            'groq_api_key': self.groq_api_key.text(),
            'language': self.language_combo.currentText(),
            'theme': self.theme_combo.currentText()
        }

        print("Saving settings:", settings)
        # Actually save the settings or emit a signal
```