import sys
import os
import json
import pyperclip
import re
import pyttsx3
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QMessageBox, QGroupBox,
    QListWidget, QListWidgetItem, QComboBox, QLineEdit, QCheckBox,
    QFileDialog, QDialog, QDialogButtonBox, QFormLayout
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, QTimer

from plyer import notification

# Set the GROQ API Key once here
os.environ["GROQ_API_KEY"] = "your_API_sec_key"

# Import Groq for Llama AI integration
try:
    from groq import Groq
except ImportError:
    print("groq package not found. Please install it using 'pip install groq'.")
    sys.exit(1)

###############################################################################
# GROQ INITIALIZATION FOR LLAMA AI
###############################################################################

# The API key is set via environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("GROQ_API_KEY must be set in the environment variables.")
    sys.exit(1)

###############################################################################
# NOTIFICATIONS (PLYER)
###############################################################################
NOTIFICATION_MAX_LENGTH = 256

def show_notification(title, message):
    """Show desktop notification using plyer."""
    if len(message) > NOTIFICATION_MAX_LENGTH:
        message = message[:NOTIFICATION_MAX_LENGTH - 3] + "..."
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="MundiLex",
            timeout=10  # Duration in seconds
        )
    except Exception as e:
        print(f"Failed to show notification: {e}")

###############################################################################
# VOCABULARY & DATA PERSISTENCE
###############################################################################
VOCAB_DATA_FILE = "vocab_data.json"

def load_vocab_data() -> dict:
    """Load vocabulary list from JSON."""
    if not os.path.exists(VOCAB_DATA_FILE):
        return {
            "vocab_list": [],
            "favorites": []
        }
    try:
        with open(VOCAB_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {
            "vocab_list": [],
            "favorites": []
        }

def save_vocab_data(data: dict):
    """Save vocabulary list to JSON."""
    try:
        with open(VOCAB_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save vocab data: {e}")

###############################################################################
# CLIPBOARD MONITOR WORKER
###############################################################################
class ClipboardWorker(QObject):
    data_fetched = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = False
        self.last_text = ""
        self.current_language = "German"  # Default language
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)

    def start_monitoring(self, language):
        """Start monitoring the clipboard for new single words."""
        self.current_language = language
        self._running = True
        self.timer.start(1000)  # Check every second

    def stop_monitoring(self):
        """Stop monitoring the clipboard."""
        self._running = False
        self.timer.stop()

    def is_single_word(self, text):
        """Check if the text is a single word in specified languages."""
        return bool(re.fullmatch(r"[A-Za-zäöüÄÖÜßàáâãäåçèéêëìíîïñòóôõöùúûüýÿÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ]+", text))

    def check_clipboard(self):
        """Check the clipboard for new single words."""
        if not self._running:
            return
        try:
            text = pyperclip.paste().strip()
            if text.startswith("sk-") or text.startswith("hf_") or len(text) > 50:
                return

            if self.is_single_word(text) and text.lower() != self.last_text.lower():
                self.last_text = text.lower()
                print(f"New text detected: {text}")

                # Fetch linguistic information using Llama AI via Groq
                response = self.fetch_linguistic_info(text, self.current_language)

                # Emit the fetched data along with the language
                self.data_fetched.emit(text, response)

                # Desktop notification
                show_notification("Linguistic Information", response)
        except Exception as e:
            err_msg = f"Error checking clipboard: {e}"
            print(err_msg)
            traceback.print_exc()
            self.error_occurred.emit(err_msg)

    def fetch_linguistic_info(self, word: str, language: str) -> str:
        """
        Fetch linguistic information using Llama AI via Groq.
        Returns the raw response string.
        """
        try:
            global client, chat_history
            global_initialized = 'client' in globals() and 'chat_history' in globals()
            if not global_initialized:
                client = Groq(api_key=GROQ_API_KEY)
                chat_history = [{
                    "role": "system",
                    "content": "You are a helpful assistant specializing in multiple languages. Provide clear and concise definitions, synonyms, antonyms, and example sentences in the specified language."
                }]
            
            user_message = {
                "role": "user",
                "content": f"Provide the definition, synonyms, antonyms, and example sentences for the word '{word}' in {language}. Format your response clearly. and whatever the language is I want you to speak in that language. also seperate your different resonses in different lines at least 2 lines space . and do not say hi or what you are about to do or any extra things just what you are asked to do"
            }

            # Append user message to chat history
            chat_history.append(user_message)

            # Request response from Llama AI
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=chat_history,
                max_tokens=500,
                temperature=0.7
            )

            assistant_message = response.choices[0].message.content.strip()
            print(f"Assistant:\n{assistant_message}")

            # Append assistant response to chat history
            chat_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            err_msg = f"Error fetching linguistic info for '{word}': {e}"
            print(err_msg)
            traceback.print_exc()
            self.error_occurred.emit(err_msg)
            return "Definition not available."

###############################################################################
# MAIN APPLICATION WINDOW
###############################################################################
class SmartDictionaryApp(QMainWindow):
    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key
        self.setWindowTitle("MundiLex")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QIcon("dictionary_icon.png"))  # Optional: Add a dictionary icon

        # Initialize Groq client
        try:
            global client, chat_history
            client = Groq(api_key=self.api_key)
            chat_history = [{
                "role": "system",
                "content": "You are a helpful assistant specializing in multiple languages. Provide clear and concise definitions, synonyms, antonyms, and example sentences in the specified language."
            }]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize Groq client: {e}")
            sys.exit(1)

        # Load saved data
        self.data_store = load_vocab_data()
        self.vocab_list_data = self.data_store.get("vocab_list", [])
        self.favorites = self.data_store.get("favorites", [])

        # Initialize flashcards
        self.current_flashcard = -1
        self.flashcards = []

        # Initialize current language
        self.current_language = "German"

        # Initialize worker and thread
        self.init_worker()

        # Initialize UI
        self.initUI()

    def init_worker(self):
        """Initialize the clipboard monitoring worker and thread."""
        self.worker = ClipboardWorker()
        self.worker.current_language = self.current_language
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        # Connect signals and slots
        self.worker.data_fetched.connect(self.handle_data_fetched)
        self.worker.error_occurred.connect(self.handle_error)

        self.thread.started.connect(lambda: self.worker.start_monitoring(self.current_language))
        self.thread.start()

    def initUI(self):
        """Set up the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Title label
        title_label = QLabel("MundiLex", self)
        title_font = QFont("Segoe UI", 28, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 15px;
        """)
        title_label.setFixedHeight(80)
        main_layout.addWidget(title_label)

        # Language Selection and Search Bar
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # Language Selection ComboBox
        language_label = QLabel("Select Language:", self)
        language_label.setFont(QFont("Segoe UI", 14))
        language_label.setStyleSheet("color: #ecf0f1;")
        top_layout.addWidget(language_label)

        self.language_combo = QComboBox(self)
        self.language_combo.setFont(QFont("Segoe UI", 14))
        self.language_combo.addItems(["German", "English", "French", "Italian", "Spanish", "Russian"])
        self.language_combo.setCurrentText(self.current_language)
        self.language_combo.currentTextChanged.connect(self.change_language)
        self.language_combo.setStyleSheet("""
            QComboBox {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 5px;
                border-radius: 10px;
            }
            QComboBox::drop-down {
                border-left-width: 1px;
                border-left-color: #bdc3c7;
                border-left-style: solid;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        top_layout.addWidget(self.language_combo)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        top_layout.addWidget(spacer)

        # Clipboard Toggle
        self.clipboard_toggle = QCheckBox("Enable Clipboard Monitoring", self)
        self.clipboard_toggle.setChecked(True)
        self.clipboard_toggle.setFont(QFont("Segoe UI", 14))
        self.clipboard_toggle.setStyleSheet("color: #ecf0f1;")
        self.clipboard_toggle.stateChanged.connect(self.toggle_clipboard)
        top_layout.addWidget(self.clipboard_toggle)

        # Search Bar
        search_label = QLabel("Search Word:", self)
        search_label.setFont(QFont("Segoe UI", 14))
        search_label.setStyleSheet("color: #ecf0f1;")
        top_layout.addWidget(search_label)

        self.search_bar = QLineEdit(self)
        self.search_bar.setFont(QFont("Segoe UI", 14))
        self.search_bar.setPlaceholderText("Enter word to search...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 10px;
                border-radius: 10px;
            }
        """)
        top_layout.addWidget(self.search_bar)

        search_btn = QPushButton("Search", self)
        search_btn.setFont(QFont("Segoe UI", 14))
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        search_btn.clicked.connect(self.search_word)
        top_layout.addWidget(search_btn)

        # Import and Export Buttons
        import_export_layout = QHBoxLayout()
        main_layout.addLayout(import_export_layout)

        import_btn = QPushButton("Import Flashcards", self)
        import_btn.setFont(QFont("Segoe UI", 14))
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
        """)
        import_btn.clicked.connect(self.import_flashcards)
        import_export_layout.addWidget(import_btn)

        export_btn = QPushButton("Export Flashcards", self)
        export_btn.setFont(QFont("Segoe UI", 14))
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
        """)
        export_btn.clicked.connect(self.export_flashcards)
        import_export_layout.addWidget(export_btn)

        # Add Favorite Button
        favorite_btn = QPushButton("Favorite", self)
        favorite_btn.setFont(QFont("Segoe UI", 14))
        favorite_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d4ac0d;
            }
        """)
        favorite_btn.clicked.connect(self.toggle_favorite)
        import_export_layout.addWidget(favorite_btn)

        # Grid for content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        main_layout.addLayout(content_layout)

        #######################################################################
        # 1) Linguistic Information Column
        #######################################################################
        linguistic_info_group = QGroupBox("Linguistic Information", self)
        linguistic_info_layout = QVBoxLayout()
        linguistic_info_group.setLayout(linguistic_info_layout)

        # Main Word Section
        main_word_label = QLabel("Word:", self)
        main_word_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        main_word_label.setStyleSheet("color: #ecf0f1;")
        linguistic_info_layout.addWidget(main_word_label)

        # Create the main_word_display QLabel
        self.main_word_display = QLabel("-", self)
        self.main_word_display.setFont(QFont("Segoe UI", 20))
        self.main_word_display.setAlignment(Qt.AlignLeft)
        self.main_word_display.setStyleSheet("""
            background-color: #bdc3c7;
            padding: 15px;
            border-radius: 10px;
            min-height: 40px;
            color: #2c3e50;
        """)
        linguistic_info_layout.addWidget(self.main_word_display)

        # Combined Information Display
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setFont(QFont("Segoe UI", 14))
        self.info_display.setStyleSheet("""
            background-color: #ecf0f1;
            color: #2c3e50;
            border-radius: 10px;
            padding: 15px;
        """)
        linguistic_info_layout.addWidget(self.info_display)

        # Pronunciation and Save Buttons
        buttons_layout = QHBoxLayout()

        pronounce_btn = QPushButton("Pronounce", self)
        pronounce_btn.setFont(QFont("Segoe UI", 14))
        pronounce_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #71368a;
            }
        """)
        pronounce_btn.clicked.connect(self.pronounce_word)
        buttons_layout.addWidget(pronounce_btn)

        save_btn = QPushButton("Add to Flashcards", self)
        save_btn.setFont(QFont("Segoe UI", 14))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        save_btn.clicked.connect(self.save_current_word)
        buttons_layout.addWidget(save_btn)

        linguistic_info_layout.addLayout(buttons_layout)

        content_layout.addWidget(linguistic_info_group, 3)

        #######################################################################
        # 2) Flashcards Display and Navigation Column
        #######################################################################
        flashcards_group = QGroupBox("Flashcards", self)
        flashcards_layout = QVBoxLayout()
        flashcards_group.setLayout(flashcards_layout)

        self.flashcard_display = QTextEdit()
        self.flashcard_display.setReadOnly(True)
        self.flashcard_display.setFont(QFont("Segoe UI", 16))
        self.flashcard_display.setStyleSheet("""
            background-color: #ecf0f1;
            color: #2c3e50;
            border-radius: 10px;
            padding: 20px;
        """)
        flashcards_layout.addWidget(self.flashcard_display)

        flashcards_btn_layout = QHBoxLayout()

        self.flip_btn = QPushButton("Flip", self)
        self.flip_btn.setFont(QFont("Segoe UI", 14))
        self.flip_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #d4ac0d;
            }
        """)
        self.flip_btn.clicked.connect(self.flip_flashcard)
        flashcards_btn_layout.addWidget(self.flip_btn)

        self.next_flashcard_btn = QPushButton("Next Card", self)
        self.next_flashcard_btn.setFont(QFont("Segoe UI", 14))
        self.next_flashcard_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.next_flashcard_btn.clicked.connect(self.next_flashcard)
        flashcards_btn_layout.addWidget(self.next_flashcard_btn)

        flashcards_layout.addLayout(flashcards_btn_layout)

        content_layout.addWidget(flashcards_group, 2)

        #######################################################################
        # 3) Saved Flashcards Management Column
        #######################################################################
        saved_flashcards_group = QGroupBox("Saved Flashcards", self)
        saved_flashcards_layout = QVBoxLayout()
        saved_flashcards_group.setLayout(saved_flashcards_layout)

        # List Widget to display saved flashcards
        self.saved_flashcards_list = QListWidget()
        self.saved_flashcards_list.setFont(QFont("Segoe UI", 14))
        self.saved_flashcards_list.setStyleSheet("""
            background-color: #ecf0f1;
            color: #2c3e50;
            border-radius: 10px;
        """)
        self.saved_flashcards_list.itemClicked.connect(self.display_flashcard)
        saved_flashcards_layout.addWidget(self.saved_flashcards_list)

        # Remove Button
        remove_btn = QPushButton("Remove Selected", self)
        remove_btn.setFont(QFont("Segoe UI", 14))
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        remove_btn.clicked.connect(self.remove_selected_flashcard)
        saved_flashcards_layout.addWidget(remove_btn)

        content_layout.addWidget(saved_flashcards_group, 1)

        #######################################################################
        # 4) Favorites Management Column
        #######################################################################
        favorites_group = QGroupBox("Favorites", self)
        favorites_layout = QVBoxLayout()
        favorites_group.setLayout(favorites_layout)

        # List Widget to display favorite words
        self.favorites_list = QListWidget()
        self.favorites_list.setFont(QFont("Segoe UI", 14))
        self.favorites_list.setStyleSheet("""
            background-color: #ecf0f1;
            color: #2c3e50;
            border-radius: 10px;
        """)
        self.favorites_list.itemClicked.connect(self.display_favorite)
        favorites_layout.addWidget(self.favorites_list)

        # Remove Favorite Button
        remove_fav_btn = QPushButton("Remove Favorite", self)
        remove_fav_btn.setFont(QFont("Segoe UI", 14))
        remove_fav_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: #ffffff;
                border-radius: 10px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        remove_fav_btn.clicked.connect(self.remove_favorite)
        favorites_layout.addWidget(remove_fav_btn)

        content_layout.addWidget(favorites_group, 1)

        #######################################################################
        # Stretch to fill space
        #######################################################################
        content_layout.setStretch(0, 3)  # Linguistic Information
        content_layout.setStretch(1, 2)  # Flashcards
        content_layout.setStretch(2, 1)  # Saved Flashcards
        content_layout.setStretch(3, 1)  # Favorites

        # Populate UI from saved data
        self.populate_saved_flashcards()
        self.populate_favorites()
        self.load_flashcards()

    ###########################################################################
    # VOCABULARY & DATA STORE
    ###########################################################################
    def populate_saved_flashcards(self):
        """Populate the saved flashcards list widget from self.vocab_list_data."""
        self.saved_flashcards_list.clear()
        for flashcard in self.vocab_list_data:
            display_text = f"{flashcard['word']} - {flashcard['language']}"
            item = QListWidgetItem(display_text)
            self.saved_flashcards_list.addItem(item)

    def populate_favorites(self):
        """Populate the favorites list widget from self.favorites."""
        self.favorites_list.clear()
        for word in self.favorites:
            item = QListWidgetItem(word)
            self.favorites_list.addItem(item)

    def save_data_store(self):
        """Save data store (vocab, favorites) to JSON."""
        self.data_store["vocab_list"] = self.vocab_list_data
        self.data_store["favorites"] = self.favorites
        save_vocab_data(self.data_store)

    ###########################################################################
    # EVENT HANDLERS
    ###########################################################################
    def handle_data_fetched(self, word: str, response: str):
        """Handle new data fetched from clipboard or search."""
        self.main_word_display.setText(word)
        formatted_response = response.replace('\n\n', '<br><br>').replace('\n', '<br>')
        self.info_display.setHtml(f"<p>{formatted_response}</p>")

    def handle_error(self, error_message: str):
        """Handle errors from the worker thread."""
        QMessageBox.critical(self, "Error", error_message)

    ###########################################################################
    # LANGUAGE SELECTION
    ###########################################################################
    def change_language(self, language):
        """Handle language change from the combo box."""
        self.current_language = language
        if self.clipboard_toggle.isChecked():
            # Restart clipboard monitoring with new language
            self.worker.stop_monitoring()
            self.thread.quit()
            self.thread.wait()

            # Initialize a new worker and thread
            self.init_worker()

    ###########################################################################
    # CLIPBOARD TOGGLE
    ###########################################################################
    def toggle_clipboard(self, state):
        """Enable or disable clipboard monitoring."""
        if state == Qt.Checked:
            # Enable clipboard monitoring
            if not self.thread.isRunning():
                self.init_worker()
        else:
            # Disable clipboard monitoring
            self.worker.stop_monitoring()
            self.thread.quit()
            self.thread.wait()

    ###########################################################################
    # SEARCH FUNCTIONALITY
    ###########################################################################
    def search_word(self):
        """Handle search button click."""
        word = self.search_bar.text().strip()
        if not word:
            QMessageBox.warning(self, "Warning", "Please enter a word to search.")
            return

        # Fetch linguistic information using Llama AI via Groq
        response = self.worker.fetch_linguistic_info(word, self.current_language)

        # Display fetched data
        self.handle_data_fetched(word, response)

    ###########################################################################
    # PRONUNCIATION
    ###########################################################################
    def pronounce_word(self):
        """Pronounce the content displayed in info_display."""
        content = self.info_display.toPlainText().strip()
        if not content or content == "Definition not available.":
            QMessageBox.warning(self, "Warning", "No content available for pronunciation.")
            return

        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            # Attempt to set language-specific voice
            voices = engine.getProperty('voices')
            language_code = self.get_language_code(self.current_language)
            language_voice_found = False
            for voice in voices:
                if hasattr(voice, 'languages'):
                    languages = voice.languages
                    for lang in languages:
                        try:
                            if language_code in lang.decode('utf-8').lower():
                                engine.setProperty('voice', voice.id)
                                language_voice_found = True
                                break
                        except:
                            continue
                if language_voice_found:
                    break
            if not language_voice_found:
                QMessageBox.warning(self, "Warning", 
                                    f"{self.current_language} voice not found. Using default voice.")
            engine.say(content)
            engine.runAndWait()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error during pronunciation: {e}")

    def get_language_code(self, language):
        """Return language code based on selected language."""
        language_codes = {
            "German": "de",
            "English": "en",
            "French": "fr",
            "Italian": "it",
            "Spanish": "es",
            "Russian": "ru"
        }
        return language_codes.get(language, "en")

    ###########################################################################
    # VOCABULARY ACTIONS
    ###########################################################################
    def save_current_word(self):
        """Add the current word to the flashcards list with all linguistic information."""
        word = self.main_word_display.text().strip()
        if not word or word == "-":
            QMessageBox.warning(
                self, "Warning", 
                "No word information available to save."
            )
            return

        # Extract information from the info_display
        info_html = self.info_display.toHtml()
        if not info_html:
            QMessageBox.warning(
                self, "Warning", 
                "No linguistic information available to save."
            )
            return

        # Parse the information
        try:
            # Use the raw response
            response = self.info_display.toPlainText().strip()

            # Check if the word already exists in flashcards
            existing_words = [fc['word'] for fc in self.vocab_list_data]
            if word not in existing_words:
                # Create a comprehensive flashcard entry
                flashcard = {
                    "word": word,
                    "language": self.current_language,
                    "response": response
                }
                self.vocab_list_data.append(flashcard)
                QMessageBox.information(
                    self, "Added", 
                    f"'{word}' has been added to your flashcards."
                )
                self.populate_saved_flashcards()
                self.save_data_store()
            else:
                QMessageBox.warning(
                    self, "Already Exists", 
                    f"'{word}' is already in your flashcards."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving flashcard: {e}")

    def import_flashcards(self):
        """Import flashcards from a JSON file."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self,"Import Flashcards","","JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, "r", encoding="utf-8") as f:
                    data = json.load(f)
                imported_flashcards = data.get("vocab_list", [])
                # Validate and add
                new_entries = 0
                for flashcard in imported_flashcards:
                    if flashcard['word'] not in [fc['word'] for fc in self.vocab_list_data]:
                        self.vocab_list_data.append(flashcard)
                        new_entries +=1
                QMessageBox.information(self, "Imported", f"Imported {new_entries} new flashcards.")
                self.populate_saved_flashcards()
                self.save_data_store()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import flashcards: {e}")

    def export_flashcards(self):
        """Export flashcards to a JSON file."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self,"Export Flashcards","","JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump({"vocab_list": self.vocab_list_data, "favorites": self.favorites}, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "Exported", "Flashcards exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export flashcards: {e}")

    def toggle_favorite(self):
        """Toggle favorite status of the current word."""
        word = self.main_word_display.text().strip()
        if not word or word == "-":
            QMessageBox.warning(self, "Warning", "No word information available to favorite.")
            return

        if word in self.favorites:
            self.favorites.remove(word)
            QMessageBox.information(self, "Removed", f"'{word}' has been removed from favorites.")
        else:
            self.favorites.append(word)
            QMessageBox.information(self, "Added", f"'{word}' has been added to favorites.")
        
        self.populate_favorites()
        self.save_data_store()

    def remove_favorite(self):
        """Remove the selected favorite word."""
        selected_items = self.favorites_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "No Selection", 
                "Please select a favorite word to remove."
            )
            return

        for item in selected_items:
            word = item.text().strip()
            if word in self.favorites:
                self.favorites.remove(word)
                self.favorites_list.takeItem(self.favorites_list.row(item))

        QMessageBox.information(
            self, "Removed", 
            "Selected favorite words have been removed."
        )
        self.save_data_store()

    def remove_selected_flashcard(self):
        """Remove the selected flashcard from the list and data store."""
        selected_items = self.saved_flashcards_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "No Selection", 
                "Please select a flashcard to remove."
            )
            return

        for item in selected_items:
            flashcard_text = item.text()
            word = flashcard_text.split(" - ")[0].strip()
            # Remove from vocab_list_data
            self.vocab_list_data = [fc for fc in self.vocab_list_data if fc['word'] != word]
            # Remove from the list widget
            self.saved_flashcards_list.takeItem(self.saved_flashcards_list.row(item))
            # Also remove from favorites if present
            if word in self.favorites:
                self.favorites.remove(word)

        QMessageBox.information(
            self, "Removed", 
            "Selected flashcards have been removed."
        )
        self.populate_favorites()
        self.save_data_store()

    ###########################################################################
    # FLASHCARDS
    ###########################################################################
    def load_flashcards(self):
        """Refresh flashcard display from vocab list."""
        self.flashcards = list(self.vocab_list_data)
        self.current_flashcard = -1
        self.next_flashcard()

    def flip_flashcard(self):
        """Toggle between showing the word and its details."""
        if self.current_flashcard == -1 or not self.flashcards:
            return
        flashcard = self.flashcards[self.current_flashcard]
        current_text = self.flashcard_display.toPlainText()
        if current_text == flashcard['word']:
            # Show all details
            response = flashcard.get('response', 'No information available.')
            formatted_response = response.replace('\n\n', '<br><br>').replace('\n', '<br>')
            self.flashcard_display.setHtml(f"<p>{formatted_response}</p>")
        else:
            # Show word
            self.flashcard_display.setText(flashcard['word'])

    def next_flashcard(self):
        """Display the next flashcard in the list."""
        if not self.flashcards:
            self.flashcard_display.setText("No flashcards available.")
            return
        self.current_flashcard = (self.current_flashcard + 1) % len(self.flashcards)
        flashcard = self.flashcards[self.current_flashcard]
        self.flashcard_display.setText(flashcard['word'])

    def display_flashcard(self, item):
        """Display the selected flashcard's information."""
        flashcard_text = item.text()
        word = flashcard_text.split(" - ")[0].strip()
        flashcard = next((fc for fc in self.flashcards if fc['word'] == word), None)
        if flashcard:
            self.main_word_display.setText(flashcard['word'])
            response = flashcard.get('response', 'No information available.')
            formatted_response = response.replace('\n\n', '<br><br>').replace('\n', '<br>')
            self.info_display.setHtml(f"<p>{formatted_response}</p>")
            self.flashcard_display.setText(flashcard['word'])

    def display_favorite(self, item):
        """Display information for the selected favorite word."""
        word = item.text().strip()
        # Fetch linguistic information for the word
        response = self.worker.fetch_linguistic_info(word, self.current_language)
        self.handle_data_fetched(word, response)

    ###########################################################################
    # ADDITIONAL FEATURES
    ###########################################################################
    # Add more features here as needed, such as categorized flashcards, quizzes, etc.

    ###########################################################################
    # CLOSE EVENT
    ###########################################################################
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Exit',
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.worker.stop_monitoring()
            self.thread.quit()
            self.thread.wait()

            self.save_data_store()

            event.accept()
        else:
            event.ignore()

###############################################################################
# MAIN
###############################################################################
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look

    # Apply a modern color palette with grey, orange, purple, and gold
    palette = QtGui.QPalette()

    # Base colors
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(45, 45, 45))  # Dark grey
    palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(30, 30, 30))  # Darker grey
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(45, 45, 45))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(60, 60, 60))  # Grey
    palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)

    # Highlight colors
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(243, 156, 18))  # Orange
    palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)

    app.setPalette(palette)

    window = SmartDictionaryApp(GROQ_API_KEY)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
