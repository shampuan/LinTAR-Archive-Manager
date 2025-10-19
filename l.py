import re
import sys
import os
import configparser
import subprocess
import datetime
import zipfile
import tarfile
import zlib
import shutil
import tempfile
from threading import Thread

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QToolButton,
    QLineEdit, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QSizePolicy, QMenu, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QPushButton, QTabWidget,
    QGroupBox, QFormLayout, QComboBox, QCheckBox, QSpinBox,
    QFileDialog, QAction, QProgressDialog, QInputDialog, QPlainTextEdit
)
from PyQt5.QtGui import QIcon, QCursor, QTextCursor, QFont, QColor
from PyQt5.QtCore import Qt, QSize, QObject, pyqtSignal, pyqtSlot, QProcess, QSettings

# Resimlerin ve dil dosyasının yolları
BASE_DIR = os.path.dirname(__file__)
LOCAL_ICON_DIR = os.path.join(BASE_DIR, "icons")
DEVELOPMENT_ICON_DIR = "/home/serhat/LinTAR_Project/DEBIAN/usr/share/lintar/icons/"
SYSTEM_ICON_DIR = "/usr/share/lintar/icons/"

# Icon dizinini belirle
if os.path.exists(LOCAL_ICON_DIR):
    ICON_DIR = LOCAL_ICON_DIR
elif os.path.exists(DEVELOPMENT_ICON_DIR):
    ICON_DIR = DEVELOPMENT_ICON_DIR
elif os.path.exists(SYSTEM_ICON_DIR):
    ICON_DIR = SYSTEM_ICON_DIR
else:
    ICON_DIR = BASE_DIR

LANG_FILE = os.path.join(BASE_DIR, "language.ini")
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".config", "lintar", "settings.ini")

# Config yönetimi
def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE, encoding='utf-8')
    return config

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        config.write(f)

def get_config_value(section, key, default):
    config = load_config()
    return config.get(section, key, fallback=default)

def set_config_value(section, key, value):
    config = load_config()
    if section not in config:
        config[section] = {}
    config[section][key] = str(value)
    save_config(config)

class ExtractWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)

    def __init__(self, archive_path, extract_to):
        super().__init__()
        self.archive_path = archive_path
        self.extract_to = extract_to
        self._is_running = True

    def run(self):
        try:
            if not self._is_running:
                return

            if self.archive_path.endswith(".zip"):
                with zipfile.ZipFile(self.archive_path, 'r') as zf:
                    total_files = len(zf.infolist())
                    for i, member in enumerate(zf.infolist()):
                        if not self._is_running:
                            break
                        zf.extract(member, self.extract_to)
                        self.progress.emit(int((i + 1) / total_files * 100))
                self.finished.emit(True, None)
                
            elif self.archive_path.endswith((".tar.gz", ".tar.bz2", ".tar.xz", ".tar")):
                with tarfile.open(self.archive_path, 'r:*') as tf:
                    members = tf.getmembers()
                    total_files = len(members)
                    for i, member in enumerate(members):
                        if not self._is_running:
                            break
                        tf.extract(member, self.extract_to)
                        self.progress.emit(int((i + 1) / total_files * 100))
                self.finished.emit(True, None)
                
            elif self.archive_path.endswith(".7z"):
                if not check_command_exists("7z"):
                    self.finished.emit(False, "7z programı bulunamadı")
                    return
                
                command = ["7z", "x", self.archive_path, f"-o{self.extract_to}", "-y"]
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                
                while True:
                    if not self._is_running:
                        process.terminate()
                        break
                    
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output and "%" in output:
                        try:
                            percent = int(output.split("%")[0].strip())
                            self.progress.emit(percent)
                        except:
                            pass
                
                if not self._is_running:
                    self.finished.emit(False, "İşlem iptal edildi")
                    return
                elif process.returncode != 0:
                    error = process.stderr.read()
                    self.finished.emit(False, error or "Bilinmeyen hata")
                else:
                    self.finished.emit(True, None)
            else:
                self.finished.emit(False, f"Tanınmayan format: {os.path.splitext(self.archive_path)[1]}")
        except Exception as e:
            self.finished.emit(False, str(e))

    def stop(self):
        self._is_running = False

class LanguageManager:
    def __init__(self):
        self.settings = QSettings('LinTAR', 'LinTAR')
        self.current_language = self.settings.value('language', 'en')
        self.translations = {}
        self.config = configparser.ConfigParser()
        self.load_languages()

    def load_languages(self):
        if os.path.exists(LANG_FILE):
            try:
                self.config.read(LANG_FILE, encoding='utf-8')
                if self.current_language in self.config:
                    self.translations = dict(self.config[self.current_language])
                elif 'en' in self.config:
                    self.translations = dict(self.config['en'])
            except Exception as e:
                print(f"Error loading language file: {e}")

    def get_text(self, key, **kwargs):
        text = self.translations.get(key, key)
        return text.format(**kwargs) if kwargs else text

    def get_available_languages(self):
        return ['en', 'tr']

    def set_language(self, lang_code):
        if lang_code in ['en', 'tr']:
            self.current_language = lang_code
            self.settings.setValue('language', lang_code)
            self.settings.sync()
            self.load_languages()

lang_manager = LanguageManager()

# Kısayol fonksiyon
def tr(key):
    return lang_manager.get_text(key)

# Theme management
def apply_theme(app, theme_name):
    if theme_name == tr('dark_theme') or theme_name == 'Koyu':
        app.setStyleSheet("""
            QMainWindow, QDialog, QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #3d3d3d;
                selection-background-color: #0d47a1;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #2b2b2b;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 3px;
            }
            QPushButton, QToolButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: #4d4d4d;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #0d47a1;
            }
            QToolBar {
                background-color: #2b2b2b;
                border: none;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #555555;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #ffffff;
            }
            QCheckBox, QRadioButton {
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3d3d3d;
                color: #ffffff;
                padding: 5px 10px;
                border: 1px solid #555555;
            }
            QTabBar::tab:selected {
                background-color: #0d47a1;
            }
        """)
    elif theme_name == tr('light_theme') or theme_name == 'Açık':
        app.setStyleSheet("""
            QMainWindow, QDialog, QWidget {
                background-color: #f5f5f5;
                color: #000000;
            }
            QTableWidget {
                background-color: #ffffff;
                color: #000000;
                gridline-color: #e0e0e0;
                selection-background-color: #2196f3;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #d0d0d0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #c0c0c0;
                padding: 3px;
            }
            QPushButton, QToolButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #c0c0c0;
                padding: 5px;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: #d0d0d0;
            }
            QMenuBar {
                background-color: #f5f5f5;
                color: #000000;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #c0c0c0;
            }
            QMenu::item:selected {
                background-color: #2196f3;
                color: #ffffff;
            }
            QToolBar {
                background-color: #f5f5f5;
                border: none;
            }
            QGroupBox {
                color: #000000;
                border: 1px solid #c0c0c0;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #000000;
            }
            QCheckBox, QRadioButton {
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: #f5f5f5;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #000000;
                padding: 5px 10px;
                border: 1px solid #c0c0c0;
            }
            QTabBar::tab:selected {
                background-color: #2196f3;
                color: #ffffff;
            }
        """)
    else:
        app.setStyleSheet('')

# Global terminal log
terminal_log = []

def log_command(command, description=""):
    """Terminal log'una komut ekler"""
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    terminal_log.append({
        'time': timestamp,
        'command': command,
        'description': description
    })

def check_command_exists(command):
    return shutil.which(command) is not None

def get_install_commands(tool_name):
    if sys.platform.startswith('linux'):
        if tool_name == 'rar':
            return "sudo apt install rar (Debian/Ubuntu)\nsudo dnf install rar (Fedora)\nsudo pacman -S rar (Arch)"
        elif tool_name == '7z':
            return "sudo apt install p7zip-full (Debian/Ubuntu)\nsudo dnf install p7zip (Fedora)\nsudo pacman -S p7zip (Arch)"
        elif tool_name == 'zip':
            return "sudo apt install zip (Debian/Ubuntu)\nsudo dnf install zip (Fedora)\nsudo pacman -S zip (Arch)"
    elif sys.platform == 'darwin':
        return f"brew install {tool_name}"
    elif sys.platform == 'win32':
        return f"Please download and install {tool_name} from official website"
    return f"Please install {tool_name} for your system"

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(lang_manager.get_text("settings_title"))
        self.setMinimumSize(400, 300)
        self.initial_language = lang_manager.current_language
        self.selected_language = self.initial_language
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        tab_widget = QTabWidget(self)

        # General Tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)

        # Dil seçimi
        self.language_combo = QComboBox()
        available_langs = lang_manager.get_available_languages()
        lang_display_names = {"tr": "Türkçe", "en": "English"}
        
        for lang_code in available_langs:
            display_name = lang_display_names.get(lang_code, lang_code.upper())
            self.language_combo.addItem(display_name, lang_code)

        current_lang_index = self.language_combo.findData(self.initial_language)
        if current_lang_index != -1:
            self.language_combo.setCurrentIndex(current_lang_index)

        self.language_combo.currentIndexChanged.connect(self.on_language_selected)
        general_layout.addRow(QLabel(lang_manager.get_text("settings_lang_label")), self.language_combo)
        
        # Varsayılan çıkartma yolu
        self.extract_path_edit = QLineEdit(get_config_value('general', 'extract_path', os.path.expanduser('~')))
        extract_browse = QPushButton(lang_manager.get_text("browse"))
        extract_browse.clicked.connect(self.browse_extract_path)
        extract_layout = QHBoxLayout()
        extract_layout.addWidget(self.extract_path_edit)
        extract_layout.addWidget(extract_browse)
        general_layout.addRow(QLabel(lang_manager.get_text("settings_extract_path_label")), extract_layout)
        
        # Tema
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(lang_manager.get_text("system_default"), "system_default")
        self.theme_combo.addItem(lang_manager.get_text("light_theme"), "light")
        self.theme_combo.addItem(lang_manager.get_text("dark_theme"), "dark")
        saved_theme = get_config_value('general', 'theme', 'system_default')
        index = self.theme_combo.findData(saved_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        general_layout.addRow(QLabel(lang_manager.get_text("settings_theme_label")), self.theme_combo)
        
        tab_widget.addTab(general_tab, lang_manager.get_text("settings_tab_general"))

        # Compression Tab
        compression_tab = QWidget()
        comp_layout = QFormLayout(compression_tab)
        
        # Varsayılan format
        self.format_combo = QComboBox()
        self.format_combo.addItems([".tar.gz", ".zip", ".tar.bz2", ".tar.xz", ".7z", ".rar"])
        self.format_combo.setCurrentText(get_config_value('compression', 'default_format', '.tar.gz'))
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_default_format_label")), self.format_combo)

        # Sıkıştırma seviyesi
        self.compression_level_combo = QComboBox()
        self.compression_level_combo.addItems([
            lang_manager.get_text("compression_level_store"),
            lang_manager.get_text("compression_level_fast"),
            lang_manager.get_text("compression_level_normal"),
            lang_manager.get_text("compression_level_good"),
            lang_manager.get_text("compression_level_best")
        ])
        saved_level = get_config_value('compression', 'level', lang_manager.get_text("compression_level_normal"))
        self.compression_level_combo.setCurrentText(saved_level)
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_compression_level_label")), self.compression_level_combo)

        # Kurtarma kaydı
        self.recovery_checkbox = QCheckBox(lang_manager.get_text("settings_recovery_record_label_checkbox_text"))
        self.recovery_checkbox.setChecked(get_config_value('compression', 'recovery_record', 'false') == 'true')
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_recovery_record_label")), self.recovery_checkbox)

        # CPU çekirdek sayısı
        self.cpu_cores_spinbox = QSpinBox()
        self.cpu_cores_spinbox.setMinimum(1)
        max_cores = os.cpu_count() or 8
        self.cpu_cores_spinbox.setMaximum(max_cores)
        saved_cores = int(get_config_value('compression', 'cpu_cores', str(max_cores // 2 if max_cores > 1 else 1)))
        self.cpu_cores_spinbox.setValue(saved_cores)
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_cpu_cores_label")), self.cpu_cores_spinbox)

        tab_widget.addTab(compression_tab, lang_manager.get_text("settings_tab_compression"))

        # Advanced Tab
        advanced_tab = QWidget()
        advanced_layout = QFormLayout(advanced_tab)
        
        # Otomatik güncelleme kontrolü
        self.auto_update_checkbox = QCheckBox(lang_manager.get_text("auto_update"))
        self.auto_update_checkbox.setChecked(get_config_value('advanced', 'auto_update', 'true') == 'true')
        advanced_layout.addRow(self.auto_update_checkbox)
        
        # Arşiv açılışında otomatik test
        self.auto_test_checkbox = QCheckBox(lang_manager.get_text("auto_test"))
        self.auto_test_checkbox.setChecked(get_config_value('advanced', 'auto_test', 'false') == 'true')
        advanced_layout.addRow(self.auto_test_checkbox)
        
        # Geçmiş temizleme
        clear_history_btn = QPushButton("🗑️ " + lang_manager.get_text("clear_history"))
        clear_history_btn.clicked.connect(self.clear_terminal_history)
        advanced_layout.addRow(clear_history_btn)
        
        # Ayarları sıfırla
        reset_btn = QPushButton("⚠️ " + lang_manager.get_text("reset_settings"))
        reset_btn.clicked.connect(self.reset_settings)
        reset_btn.setStyleSheet("QPushButton { color: red; }")
        advanced_layout.addRow(reset_btn)
        
        tab_widget.addTab(advanced_tab, lang_manager.get_text("settings_tab_advanced"))

        main_layout.addWidget(tab_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        btn_ok = QPushButton(lang_manager.get_text("button_ok"))
        btn_ok.clicked.connect(self.accept_settings)
        button_layout.addWidget(btn_ok)

        btn_cancel = QPushButton(lang_manager.get_text("button_cancel"))
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_apply = QPushButton(lang_manager.get_text("button_apply"))
        btn_apply.clicked.connect(self.apply_settings)
        button_layout.addWidget(btn_apply)

        main_layout.addLayout(button_layout)

    def on_language_selected(self, index):
        self.selected_language = self.language_combo.itemData(index)

    def browse_extract_path(self):
        path = QFileDialog.getExistingDirectory(self, lang_manager.get_text("default_extract_path_select"), self.extract_path_edit.text())
        if path:
            self.extract_path_edit.setText(path)
    
    def clear_terminal_history(self):
        global terminal_log
        terminal_log.clear()
        QMessageBox.information(self, lang_manager.get_text("success"), lang_manager.get_text("settings_clear_history_confirm"))
    
    def reset_settings(self):
        reply = QMessageBox.question(self, lang_manager.get_text("delete_confirm"), 
                                    lang_manager.get_text("settings_reset_confirm"),
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            QMessageBox.information(self, lang_manager.get_text("success"), lang_manager.get_text("settings_reset_success"))
            self.close()
    
    def apply_settings(self):
        # Genel ayarları kaydet
        set_config_value('general', 'extract_path', self.extract_path_edit.text())
        theme_data = self.theme_combo.currentData()
        set_config_value('general', 'theme', theme_data)
        
        # Sıkıştırma ayarlarını kaydet
        set_config_value('compression', 'default_format', self.format_combo.currentText())
        set_config_value('compression', 'level', self.compression_level_combo.currentText())
        set_config_value('compression', 'recovery_record', 'true' if self.recovery_checkbox.isChecked() else 'false')
        set_config_value('compression', 'cpu_cores', str(self.cpu_cores_spinbox.value()))
        
        # Gelişmiş ayarları kaydet
        set_config_value('advanced', 'auto_update', 'true' if self.auto_update_checkbox.isChecked() else 'false')
        set_config_value('advanced', 'auto_test', 'true' if self.auto_test_checkbox.isChecked() else 'false')
        
        # Tema uygula
        if theme_data == 'light':
            apply_theme(QApplication.instance(), tr('light_theme'))
        elif theme_data == 'dark':
            apply_theme(QApplication.instance(), tr('dark_theme'))
        else:
            apply_theme(QApplication.instance(), '')
        
        # Dil değişikliği
        if self.selected_language != self.initial_language:
            lang_manager.set_language(self.selected_language)
            QMessageBox.information(self,
                                  lang_manager.get_text("message_info_title"),
                                  lang_manager.get_text("settings_language_changed_restart_prompt"))
            self.initial_language = self.selected_language
        else:
            QMessageBox.information(self,
                                  lang_manager.get_text("message_settings_apply_title"),
                                  lang_manager.get_text("settings_saved"))

    def accept_settings(self):
        self.apply_settings()
        self.accept()

class TerminalDialog(QDialog):
    def __init__(self, working_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"💻 Terminal - {working_dir}")
        self.setGeometry(200, 200, 800, 500)
        self.working_dir = working_dir
        self.command_history = []
        self.history_index = -1
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Terminal output
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Monospace', 'Courier New';
                font-size: 10pt;
                border: none;
            }
        """)
        layout.addWidget(self.output)
        
        # Input line
        input_layout = QHBoxLayout()
        self.prompt_label = QLabel("$")
        self.prompt_label.setStyleSheet("color: #4ec9b0; font-weight: bold; font-size: 10pt;")
        input_layout.addWidget(self.prompt_label)
        
        self.input = QLineEdit()
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                font-family: 'Monospace', 'Courier New';
                font-size: 10pt;
                border: 1px solid #444;
                padding: 5px;
            }
        """)
        self.input.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.input)
        
        layout.addLayout(input_layout)
        
        # Context menu
        self.output.setContextMenuPolicy(Qt.CustomContextMenu)
        self.output.customContextMenuRequested.connect(self.show_context_menu)
        
        self.append_output(f"\u250c\u2500 Terminal: {self.working_dir}\n", "#4ec9b0")
        self.append_output("│ Program İşlem Geçmişi:\n", "#569cd6")
        self.show_program_log()
        self.append_output("└\u2500$ ", "#4ec9b0")
    
    def show_program_log(self):
        """Program işlem geçmişini gösterir"""
        if terminal_log:
            for entry in terminal_log[-20:]:  # Son 20 işlem
                self.append_output(f"  [{entry['time']}] ", "#808080")
                self.append_output(f"{entry['command']}", "#ce9178")
                if entry['description']:
                    self.append_output(f" # {entry['description']}", "#6a9955")
                self.append_output("\n", "#d4d4d4")
        else:
            self.append_output(f"  {tr('no_operations')}\n", "#808080")
    
    def execute_command(self):
        command = self.input.text().strip()
        if not command:
            return
        
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        self.append_output(command + "\n", "#d4d4d4")
        self.input.clear()
        
        if command in ['exit', 'quit', 'q']:
            self.close()
            return
        
        if command == 'clear':
            self.output.clear()
            self.append_output(f"\u250c\u2500 Terminal: {self.working_dir}\n", "#4ec9b0")
            self.append_output("└\u2500$ ", "#4ec9b0")
            return
        
        if command.startswith('cd '):
            new_dir = command[3:].strip()
            if new_dir == '~':
                new_dir = os.path.expanduser('~')
            elif not os.path.isabs(new_dir):
                new_dir = os.path.join(self.working_dir, new_dir)
            
            if os.path.isdir(new_dir):
                self.working_dir = os.path.abspath(new_dir)
                self.setWindowTitle(f"💻 Terminal - {self.working_dir}")
                self.append_output(tr('terminal_dir_changed', dir=self.working_dir) + "\n", "#4ec9b0")
            else:
                self.append_output(tr('terminal_dir_not_found', dir=new_dir) + "\n", "#f48771")
            self.append_output("└\u2500$ ", "#4ec9b0")
            return
        
        # Komutu çalıştır
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                self.append_output(result.stdout, "#d4d4d4")
            if result.stderr:
                self.append_output(result.stderr, "#f48771")
            
        except subprocess.TimeoutExpired:
            self.append_output(tr('terminal_timeout') + "\n", "#f48771")
        except Exception as e:
            self.append_output(tr('terminal_error', error=str(e)) + "\n", "#f48771")
        
        self.append_output("└\u2500$ ", "#4ec9b0")
    
    def append_output(self, text, color="#d4d4d4"):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.output.setTextCursor(cursor)
        
        format = cursor.charFormat()
        from PyQt5.QtGui import QColor
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        
        cursor.insertText(text)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()
    
    def show_context_menu(self, position):
        menu = QMenu(self)
        menu.addAction(tr('copy'), self.copy_text)
        menu.addAction(tr('paste'), self.paste_text)
        menu.addAction(tr('select_all_text'), self.select_all)
        menu.addSeparator()
        menu.addAction(tr('clear_terminal'), lambda: self.input.setText('clear') or self.execute_command())
        menu.exec_(self.output.mapToGlobal(position))
    
    def copy_text(self):
        self.output.copy()
    
    def paste_text(self):
        clipboard = QApplication.clipboard()
        self.input.insert(clipboard.text())
    
    def select_all(self):
        self.output.selectAll()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            if self.history_index > 0:
                self.history_index -= 1
                self.input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key_Down:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.input.setText(self.command_history[self.history_index])
            else:
                self.history_index = len(self.command_history)
                self.input.clear()
        else:
            super().keyPressEvent(event)

class CompressionDialog(QDialog):
    def __init__(self, parent=None, current_path="~"):
        super().__init__(parent)
        self.setWindowTitle(lang_manager.get_text("compress_button"))
        self.setGeometry(200, 200, 600, 550)
        self.current_path = os.path.abspath(os.path.expanduser(current_path))
        self.selected_sources = []
        self.init_ui()
        self.update_format_specific_options(self.format_combo.currentIndex())

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # General Settings Group
        general_group = QGroupBox(lang_manager.get_text("general_settings"))
        general_layout = QFormLayout(general_group)

        # 1. Sources to Compress
        self.source_path_label = QLabel(lang_manager.get_text("sources"))
        self.source_path_display = QLineEdit(lang_manager.get_text("selected_files_folders_will_appear_here"))
        self.source_path_display.setReadOnly(True)
        btn_select_sources = QPushButton(lang_manager.get_text("browse"))
        btn_select_sources.clicked.connect(self.select_sources)

        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_path_display)
        source_layout.addWidget(btn_select_sources)
        general_layout.addRow(self.source_path_label, source_layout)

        # 2. Archive Name
        self.archive_name_label = QLabel(lang_manager.get_text("archive_name"))
        self.archive_name_edit = QLineEdit(lang_manager.get_text("default_archive_name"))
        general_layout.addRow(self.archive_name_label, self.archive_name_edit)

        # 3. Save To Directory
        self.destination_path_label = QLabel(lang_manager.get_text("save_to"))
        self.destination_path_edit = QLineEdit(self.current_path)
        self.destination_path_edit.setReadOnly(True)
        btn_select_destination = QPushButton(lang_manager.get_text("browse"))
        btn_select_destination.clicked.connect(self.select_destination)

        destination_layout = QHBoxLayout()
        destination_layout.addWidget(self.destination_path_edit)
        destination_layout.addWidget(btn_select_destination)
        general_layout.addRow(self.destination_path_label, destination_layout)

        main_layout.addWidget(general_group)

        # Compression Options Group
        compression_group = QGroupBox(lang_manager.get_text("compression_options"))
        compression_layout = QFormLayout(compression_group)

        # 1. Archive Format
        self.format_label = QLabel(lang_manager.get_text("format"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([".tar.gz", ".zip", ".tar.bz2", ".tar.xz", ".7z", ".rar"])
        self.format_combo.setCurrentText(".tar.gz")
        self.format_combo.currentIndexChanged.connect(self.update_format_specific_options)
        compression_layout.addRow(self.format_label, self.format_combo)

        # 2. Compression Level
        self.level_label = QLabel(lang_manager.get_text("compression_level"))
        self.level_combo = QComboBox()
        self.level_combo.addItems([
            lang_manager.get_text("compression_level_store"),
            lang_manager.get_text("compression_level_fast"),
            lang_manager.get_text("compression_level_normal"),
            lang_manager.get_text("compression_level_good"),
            lang_manager.get_text("compression_level_best")
        ])
        self.level_combo.setCurrentText(lang_manager.get_text("compression_level_normal"))
        compression_layout.addRow(self.level_label, self.level_combo)

        main_layout.addWidget(compression_group)

        # Encryption Options Group
        self.encryption_group = QGroupBox(lang_manager.get_text("encryption_options"))
        encryption_layout = QFormLayout(self.encryption_group)

        self.enable_encryption_checkbox = QCheckBox(lang_manager.get_text("enable_encryption"))
        self.enable_encryption_checkbox.stateChanged.connect(self.toggle_password_fields)
        encryption_layout.addRow(self.enable_encryption_checkbox)

        self.password_label = QLabel(lang_manager.get_text("password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        encryption_layout.addRow(self.password_label, self.password_input)

        self.verify_password_label = QLabel(lang_manager.get_text("verify_password"))
        self.verify_password_input = QLineEdit()
        self.verify_password_input.setEchoMode(QLineEdit.Password)
        encryption_layout.addRow(self.verify_password_label, self.verify_password_input)

        main_layout.addWidget(self.encryption_group)

        # Advanced Compression Options Group
        self.advanced_compression_group = QGroupBox(lang_manager.get_text("advanced_compression_options"))
        advanced_comp_layout = QFormLayout(self.advanced_compression_group)

        self.solid_compression_checkbox = QCheckBox(lang_manager.get_text("solid_compression"))
        advanced_comp_layout.addRow(self.solid_compression_checkbox)

        self.split_to_volumes_checkbox = QCheckBox(lang_manager.get_text("split_to_volumes"))
        self.split_volume_size_input = QLineEdit("100MB")
        self.split_volume_size_input.setEnabled(False)
        self.split_to_volumes_checkbox.stateChanged.connect(self.split_volume_size_input.setEnabled)
        advanced_comp_layout.addRow(self.split_to_volumes_checkbox, self.split_volume_size_input)

        main_layout.addWidget(self.advanced_compression_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_compress = QPushButton(lang_manager.get_text("compress_button"))
        self.btn_compress.clicked.connect(self.start_compression)
        button_layout.addWidget(self.btn_compress)

        self.btn_cancel = QPushButton(lang_manager.get_text("button_cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(button_layout)

        self.toggle_password_fields(Qt.Unchecked)

    def toggle_password_fields(self, state):
        enabled = (state == Qt.Checked)
        self.password_label.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.verify_password_label.setEnabled(enabled)
        self.verify_password_input.setEnabled(enabled)
        if not enabled:
            self.password_input.clear()
            self.verify_password_input.clear()

    def update_format_specific_options(self, index):
        selected_format = self.format_combo.currentText()

        encryption_enabled_for_format = selected_format in [".zip", ".7z", ".rar"]
        self.encryption_group.setEnabled(encryption_enabled_for_format)

        solid_compression_enabled_for_format = selected_format in [".7z", ".rar"]
        split_to_volumes_enabled_for_format = selected_format in [".7z", ".rar"]

        self.solid_compression_checkbox.setEnabled(solid_compression_enabled_for_format)
        self.split_to_volumes_checkbox.setEnabled(split_to_volumes_enabled_for_format)

    def select_sources(self):
        options = QFileDialog.DontUseNativeDialog
        start_dir = self.parent().address_bar.text() if self.parent() else self.current_path

        selected_files, _ = QFileDialog.getOpenFileNames(self,
                                              lang_manager.get_text("select_files_for_compression"),
                                              start_dir,
                                              "All Files (*);;Archive Files (*.zip *.tar.gz)",
                                              options=options)

        selected_dir = QFileDialog.getExistingDirectory(self,
                                                  lang_manager.get_text("select_directory_for_compression"),
                                                  start_dir,
                                                  options=options)

        self.selected_sources = []
        if selected_files:
            self.selected_sources.extend(selected_files)
        if selected_dir:
            if selected_dir not in self.selected_sources:
                self.selected_sources.append(selected_dir)

        if self.selected_sources:
            display_text = ", ".join([os.path.basename(p) for p in self.selected_sources])
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            self.source_path_display.setText(display_text)
        else:
            self.source_path_display.setText(lang_manager.get_text("selected_files_folders_will_appear_here"))

    def select_destination(self):
        options = QFileDialog.DontUseNativeDialog
        start_dir = self.destination_path_edit.text() if self.destination_path_edit.text() else self.current_path

        directory = QFileDialog.getExistingDirectory(self,
                                                  lang_manager.get_text("select_destination_directory"),
                                                  start_dir,
                                                  options=options)
        if directory:
            self.destination_path_edit.setText(directory)

    def _get_zip_compression_level(self, level_text):
        if level_text == lang_manager.get_text("compression_level_store"):
            return zipfile.ZIP_STORED, zlib.Z_NO_COMPRESSION
        elif level_text == lang_manager.get_text("compression_level_fast"):
            return zipfile.ZIP_DEFLATED, zlib.Z_BEST_SPEED
        elif level_text == lang_manager.get_text("compression_level_normal"):
            return zipfile.ZIP_DEFLATED, zlib.Z_DEFAULT_COMPRESSION
        elif level_text == lang_manager.get_text("compression_level_good"):
            return zipfile.ZIP_DEFLATED, 6
        elif level_text == lang_manager.get_text("compression_level_best"):
            return zipfile.ZIP_DEFLATED, zlib.Z_BEST_COMPRESSION
        return zipfile.ZIP_DEFLATED, zlib.Z_DEFAULT_COMPRESSION

    def _create_python_zip_archive(self, archive_path, sources, password=None, compression_level_text="Normal"):
        zip_compression_method, zlib_compression_level = self._get_zip_compression_level(compression_level_text)
        try:
            with zipfile.ZipFile(archive_path, 'w',
                                 compression=zip_compression_method,
                                 compresslevel=zlib_compression_level) as zf:
                if password:
                    zf.setpassword(password.encode('utf-8'))

                for source in sources:
                    if os.path.isfile(source):
                        zf.write(source, arcname=os.path.basename(source))
                    elif os.path.isdir(source):
                        for root, _, files in os.walk(source):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, os.path.dirname(source))
                                zf.write(file_path, arcname=arcname)
                    else:
                        print(f"Warning: {source} is invalid, skipping.")
            return True, None
        except Exception as e:
            return False, str(e)

    def _create_tar_archive(self, archive_path, sources, compression_mode="gz"):
        mode = f"w:{compression_mode}" if compression_mode else "w"
        try:
            with tarfile.open(archive_path, mode) as tar:
                for source in sources:
                    tar.add(source, arcname=os.path.basename(source))
            return True, None
        except Exception as e:
            return False, str(e)

    def _run_external_command(self, command_parts, cwd, password=None):
        try:
            process = subprocess.run(
                command_parts,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return True, None
        except subprocess.CalledProcessError as e:
            error_output = e.stderr if e.stderr else e.stdout
            return False, f"Command error: {error_output}"
        except FileNotFoundError:
            return False, lang_manager.get_text("external_tool_not_found", tool_name=command_parts[0])
        except Exception as e:
            return False, str(e)

    def _create_7z_archive(self, archive_path, sources, password=None, level_text="Normal", solid=False, split_volumes=None):
        command_name = "7z"
        if not check_command_exists(command_name):
            install_cmds = get_install_commands(command_name)
            QMessageBox.warning(self, lang_manager.get_text("external_tool_required_title", tool_name=command_name),
                                lang_manager.get_text("external_tool_required_text", format_name=".7z", tool_name=command_name) +
                                "\n\n" + lang_manager.get_text("external_tool_required_info", install_commands=install_cmds))
            return False, "7z program not found"

        args = ["a", archive_path]
        
        if level_text == lang_manager.get_text("compression_level_store"):
            args.extend(["-mx0"])
        elif level_text == lang_manager.get_text("compression_level_fast"):
            args.extend(["-mx1"])
        elif level_text == lang_manager.get_text("compression_level_normal"):
            args.extend(["-mx5"])
        elif level_text == lang_manager.get_text("compression_level_good"):
            args.extend(["-mx7"])
        elif level_text == lang_manager.get_text("compression_level_best"):
            args.extend(["-mx9"])

        if password:
            args.append(f"-p{password}")
            args.append("-mhe=on")

        if solid:
            args.append("-ms=on")
        
        if split_volumes:
            args.append(f"-v{split_volumes}")

        for source in sources:
            args.append(source)
        
        command_cwd = os.path.dirname(archive_path) or os.getcwd()
        return self._run_external_command([command_name] + args, command_cwd)

    def _create_rar_archive(self, archive_path, sources, password=None, level_text="Normal", solid=False, split_volumes=None):
        command_name = "rar"
        if not check_command_exists(command_name):
            install_cmds = get_install_commands(command_name)
            QMessageBox.warning(self, lang_manager.get_text("external_tool_required_title", tool_name=command_name),
                                lang_manager.get_text("external_tool_required_text", format_name=".rar", tool_name=command_name) +
                                "\n\n" + lang_manager.get_text("external_tool_required_info", install_commands=install_cmds))
            return False, "rar program not found"

        args = ["a", "-ep1"]
        
        rar_levels = {
            lang_manager.get_text("compression_level_store"): "-m0",
            lang_manager.get_text("compression_level_fast"): "-m1",
            lang_manager.get_text("compression_level_normal"): "-m3",
            lang_manager.get_text("compression_level_good"): "-m4",
            lang_manager.get_text("compression_level_best"): "-m5"
        }
        args.append(rar_levels.get(level_text, "-m3"))

        if password:
            args.append(f"-p{password}")
            args.append("-hp")

        if solid:
            args.append("-s")
        
        if split_volumes:
            args.append(f"-v{split_volumes}")

        args.append(archive_path)

        common_parent_dir = None
        if sources:
            common_parent_dir = os.path.commonpath(sources)
            if os.path.isfile(common_parent_dir):
                common_parent_dir = os.path.dirname(common_parent_dir)

            rar_sources = []
            for source in sources:
                rel_path = os.path.relpath(source, common_parent_dir)
                rar_sources.append(rel_path)
            
            args.extend(rar_sources)
        else:
            return False, lang_manager.get_text("no_sources_selected")

        command_cwd = common_parent_dir if common_parent_dir else os.getcwd()
        return self._run_external_command([command_name] + args, command_cwd)

    def start_compression(self):
        archive_name = self.archive_name_edit.text()
        destination = self.destination_path_edit.text()
        selected_format = self.format_combo.currentText()
        selected_level = self.level_combo.currentText()
        enable_encryption = self.enable_encryption_checkbox.isChecked()
        password = self.password_input.text()
        verify_password = self.verify_password_input.text()
        
        solid_compression = self.solid_compression_checkbox.isChecked()
        split_volumes = self.split_volume_size_input.text() if self.split_to_volumes_checkbox.isChecked() else None

        if not self.selected_sources:
            QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                lang_manager.get_text("no_sources_selected"))
            return

        if not archive_name:
            QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                lang_manager.get_text("archive_name_empty"))
            return

        if not destination:
             QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                 lang_manager.get_text("invalid_destination_path"))
             return

        if enable_encryption:
            if not password:
                QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                    lang_manager.get_text("password_empty"))
                return
            if password != verify_password:
                QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                    lang_manager.get_text("passwords_do_not_match"))
                return
            if len(password) < 4:
                QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                    lang_manager.get_text("password_too_short"))
                return
        
        for source_path in self.selected_sources:
            if not os.path.exists(source_path):
                QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                    lang_manager.get_text("source_file_not_found", source_path=source_path))
                return
            if not os.access(source_path, os.R_OK):
                QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                    lang_manager.get_text("source_file_no_read_permission", source_path=source_path))
                return

        full_archive_path = os.path.join(destination, archive_name + selected_format)
        
        archive_directory = os.path.dirname(full_archive_path)
        try:
            if archive_directory and not os.path.exists(archive_directory):
                os.makedirs(archive_directory, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, lang_manager.get_text("compression_error_title"),
                                 f"Error creating destination directory: '{archive_directory}'\n{e}")
            return

        success = False
        error_message = ""
        
        # Bilinmeyen format kontrolü
        if selected_format not in [".zip", ".tar.gz", ".tar.bz2", ".tar.xz", ".7z", ".rar"]:
            QMessageBox.warning(self, lang_manager.get_text("compression_error_title"),
                                lang_manager.get_text("unknown_format", format=selected_format))
            return

        # Progress dialog göster
        progress = QProgressDialog(tr('compressing', file_name=archive_name + selected_format), tr('cancel'), 0, 0, self)
        progress.setWindowTitle(tr('compress'))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        # İşlemi thread'de çalıştır
        from PyQt5.QtCore import QThread, QTimer
        
        def run_compression():
            nonlocal success, error_message
            log_command(tr('compress_started') + f": {archive_name + selected_format}", f"Format: {selected_format}, {tr('compression_level')}: {selected_level}")
            if selected_format == ".zip":
                if check_command_exists("7z"):
                    success, error_message = self._create_7z_archive(full_archive_path, self.selected_sources,
                                                                      password if enable_encryption else None,
                                                                      selected_level,
                                                                      solid_compression, split_volumes)
                else:
                    success, error_message = self._create_python_zip_archive(full_archive_path, self.selected_sources,
                                                                             password if enable_encryption else None,
                                                                             selected_level)
                
            elif selected_format == ".tar.gz":
                success, error_message = self._create_tar_archive(full_archive_path, self.selected_sources, "gz")
            elif selected_format == ".tar.bz2":
                success, error_message = self._create_tar_archive(full_archive_path, self.selected_sources, "bz2")
            elif selected_format == ".tar.xz":
                success, error_message = self._create_tar_archive(full_archive_path, self.selected_sources, "xz")
            elif selected_format == ".7z":
                success, error_message = self._create_7z_archive(full_archive_path, self.selected_sources,
                                                                  password if enable_encryption else None,
                                                                  selected_level, solid_compression, split_volumes)
            elif selected_format == ".rar":
                success, error_message = self._create_rar_archive(full_archive_path, self.selected_sources,
                                                                  password if enable_encryption else None,
                                                                  selected_level, solid_compression, split_volumes)
        
        # Thread'i başlat
        thread = Thread(target=run_compression)
        thread.start()
        
        # Thread'in bitmesini bekle
        while thread.is_alive():
            QApplication.processEvents()
            thread.join(0.1)
        
        progress.close()
        
        if success:
            log_command(tr('compress_success') + f": {archive_name + selected_format}", tr('success'))
            QMessageBox.information(self, lang_manager.get_text("compression_success_title"),
                                    lang_manager.get_text("compression_success_text", archive_name=archive_name + selected_format))
            self.accept()
        else:
            log_command(tr('compress_error') + f": {archive_name + selected_format}", f"{tr('error')}: {error_message}")
            QMessageBox.critical(self, lang_manager.get_text("compression_error_title"),
                                 lang_manager.get_text("compression_error_text", archive_name=archive_name + selected_format, error_message=error_message))

class LinTARDummyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinTAR - Archive Manager for Linux Systems (v1.0.1 Beta)")
        self.setGeometry(100, 100, 850, 600)

        # Set application icon
        app_icon_path = os.path.join(ICON_DIR, "LinTAR.png")
        if os.path.exists(app_icon_path):
            self.setWindowIcon(QIcon(app_icon_path))
        else:
            print(f"Warning: App icon not found: {app_icon_path}")

        self.history = []
        self.history_index = -1
        self.extract_worker = None
        self.extract_thread = None
        self.progress_dialog = None
        self.current_archive = None  # Şu anda açık arşiv
        self.archive_contents = []   # Arşiv içeriği

        self.init_ui()
        self.set_current_path(os.path.expanduser("~"), add_to_history=True)
        
        # Tema uygula
        saved_theme = get_config_value('general', 'theme', 'system_default')
        if saved_theme == 'light':
            apply_theme(QApplication.instance(), tr('light_theme'))
        elif saved_theme == 'dark':
            apply_theme(QApplication.instance(), tr('dark_theme'))
        else:
            apply_theme(QApplication.instance(), '')

    def init_ui(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu(lang_manager.get_text("file_menu"))
        
        new_archive_action = QAction(lang_manager.get_text("new_archive_menu"), self)
        new_archive_action.setShortcut("Ctrl+N")
        new_archive_action.triggered.connect(self.new_archive)
        file_menu.addAction(new_archive_action)
        
        open_archive_action = QAction(lang_manager.get_text("open_archive"), self)
        open_archive_action.setShortcut("Ctrl+O")
        open_archive_action.triggered.connect(self.open_archive)
        file_menu.addAction(open_archive_action)
        
        file_menu.addSeparator()
        
        save_files_action = QAction(lang_manager.get_text("save_files"), self)
        save_files_action.setShortcut("Ctrl+S")
        save_files_action.triggered.connect(self.save_files)
        file_menu.addAction(save_files_action)
        
        save_as_action = QAction(lang_manager.get_text("save_as_files"), self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_as_files)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(lang_manager.get_text("exit_app"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu(lang_manager.get_text("edit_menu"))
        
        select_action = QAction(lang_manager.get_text("select"), self)
        select_action.triggered.connect(self.select_items)
        edit_menu.addAction(select_action)
        
        select_all_action = QAction(lang_manager.get_text("select_all"), self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.select_all_items)
        edit_menu.addAction(select_all_action)
        
        edit_menu.addSeparator()
        
        rename_action = QAction(lang_manager.get_text("rename"), self)
        rename_action.setShortcut("F2")
        rename_action.triggered.connect(self.rename_item)
        edit_menu.addAction(rename_action)

        # View Menu
        view_menu = menubar.addMenu(lang_manager.get_text("view_menu"))
        
        self.large_icons_action = QAction(lang_manager.get_text("large_icons"), self)
        self.large_icons_action.setCheckable(True)
        self.large_icons_action.triggered.connect(lambda: self.set_view_mode('large'))
        view_menu.addAction(self.large_icons_action)
        
        self.small_icons_action = QAction(lang_manager.get_text("small_icons"), self)
        self.small_icons_action.setCheckable(True)
        self.small_icons_action.triggered.connect(lambda: self.set_view_mode('small'))
        view_menu.addAction(self.small_icons_action)
        
        self.list_action = QAction(lang_manager.get_text("list_view"), self)
        self.list_action.setCheckable(True)
        self.list_action.triggered.connect(lambda: self.set_view_mode('list'))
        view_menu.addAction(self.list_action)

        self.details_action = QAction(lang_manager.get_text("details_view"), self)
        self.details_action.setCheckable(True)
        self.details_action.setChecked(True)
        self.details_action.triggered.connect(lambda: self.set_view_mode('details'))
        view_menu.addAction(self.details_action)

        view_menu.addSeparator()

        self.toolbar_action = QAction(lang_manager.get_text("toolbar"), self)
        self.toolbar_action.setCheckable(True)
        self.toolbar_action.setChecked(True)
        self.toolbar_action.triggered.connect(self.toggle_toolbar)
        view_menu.addAction(self.toolbar_action)

        self.statusbar_action = QAction(lang_manager.get_text("statusbar"), self)
        self.statusbar_action.setCheckable(True)
        self.statusbar_action.setChecked(False)
        self.statusbar_action.triggered.connect(self.toggle_statusbar)
        view_menu.addAction(self.statusbar_action)

        # Help Menu
        help_menu = menubar.addMenu(lang_manager.get_text("help_menu"))
        
        help_topics_action = QAction(lang_manager.get_text("help_topics"), self)
        help_topics_action.setShortcut("F1")
        help_topics_action.triggered.connect(self.show_help_topics)
        help_menu.addAction(help_topics_action)
        
        license_action = QAction(lang_manager.get_text("license_info"), self)
        license_action.triggered.connect(self.show_license)
        help_menu.addAction(license_action)
        
        help_menu.addSeparator()
        
        about_action = QAction(lang_manager.get_text("about_lintar"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Toolbar
        self.toolbar = QToolBar(lang_manager.get_text("toolbar"))
        self.toolbar.setIconSize(QSize(64, 64))
        self.addToolBar(self.toolbar)

        # Toolbar Buttons
        self.add_toolbar_button(self.toolbar, lang_manager.get_text("compress_button"), "Compress.png", self.open_compression_dialog)
        self.add_toolbar_button(self.toolbar, lang_manager.get_text("extract_button"), "Extract.png", self.extract_selected_archive)
        self.add_toolbar_button(self.toolbar, lang_manager.get_text("test_button"), "Test.png", self.test_selected_archive)
        self.add_toolbar_button(self.toolbar, lang_manager.get_text("repair_button"), "Repair.png", self.repair_selected_archive)
        self.add_toolbar_button(self.toolbar, lang_manager.get_text("search_button"), "Search.png", self.search_in_archive)
        self.add_toolbar_button(self.toolbar, lang_manager.get_text("delete_button"), "Delete.png", self.delete_selected_files)
        self.add_toolbar_button(self.toolbar, lang_manager.get_text("info_button"), "Information.png", self.show_file_info)
        self.add_toolbar_button(self.toolbar, lang_manager.get_text("terminal_button"), "Terminal.png", self.open_terminal)

        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer_widget)

        # Language Button
        self.add_toolbar_button(self.toolbar, "Language", "Language.png", self.show_language_menu)
        
        # Settings Button
        self.add_toolbar_button(self.toolbar, lang_manager.get_text("settings_button"), "Settings.png", self.open_settings)

        # Navigation Layout
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(10, 0, 10, 0)

        nav_icon_size = QSize(24, 24)

        # Back Button
        self.back_button = QToolButton(self)
        back_icon_path = os.path.join(ICON_DIR, "back_button.png")
        if os.path.exists(back_icon_path):
            self.back_button.setIcon(QIcon(back_icon_path))
        else:
            self.back_button.setIcon(QIcon.fromTheme("go-previous"))
        self.back_button.setIconSize(nav_icon_size)
        self.back_button.setToolTip(lang_manager.get_text("back_button"))
        self.back_button.clicked.connect(self.back_button_clicked)
        nav_layout.addWidget(self.back_button)

        # Forward Button
        self.forward_button = QToolButton(self)
        forward_icon_path = os.path.join(ICON_DIR, "forward_button.png")
        if os.path.exists(forward_icon_path):
            self.forward_button.setIcon(QIcon(forward_icon_path))
        else:
            self.forward_button.setIcon(QIcon.fromTheme("go-next"))
        self.forward_button.setIconSize(nav_icon_size)
        self.forward_button.setToolTip(lang_manager.get_text("forward_button"))
        self.forward_button.clicked.connect(self.forward_button_clicked)
        nav_layout.addWidget(self.forward_button)

        # Up Button
        self.up_button = QToolButton(self)
        up_icon_path = os.path.join(ICON_DIR, "up_button.png")
        if os.path.exists(up_icon_path):
            self.up_button.setIcon(QIcon(up_icon_path))
        else:
            self.up_button.setIcon(QIcon.fromTheme("go-up"))
        self.up_button.setIconSize(nav_icon_size)
        self.up_button.setToolTip(lang_manager.get_text("up_button"))
        self.up_button.clicked.connect(self.up_button_clicked)
        nav_layout.addWidget(self.up_button)

        # Address Bar
        lbl_address = QLabel(lang_manager.get_text("address_label"))
        nav_layout.addWidget(lbl_address)

        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText(lang_manager.get_text("address_placeholder"))
        self.address_bar.setReadOnly(False)
        self.address_bar.returnPressed.connect(self.on_address_bar_return_pressed)
        self.address_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        nav_layout.addWidget(self.address_bar)

        # File List Table
        self.file_list_table = QTableWidget()
        self.file_list_table.setGridStyle(Qt.SolidLine)
        self.file_list_table.verticalHeader().setVisible(False)
        self.file_list_table.verticalHeader().setDefaultSectionSize(28)
        self.file_list_table.setColumnCount(6)
        self.file_list_table.setHorizontalHeaderLabels([
            lang_manager.get_text("table_header_name"),
            lang_manager.get_text("table_header_original_size"),
            lang_manager.get_text("table_header_compressed_size"),
            lang_manager.get_text("table_header_type"),
            lang_manager.get_text("table_header_modified_date"),
            lang_manager.get_text("table_header_compression_ratio")
        ])
        self.file_list_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.file_list_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_list_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.file_list_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.file_list_table.doubleClicked.connect(self.on_item_double_clicked)
        self.file_list_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list_table.customContextMenuRequested.connect(self.show_context_menu)

        # Main Layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.file_list_table)

        self.setCentralWidget(central_widget)

    def show_language_menu(self):
        menu = QMenu(self)
        available_langs = lang_manager.get_available_languages()
        
        for lang_code in available_langs:
            action = QAction(lang_code.upper(), self)
            action.triggered.connect(lambda checked, code=lang_code: self.change_language(code))
            menu.addAction(action)
        
        menu.exec_(QCursor.pos())

    def change_language(self, lang_code):
        lang_manager.set_language(lang_code)
        QMessageBox.information(self, tr('info_title'), tr('restart_required'))
    
    def toggle_toolbar(self):
        self.toolbar.setVisible(self.toolbar_action.isChecked())
    
    def toggle_statusbar(self):
        if self.statusbar_action.isChecked():
            self.statusBar().show()
        else:
            self.statusBar().hide()
    
    def set_view_mode(self, mode):
        # Tüm view action'ları temizle
        self.large_icons_action.setChecked(False)
        self.small_icons_action.setChecked(False)
        self.list_action.setChecked(False)
        self.details_action.setChecked(False)
        
        if mode == 'large':
            self.large_icons_action.setChecked(True)
            self.file_list_table.verticalHeader().setDefaultSectionSize(80)
            self.toolbar.setIconSize(QSize(64, 64))
            for col in range(1, 6):
                self.file_list_table.setColumnHidden(col, True)
        elif mode == 'small':
            self.small_icons_action.setChecked(True)
            self.file_list_table.verticalHeader().setDefaultSectionSize(32)
            self.toolbar.setIconSize(QSize(32, 32))
            for col in range(1, 6):
                self.file_list_table.setColumnHidden(col, True)
        elif mode == 'list':
            self.list_action.setChecked(True)
            self.file_list_table.verticalHeader().setDefaultSectionSize(24)
            self.toolbar.setIconSize(QSize(48, 48))
            self.file_list_table.setColumnHidden(1, True)
            self.file_list_table.setColumnHidden(2, True)
            self.file_list_table.setColumnHidden(3, False)
            self.file_list_table.setColumnHidden(4, True)
            self.file_list_table.setColumnHidden(5, True)
        elif mode == 'details':
            self.details_action.setChecked(True)
            self.file_list_table.verticalHeader().setDefaultSectionSize(28)
            self.toolbar.setIconSize(QSize(64, 64))
            for col in range(6):
                self.file_list_table.setColumnHidden(col, False)
        
        self.file_list_table.viewport().update()
        self.file_list_table.update()
    
    def select_items(self):
        """Dosya/klasör seçme dialogu"""
        items = []
        for row in range(self.file_list_table.rowCount()):
            item_name = self.file_list_table.item(row, 0).text()
            items.append(item_name)
        
        if not items:
            QMessageBox.information(self, "Seç", "Seçilecek öğe bulunamadı.")
            return
        
        from PyQt5.QtWidgets import QListWidget, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Öğe Seç")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        list_widget.addItems(items)
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            self.file_list_table.clearSelection()
            for item in list_widget.selectedItems():
                item_name = item.text()
                for row in range(self.file_list_table.rowCount()):
                    if self.file_list_table.item(row, 0).text() == item_name:
                        self.file_list_table.selectRow(row)
    
    def select_all_items(self):
        """Tüm öğeleri seç"""
        self.file_list_table.selectAll()
    
    def rename_item(self):
        """Seçili dosya/klasörü yeniden adlandır"""
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Yeniden Adlandır", "Lütfen yeniden adlandırılacak öğeyi seçin.")
            return
        
        if self.current_archive:
            QMessageBox.warning(self, "Yeniden Adlandır", "Arşiv içindeki öğeler yeniden adlandırılamaz.")
            return
        
        row = selected_items[0].row()
        old_name = self.file_list_table.item(row, 0).text()
        current_dir = self.address_bar.text()
        old_path = os.path.join(current_dir, old_name)
        
        new_name, ok = QInputDialog.getText(self, "Yeniden Adlandır", 
                                            f"'{old_name}' için yeni isim:", 
                                            text=old_name)
        
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(current_dir, new_name)
            
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Hata", f"'{new_name}' zaten mevcut.")
                return
            
            try:
                os.rename(old_path, new_path)
                QMessageBox.information(self, "Başarılı", f"'{old_name}' -> '{new_name}' olarak yeniden adlandırıldı.")
                self.set_current_path(current_dir, add_to_history=False)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Yeniden adlandırma başarısız: {str(e)}")
    
    def new_archive(self):
        """Yeni arşiv oluştur"""
        self.open_compression_dialog()
    
    def open_archive(self):
        """Arşiv aç"""
        archive_path, _ = QFileDialog.getOpenFileName(
            self,
            "Arşiv Aç",
            os.path.expanduser("~"),
            "Arşiv Dosyaları (*.zip *.tar *.tar.gz *.tar.bz2 *.tar.xz *.7z *.rar);;Tüm Dosyalar (*)"
        )
        
        if archive_path and os.path.isfile(archive_path):
            self.enter_archive(archive_path)
    
    def save_files(self):
        """Seçili dosyaları kaydet (arşivden çıkart)"""
        if not self.current_archive:
            QMessageBox.information(self, tr('save_title'), tr('save_not_in_archive'))
            return
        
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, tr('save_title'), tr('save_prompt'))
            return
        
        # Varsayılan çıkartma yolunu kullan
        extract_to = get_config_value('general', 'extract_path', os.path.expanduser('~'))
        
        selected_rows = set(item.row() for item in selected_items)
        filenames = [self.file_list_table.item(row, 0).text() for row in selected_rows]
        
        progress = QProgressDialog(tr('extracting_file', file_name=f"{len(filenames)} {tr('file')}"), tr('cancel'), 0, 0, self)
        progress.setWindowTitle(tr('save_title'))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        def extract_files():
            try:
                lower_path = self.current_archive.lower()
                
                if lower_path.endswith('.zip'):
                    with zipfile.ZipFile(self.current_archive, 'r') as zf:
                        for filename in filenames:
                            zf.extract(filename, extract_to)
                
                elif lower_path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')):
                    with tarfile.open(self.current_archive, 'r:*') as tf:
                        for filename in filenames:
                            member = tf.getmember(filename)
                            tf.extract(member, extract_to)
                
                elif lower_path.endswith(('.7z', '.rar')):
                    if check_command_exists('7z'):
                        cmd = ['7z', 'e', self.current_archive, f'-o{extract_to}'] + filenames
                        subprocess.run(cmd, capture_output=True, text=True)
                
            except Exception as e:
                QMessageBox.critical(self, tr('error'), tr('save_error', error=str(e)))
        
        thread = Thread(target=extract_files)
        thread.start()
        
        while thread.is_alive():
            QApplication.processEvents()
            thread.join(0.1)
        
        progress.close()
        QMessageBox.information(self, tr('success'), tr('save_success', count=len(filenames), path=extract_to))
    
    def save_as_files(self):
        """Seçili dosyaları farklı konuma kaydet"""
        if not self.current_archive:
            QMessageBox.information(self, tr('save_as_title'), tr('save_as_not_in_archive'))
            return
        
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, tr('save_as_title'), tr('save_as_prompt'))
            return
        
        extract_to = QFileDialog.getExistingDirectory(self, tr('select_extract_destination'), os.path.expanduser("~"))
        if not extract_to:
            return
        
        selected_rows = set(item.row() for item in selected_items)
        filenames = [self.file_list_table.item(row, 0).text() for row in selected_rows]
        
        progress = QProgressDialog(tr('extracting_file', file_name=f"{len(filenames)} {tr('file')}"), tr('cancel'), 0, 0, self)
        progress.setWindowTitle(tr('save_as_title'))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        def extract_files():
            try:
                lower_path = self.current_archive.lower()
                
                if lower_path.endswith('.zip'):
                    with zipfile.ZipFile(self.current_archive, 'r') as zf:
                        for filename in filenames:
                            zf.extract(filename, extract_to)
                
                elif lower_path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')):
                    with tarfile.open(self.current_archive, 'r:*') as tf:
                        for filename in filenames:
                            member = tf.getmember(filename)
                            tf.extract(member, extract_to)
                
                elif lower_path.endswith(('.7z', '.rar')):
                    if check_command_exists('7z'):
                        cmd = ['7z', 'e', self.current_archive, f'-o{extract_to}'] + filenames
                        subprocess.run(cmd, capture_output=True, text=True)
                
            except Exception as e:
                QMessageBox.critical(self, tr('error'), tr('save_error', error=str(e)))
        
        thread = Thread(target=extract_files)
        thread.start()
        
        while thread.is_alive():
            QApplication.processEvents()
            thread.join(0.1)
        
        progress.close()
        QMessageBox.information(self, tr('success'), tr('save_success', count=len(filenames), path=extract_to))
    
    def show_help_topics(self):
        """Yardım konularını göster"""
        if lang_manager.current_language == 'tr':
            help_text = """
            <html><body style='font-family: Arial, sans-serif;'>
            <h2 style='color: #2c3e50;'>📖 LinTAR Yardım</h2>
            <h3 style='color: #3498db;'>📦 Arşiv Oluşturma</h3>
            <ul>
                <li>Dosya/klasör seçin ve <b>Sıkıştır</b> butonuna tıklayın</li>
                <li>Arşiv formatını seçin (ZIP, TAR.GZ, 7Z, RAR vb.)</li>
                <li>Sıkıştırma seviyesini ayarlayın</li>
                <li>İsterseniz şifre ekleyin</li>
            </ul>
            <h3 style='color: #3498db;'>📂 Arşiv Çıkartma</h3>
            <ul>
                <li>Arşiv dosyasını seçin ve <b>Çıkart</b> butonuna tıklayın</li>
                <li>Hedef klasörü seçin</li>
                <li>Şifre korumalı arşivler için şifre girin</li>
            </ul>
            <h3 style='color: #3498db;'>🔍 Arşiv İçinde Gezinme</h3>
            <ul>
                <li>Arşiv dosyasına çift tıklayarak içine girin</li>
                <li>Klasörlere çift tıklayarak gezinin</li>
                <li><b>Yukarı</b> butonu ile geri dönün</li>
                <li>Tek dosya çıkartmak için dosyaya çift tıklayın</li>
            </ul>
            <h3 style='color: #3498db;'>⚙️ Diğer Özellikler</h3>
            <ul>
                <li><b>Test:</b> Arşiv bütünlüğünü kontrol edin</li>
                <li><b>Onar:</b> Hasarlı arşivleri onarın (RAR/7Z)</li>
                <li><b>Ara:</b> Arşiv içinde dosya arayın</li>
                <li><b>Sil:</b> Arşivden dosya silin</li>
                <li><b>Terminal:</b> Komut satırı açın</li>
            </ul>
            <h3 style='color: #3498db;'>⌨️ Kısayol Tuşları</h3>
            <ul>
                <li><b>Ctrl+N:</b> Yeni arşiv</li>
                <li><b>Ctrl+O:</b> Arşiv aç</li>
                <li><b>Ctrl+S:</b> Dosyaları kaydet</li>
                <li><b>Ctrl+A:</b> Tümünü seç</li>
                <li><b>F2:</b> Yeniden adlandır</li>
                <li><b>F1:</b> Yardım</li>
            </ul>
            </body></html>
            """
        else:
            help_text = """
            <html><body style='font-family: Arial, sans-serif;'>
            <h2 style='color: #2c3e50;'>📖 LinTAR Help</h2>
            <h3 style='color: #3498db;'>📦 Creating Archives</h3>
            <ul>
                <li>Select files/folders and click <b>Compress</b> button</li>
                <li>Choose archive format (ZIP, TAR.GZ, 7Z, RAR, etc.)</li>
                <li>Set compression level</li>
                <li>Add password if needed</li>
            </ul>
            <h3 style='color: #3498db;'>📂 Extracting Archives</h3>
            <ul>
                <li>Select archive file and click <b>Extract</b> button</li>
                <li>Choose destination folder</li>
                <li>Enter password for protected archives</li>
            </ul>
            <h3 style='color: #3498db;'>🔍 Browsing Archives</h3>
            <ul>
                <li>Double-click archive file to enter</li>
                <li>Double-click folders to navigate</li>
                <li>Use <b>Up</b> button to go back</li>
                <li>Double-click file to extract single file</li>
            </ul>
            <h3 style='color: #3498db;'>⚙️ Other Features</h3>
            <ul>
                <li><b>Test:</b> Check archive integrity</li>
                <li><b>Repair:</b> Repair damaged archives (RAR/7Z)</li>
                <li><b>Search:</b> Search files in archive</li>
                <li><b>Delete:</b> Delete files from archive</li>
                <li><b>Terminal:</b> Open command line</li>
            </ul>
            <h3 style='color: #3498db;'>⌨️ Keyboard Shortcuts</h3>
            <ul>
                <li><b>Ctrl+N:</b> New archive</li>
                <li><b>Ctrl+O:</b> Open archive</li>
                <li><b>Ctrl+S:</b> Save files</li>
                <li><b>Ctrl+A:</b> Select all</li>
                <li><b>F2:</b> Rename</li>
                <li><b>F1:</b> Help</li>
            </ul>
            </body></html>
            """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("📖 " + tr('help_title'))
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setMinimumWidth(600)
        msg.exec_()
    
    def show_license(self):
        """Lisans bilgilerini göster"""
        if lang_manager.current_language == 'tr':
            license_text = """
            <html><body style='font-family: Arial, sans-serif;'>
            <h2 style='color: #2c3e50;'>📜 LinTAR Lisans Bilgileri</h2>
            <h3 style='color: #27ae60;'>GNU General Public License v3.0</h3>
            <p style='text-align: justify;'>
            LinTAR özgür bir yazılımdır: Free Software Foundation tarafından yayınlanan
            GNU Genel Kamu Lisansı'nın 3. sürümü veya daha sonraki sürümleri kapsamında
            yeniden dağıtabilir ve/veya değiştirebilirsiniz.
            </p>
            <p style='text-align: justify;'>
            Bu program yararlı olacağı umut edilerek dağıtılmaktadır, ancak HERİHANGİ BİR GARANTİ OLMAKSIZIN;
            hatta zımni SATİLABİLİRLİK veya BELİRLİ BİR AMACA UYGUNLUK garantisi olmaksızın.
            Daha fazla ayrıntı için GNU Genel Kamu Lisansı'na bakın.
            </p>
            <p style='text-align: justify;'>
            Bu programla birlikte GNU Genel Kamu Lisansı'nın bir kopyasını almış olmalısınız.
            Almadıysanız, bkz: <a href='https://www.gnu.org/licenses/'>https://www.gnu.org/licenses/</a>
            </p>
            <hr>
            <h3 style='color: #3498db;'>Üçüncü Taraf Araçlar</h3>
            <p>LinTAR aşağıdaki harici araçları kullanır:</p>
            <ul>
                <li><b>7-Zip:</b> LGPL Lisansı</li>
                <li><b>RAR/UnRAR:</b> Ücretsiz (unrar) / Shareware (rar)</li>
                <li><b>Python:</b> PSF Lisansı</li>
                <li><b>PyQt5:</b> GPL v3</li>
            </ul>
            <p style='margin-top: 20px; color: #7f8c8d;'>
            <small>© 2025 LinTAR Projesi. Tüm hakları saklıdır.</small>
            </p>
            </body></html>
            """
        else:
            license_text = """
            <html><body style='font-family: Arial, sans-serif;'>
            <h2 style='color: #2c3e50;'>📜 LinTAR License Information</h2>
            <h3 style='color: #27ae60;'>GNU General Public License v3.0</h3>
            <p style='text-align: justify;'>
            LinTAR is free software: you can redistribute it and/or modify
            it under the terms of the GNU General Public License as published by
            the Free Software Foundation, either version 3 of the License, or
            (at your option) any later version.
            </p>
            <p style='text-align: justify;'>
            This program is distributed in the hope that it will be useful,
            but WITHOUT ANY WARRANTY; without even the implied warranty of
            MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
            GNU General Public License for more details.
            </p>
            <p style='text-align: justify;'>
            You should have received a copy of the GNU General Public License
            along with this program. If not, see 
            <a href='https://www.gnu.org/licenses/'>https://www.gnu.org/licenses/</a>
            </p>
            <hr>
            <h3 style='color: #3498db;'>Third-Party Tools</h3>
            <p>LinTAR uses the following external tools:</p>
            <ul>
                <li><b>7-Zip:</b> LGPL License</li>
                <li><b>RAR/UnRAR:</b> Freeware (unrar) / Shareware (rar)</li>
                <li><b>Python:</b> PSF License</li>
                <li><b>PyQt5:</b> GPL v3</li>
            </ul>
            <p style='margin-top: 20px; color: #7f8c8d;'>
            <small>© 2025 LinTAR Project. All rights reserved.</small>
            </p>
            </body></html>
            """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("📜 " + tr('license_title'))
        msg.setTextFormat(Qt.RichText)
        msg.setText(license_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setMinimumWidth(600)
        msg.exec_()
    
    def show_about(self):
        """Hakkında bilgilerini göster"""
        if lang_manager.current_language == 'tr':
            about_text = """
            <html><body style='font-family: Arial, sans-serif; text-align: center;'>
            <h1 style='color: #2c3e50;'>🐧 LinTAR</h1>
            <h3 style='color: #3498db;'>Linux Sistemleri için Arşiv Yöneticisi</h3>
            <p style='font-size: 14pt; margin: 20px;'>
            <b>Sürüm:</b> 1.0.1 Beta
            </p>
            <hr style='width: 80%; margin: 20px auto;'>
            <h3 style='color: #27ae60;'>👥 Geliştiriciler</h3>
            <p style='margin: 10px;'>
            <b>Konsept ve Proje Tasarımı:</b><br>
            Aydın Serhat KILIÇOĞLU (Shampuan)<br>
            <a href='https://github.com/shampuan'>github.com/shampuan</a>
            </p>
            <p style='margin: 10px;'>
            <b>Uygulama ve Kodlama:</b><br>
            Fatih ÖNDER (CekToR)<br>
            <a href='https://github.com/cektor'>github.com/cektor</a>
            </p>
            <hr style='width: 80%; margin: 20px auto;'>
            <p style='margin: 20px;'>
            <b>Lisans:</b> GPL v3.0
            </p>
            <p style='color: #e74c3c; font-weight: bold; margin: 20px; font-size: 12pt;'>
            ⚠️ Bu program hiçbir garanti getirmez.
            </p>
            <p style='color: #7f8c8d; margin-top: 30px;'>
            <small>© 2025 LinTAR Projesi. Linux kullanıcıları için ❤️ ile yapıldı.</small>
            </p>
            </body></html>
            """
        else:
            about_text = """
            <html><body style='font-family: Arial, sans-serif; text-align: center;'>
            <h1 style='color: #2c3e50;'>🐧 LinTAR</h1>
            <h3 style='color: #3498db;'>Archive Manager for Linux Systems</h3>
            <p style='font-size: 14pt; margin: 20px;'>
            <b>Version:</b> 1.0.1 Beta
            </p>
            <hr style='width: 80%; margin: 20px auto;'>
            <h3 style='color: #27ae60;'>👥 Developers</h3>
            <p style='margin: 10px;'>
            <b>Concept &amp; Project Design:</b><br>
            Aydın Serhat KILIÇOĞLU (Shampuan)<br>
            <a href='https://github.com/shampuan'>github.com/shampuan</a>
            </p>
            <p style='margin: 10px;'>
            <b>Implementation &amp; Coding:</b><br>
            Fatih ÖNDER (CekToR)<br>
            <a href='https://github.com/cektor'>github.com/cektor</a>
            </p>
            <hr style='width: 80%; margin: 20px auto;'>
            <p style='margin: 20px;'>
            <b>License:</b> GPL v3.0
            </p>
            <p style='color: #e74c3c; font-weight: bold; margin: 20px; font-size: 12pt;'>
            ⚠️ This program comes with NO WARRANTY.
            </p>
            <p style='color: #7f8c8d; margin-top: 30px;'>
            <small>© 2025 LinTAR Project. Made with ❤️ for Linux users.</small>
            </p>
            </body></html>
            """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("🐧 " + tr('about_title'))
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setMinimumWidth(650)
        msg.exec_()

    def create_dummy_action(self, text, action_id):
        action = QAction(text, self)
        action.triggered.connect(lambda: self.dummy_action(lang_manager.get_text(action_id, source_info=text)))
        return action

    def add_toolbar_button(self, toolbar, text, icon_filename, slot):
        icon_path = os.path.join(ICON_DIR, icon_filename)
        if os.path.exists(icon_path):
            button_icon = QIcon(icon_path)
        else:
            print(f"Warning: Icon file not found: {icon_path}")
            button_icon = QIcon.fromTheme("document-new")

        tool_button = QToolButton(self)
        tool_button.setText(text)
        tool_button.setIcon(button_icon)
        tool_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        tool_button.clicked.connect(slot)
        tool_button.setToolTip(text)

        toolbar.addWidget(tool_button)

    def dummy_action(self, source_info="Unknown Source"):
        QMessageBox.information(self, lang_manager.get_text("message_info_title"), 
                              lang_manager.get_text("message_info_text", source_info=source_info))

    def get_archive_original_size(self, archive_path):
        """Arşiv dosyasının orijinal (sıkıştırılmamış) boyutunu hesaplar - Windows 7-Zip gibi"""
        try:
            lower_path = archive_path.lower()
            
            # ZIP dosyaları için - Python zipfile modülü kullan
            if lower_path.endswith('.zip'):
                try:
                    with zipfile.ZipFile(archive_path, 'r') as zf:
                        total_uncompressed = 0
                        for info in zf.infolist():
                            # Sadece dosyaları say, klasörleri değil
                            if not info.is_dir():
                                total_uncompressed += info.file_size
                        return total_uncompressed
                except zipfile.BadZipFile:
                    return 0
                except Exception:
                    return 0
            
            # TAR dosyaları için - Python tarfile modülü kullan
            elif lower_path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')):
                try:
                    with tarfile.open(archive_path, 'r:*') as tf:
                        total_uncompressed = 0
                        for member in tf.getmembers():
                            # Sadece normal dosyaları say
                            if member.isfile():
                                total_uncompressed += member.size
                        return total_uncompressed
                except tarfile.TarError:
                    return 0
                except Exception:
                    return 0
            
            # 7Z ve RAR için - 7z komut satırı aracını kullan
            elif lower_path.endswith(('.7z', '.rar')):
                if not check_command_exists('7z'):
                    return 0
                    
                try:
                    # 7z l komutu ile arşiv içeriğini listele
                    result = subprocess.run(
                        ['7z', 'l', '-slt', archive_path],  # -slt: teknik liste formatı
                        capture_output=True, 
                        text=True, 
                        timeout=20,
                        check=False
                    )
                    
                    if result.returncode != 0:
                        return 0
                    
                    output = result.stdout
                    total_uncompressed = 0
                    
                    # -slt formatında her dosya için Size değerini topla
                    current_size = 0
                    is_file = True
                    
                    for line in output.split('\n'):
                        line = line.strip()
                        
                        if line.startswith('Path = '):
                            # Yeni dosya başlangıcı
                            if current_size > 0 and is_file:
                                total_uncompressed += current_size
                            current_size = 0
                            is_file = True
                            
                        elif line.startswith('Size = '):
                            try:
                                current_size = int(line.split('=', 1)[1].strip())
                            except (ValueError, IndexError):
                                current_size = 0
                                
                        elif line.startswith('Attributes = '):
                            # Klasör mü kontrol et (D attributesi)
                            attrs = line.split('=', 1)[1].strip()
                            is_file = 'D' not in attrs
                    
                    # Son dosyayı da ekle
                    if current_size > 0 and is_file:
                        total_uncompressed += current_size
                    
                    # Eğer -slt formatı çalışmazsa, normal format dene
                    if total_uncompressed == 0:
                        result2 = subprocess.run(
                            ['7z', 'l', archive_path],
                            capture_output=True,
                            text=True,
                            timeout=20,
                            check=False
                        )
                        
                        if result2.returncode == 0:
                            # Özet satırını ara
                            for line in result2.stdout.split('\n'):
                                # "X files, Y bytes" formatını ara
                                match = re.search(r'(\d+)\s+files?,\s+(\d+)\s+bytes?', line, re.IGNORECASE)
                                if match:
                                    return int(match.group(2))
                    
                    return total_uncompressed
                    
                except subprocess.TimeoutExpired:
                    return 0
                except Exception:
                    return 0
            
            # Desteklenmeyen format
            return 0
            
        except Exception:
            return 0
    
    def calculate_compression_ratio(self, original_size, compressed_size):
        """Sıkıştırma oranını hesaplar"""
        try:
            original = int(original_size)
            compressed = int(compressed_size)
            
            # Geçersiz değerler için kontrol
            if original <= 0 or compressed <= 0:
                return "N/A"
            
            # Sıkıştırma oranı hesaplama: (orijinal - sıkıştırılmış) / orijinal * 100
            ratio = ((original - compressed) / original) * 100
            
            # Negatif oran (boyut artmış) durumunda
            if ratio < 0:
                return f"+{abs(ratio):.1f}%"  # Boyut artmış
            elif ratio == 0:
                return "0.0%"
            else:
                return f"{ratio:.1f}%"
                
        except (ValueError, TypeError, ZeroDivisionError):
            return "N/A"

    def get_file_icon(self, filename, is_dir=False):
        """Dosya türüne göre sistem ikonu döndürür"""
        if is_dir:
            return QIcon.fromTheme("folder", QIcon.fromTheme("folder-open"))
        
        ext = os.path.splitext(filename)[1].lower()
        
        # Arşiv dosyaları
        if ext in ['.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar']:
            return QIcon.fromTheme("package-x-generic", QIcon.fromTheme("application-x-archive"))
        # Resim dosyaları
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico']:
            return QIcon.fromTheme("image-x-generic", QIcon.fromTheme("image"))
        # Video dosyaları
        elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']:
            return QIcon.fromTheme("video-x-generic", QIcon.fromTheme("video"))
        # Ses dosyaları
        elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a']:
            return QIcon.fromTheme("audio-x-generic", QIcon.fromTheme("audio"))
        # Metin dosyaları
        elif ext in ['.txt', '.log', '.md', '.rst']:
            return QIcon.fromTheme("text-x-generic", QIcon.fromTheme("text-plain"))
        # Kod dosyaları
        elif ext in ['.py', '.java', '.c', '.cpp', '.h', '.js', '.html', '.css', '.php', '.sh']:
            return QIcon.fromTheme("text-x-script", QIcon.fromTheme("text-x-generic"))
        # PDF dosyaları
        elif ext == '.pdf':
            return QIcon.fromTheme("application-pdf", QIcon.fromTheme("x-office-document"))
        # Office dosyaları
        elif ext in ['.doc', '.docx', '.odt']:
            return QIcon.fromTheme("x-office-document", QIcon.fromTheme("application-msword"))
        elif ext in ['.xls', '.xlsx', '.ods']:
            return QIcon.fromTheme("x-office-spreadsheet", QIcon.fromTheme("application-vnd.ms-excel"))
        elif ext in ['.ppt', '.pptx', '.odp']:
            return QIcon.fromTheme("x-office-presentation", QIcon.fromTheme("application-vnd.ms-powerpoint"))
        # Çalıştırılabilir dosyalar
        elif ext in ['.exe', '.msi', '.deb', '.rpm', '.appimage']:
            return QIcon.fromTheme("application-x-executable", QIcon.fromTheme("application-x-executable"))
        # Varsayılan
        else:
            return QIcon.fromTheme("text-x-generic", QIcon.fromTheme("unknown"))

    def set_current_path(self, path, add_to_history=True):
        absolute_path = os.path.abspath(os.path.expanduser(path))

        if not os.path.exists(absolute_path) or not os.path.isdir(absolute_path):
            QMessageBox.warning(self, lang_manager.get_text("message_invalid_path"),
                              lang_manager.get_text("message_path_not_found", path=absolute_path))
            return

        self.address_bar.setText(absolute_path)
        self.file_list_table.setRowCount(0)

        if add_to_history:
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            self.history.append(absolute_path)
            self.history_index = len(self.history) - 1

        self.update_navigation_buttons()

        try:
            items = os.listdir(absolute_path)
            dirs = sorted([item for item in items if os.path.isdir(os.path.join(absolute_path, item))])
            files = sorted([item for item in items if os.path.isfile(os.path.join(absolute_path, item))])

            sorted_items = dirs + files
            self.file_list_table.setRowCount(len(sorted_items))

            row = 0
            for item_name in sorted_items:
                item_path = os.path.join(absolute_path, item_name)

                name_item = QTableWidgetItem(item_name)
                name_item.setIcon(self.get_file_icon(item_name, os.path.isdir(item_path)))
                self.file_list_table.setItem(row, 0, name_item)

                if os.path.isdir(item_path):
                    self.file_list_table.setItem(row, 1, QTableWidgetItem(""))
                    self.file_list_table.setItem(row, 2, QTableWidgetItem(""))
                    self.file_list_table.setItem(row, 3, QTableWidgetItem(lang_manager.get_text("table_header_type_folder")))
                    self.file_list_table.setItem(row, 4, QTableWidgetItem(self.get_modified_date(item_path)))
                    self.file_list_table.setItem(row, 5, QTableWidgetItem("N/A"))
                else:
                    # Dosya boyutu (sıkıştırılmış)
                    compressed_size = os.path.getsize(item_path)
                    
                    # Arşiv mi kontrol et
                    lower_name = item_name.lower()
                    is_archive = lower_name.endswith(('.zip', '.tar.gz', '.tar.bz2', '.tar.xz', '.tar', '.rar', '.7z'))
                    
                    if is_archive:
                        # Arşiv dosyası için orijinal boyutu hesapla
                        original_size = self.get_archive_original_size(item_path)
                        
                        if original_size > 0:
                            # Orijinal boyut bulundu
                            original_size_text = self.format_size(original_size)
                            compression_ratio = self.calculate_compression_ratio(original_size, compressed_size)
                        else:
                            # Orijinal boyut bulunamadı, sıkıştırılmış boyutu göster
                            original_size_text = self.format_size(compressed_size)
                            compression_ratio = "N/A"
                    else:
                        # Normal dosya
                        original_size_text = self.format_size(compressed_size)
                        compression_ratio = "-"
                    
                    # Tabloyu doldur
                    self.file_list_table.setItem(row, 1, QTableWidgetItem(original_size_text))
                    self.file_list_table.setItem(row, 2, QTableWidgetItem(self.format_size(compressed_size)))
                    self.file_list_table.setItem(row, 3, QTableWidgetItem(self.get_file_type(item_name)))
                    self.file_list_table.setItem(row, 4, QTableWidgetItem(self.get_modified_date(item_path)))
                    self.file_list_table.setItem(row, 5, QTableWidgetItem(compression_ratio))
                
                row += 1

        except PermissionError:
            QMessageBox.warning(self, lang_manager.get_text("message_info_title"), 
                              f"No permission to access directory: '{absolute_path}'")
        except Exception as e:
            QMessageBox.critical(self, lang_manager.get_text("message_info_title"), 
                              f"Error reading directory: {e}")

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def get_modified_date(self, path):
        try:
            timestamp = os.path.getmtime(path)
            return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            return ""

    def get_file_type(self, filename):
        current_dir = self.address_bar.text()
        full_path = os.path.join(current_dir, filename)

        if os.path.isdir(full_path):
            return lang_manager.get_text("table_header_type_folder")

        name, ext = os.path.splitext(filename)
        if ext:
            return ext[1:].upper() + " File"
        return "File"

    def open_terminal(self):
        current_path = self.address_bar.text()
        if not os.path.isdir(current_path):
            current_path = os.path.expanduser("~")
        
        terminal_dialog = TerminalDialog(current_path, self)
        terminal_dialog.exec_()

    def on_item_double_clicked(self, index):
        item_name = self.file_list_table.item(index.row(), 0).text()
        item_type = self.file_list_table.item(index.row(), 3).text()
        current_dir = self.address_bar.text()
        
        if self.current_archive:
            # Arşiv içindeyiz
            if item_type == 'Klasör':
                self.navigate_into_archive_folder(item_name)
            else:
                self.extract_file_from_archive(item_name)
        else:
            new_path = os.path.join(current_dir, item_name)
            if os.path.isdir(new_path):
                self.set_current_path(new_path, add_to_history=True)
            elif item_name.lower().endswith(('.zip', '.tar.gz', '.tar.bz2', '.tar.xz', '.tar', '.rar', '.7z')):
                self.enter_archive(new_path)
            else:
                # Tüm dosya türlerini varsayılan programla aç
                try:
                    if sys.platform.startswith('linux'):
                        subprocess.Popen(['xdg-open', new_path])
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', new_path])
                    elif sys.platform == 'win32':
                        os.startfile(new_path)
                except Exception as e:
                    QMessageBox.warning(self, "Hata", f"Dosya açılamadı: {str(e)}")

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()

    def open_compression_dialog(self):
        selected_items = self.file_list_table.selectedItems()
        
        # Hiçbir dosya seçili değilse uyarı ver
        if not selected_items:
            QMessageBox.warning(self, tr('compress'), tr('select_item'))
            return
        
        selected_paths_for_dialog = []
        current_dir = self.address_bar.text()
        default_archive_name = "new_archive"  # Varsayılan isim
        
        selected_rows = set()
        for item in selected_items:
            selected_rows.add(item.row())

        for row in selected_rows:
            item_name = self.file_list_table.item(row, 0).text()
            selected_paths_for_dialog.append(os.path.join(current_dir, item_name))
        
        # Varsayılan arşiv ismini seçili dosyalara göre belirle
        if selected_paths_for_dialog:
            first_selected = os.path.basename(selected_paths_for_dialog[0])
            
            if len(selected_paths_for_dialog) == 1:
                # Tek dosya seçiliyse, o dosyanın ismini kullan (uzantısız)
                default_archive_name = os.path.splitext(first_selected)[0]
            else:
                # Birden fazla dosya seçiliyse, ilk dosyanın ismi + "_ve_digerleri"
                base_name = os.path.splitext(first_selected)[0]
                default_archive_name = f"{base_name}_ve_{len(selected_paths_for_dialog)-1}_diger"

        dialog = CompressionDialog(self, current_path=current_dir)
        
        # Varsayılan arşiv ismini ayarla
        dialog.archive_name_edit.setText(default_archive_name)

        dialog.selected_sources = selected_paths_for_dialog
        display_text = ", ".join([os.path.basename(p) for p in dialog.selected_sources])
        if len(display_text) > 50:
            display_text = display_text[:47] + "..."
        dialog.source_path_display.setText(display_text)

        if dialog.exec_() in [QDialog.Accepted, QDialog.Rejected]:
            self.set_current_path(self.address_bar.text(), add_to_history=False)
            print("Info: Compression completed, file list updated")
        else:
            print("Info: Compression canceled or failed")

    def update_navigation_buttons(self):
        if self.current_archive:
            self.back_button.setEnabled(False)
            self.forward_button.setEnabled(False)
            self.up_button.setEnabled(True)
        else:
            self.back_button.setEnabled(self.history_index > 0)
            self.forward_button.setEnabled(self.history_index < len(self.history) - 1)
            current_path = self.address_bar.text()
            parent_path = os.path.dirname(current_path)
            self.up_button.setEnabled(parent_path != current_path)

    def back_button_clicked(self):
        if self.current_archive:
            return
        if self.history_index > 0:
            self.history_index -= 1
            self.set_current_path(self.history[self.history_index], add_to_history=False)

    def forward_button_clicked(self):
        if self.current_archive:
            return
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.set_current_path(self.history[self.history_index], add_to_history=False)

    def up_button_clicked(self):
        if self.current_archive:
            if hasattr(self, 'current_archive_path') and self.current_archive_path:
                # Arşiv içinde bir seviye yukarı çık
                if '/' in self.current_archive_path:
                    self.current_archive_path = '/'.join(self.current_archive_path.split('/')[:-1])
                else:
                    self.current_archive_path = ''
                self.reload_archive_contents()
            else:
                # Arşivden tamamen çık
                archive_dir = os.path.dirname(self.current_archive)
                self.current_archive = None
                self.current_archive_path = ''
                self.archive_contents = []
                self.set_current_path(archive_dir, add_to_history=True)
        else:
            current_path = self.address_bar.text()
            parent_path = os.path.dirname(current_path)
            if parent_path != current_path and os.path.isdir(parent_path):
                self.set_current_path(parent_path, add_to_history=True)

    def extract_selected_archive(self):
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, tr('extract'), tr('select_archive'))
            return

        selected_file = self.file_list_table.item(selected_items[0].row(), 0).text()
        current_dir = self.address_bar.text()
        archive_path = os.path.join(current_dir, selected_file)

        if not os.path.isfile(archive_path):
            QMessageBox.warning(self, lang_manager.get_text("extraction_error_title"),
                                 lang_manager.get_text("invalid_archive_file"))
            return

        extract_to = QFileDialog.getExistingDirectory(self,
                                                      lang_manager.get_text("select_extract_destination"),
                                                      current_dir)
        if not extract_to:
            return

        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            tr('extracting_file', file_name=selected_file),
            tr('cancel'), 
            0, 0, self)
        self.progress_dialog.setWindowTitle(tr('extract'))
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.canceled.connect(self.cancel_extraction)

        log_command(tr('extract_started') + f": {selected_file}", f"{tr('path')}: {extract_to}")
        
        # Create worker thread
        self.extract_worker = ExtractWorker(archive_path, extract_to)
        self.extract_thread = Thread(target=self.extract_worker.run)
        
        # Connect signals
        self.extract_worker.progress.connect(self.update_progress)
        self.extract_worker.finished.connect(self.extraction_finished)
        
        # Start thread
        self.extract_thread.start()
        self.progress_dialog.show()

    @pyqtSlot(int)
    def update_progress(self, value):
        if self.progress_dialog:
            self.progress_dialog.setValue(value)

    @pyqtSlot(bool, str)
    def extraction_finished(self, success, error_message):
        if self.progress_dialog:
            self.progress_dialog.close()
        
        if success:
            archive_name = tr('archive') if not self.extract_worker else os.path.basename(self.extract_worker.archive_path)
            destination_path = tr('folder') if not self.extract_worker else self.extract_worker.extract_to
            log_command(tr('extract_success') + f": {archive_name}", tr('success'))
            QMessageBox.information(self, lang_manager.get_text("extraction_success_title"),
                                     lang_manager.get_text("extraction_success_text",
                                                           archive_name=archive_name,
                                                           destination_path=destination_path))
        else:
            archive_name = tr('archive') if not self.extract_worker else os.path.basename(self.extract_worker.archive_path)
            log_command(tr('extract_error') + f": {archive_name}", f"{tr('error')}: {error_message}")
            QMessageBox.critical(self, lang_manager.get_text("extraction_error_title"),
                                 lang_manager.get_text("extraction_error_text",
                                                       archive_name=archive_name,
                                                       error_message=error_message))
        
        self.cleanup_extraction()

    def cancel_extraction(self):
        if self.extract_worker:
            self.extract_worker.stop()
        if self.extract_thread and self.extract_thread.is_alive():
            self.extract_thread.join(timeout=1)
        
        self.cleanup_extraction()

    def cleanup_extraction(self):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        if self.extract_thread and self.extract_thread.is_alive():
            self.extract_thread.join(timeout=1)
        
        self.extract_thread = None
        self.extract_worker = None

    def on_address_bar_return_pressed(self):
        new_path = self.address_bar.text()
        self.set_current_path(new_path, add_to_history=True)
    
    def test_selected_archive(self):
        """Seçili arşivi test eder"""
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, tr('test'), tr('select_archive'))
            return
        
        selected_file = self.file_list_table.item(selected_items[0].row(), 0).text()
        current_dir = self.address_bar.text()
        archive_path = os.path.join(current_dir, selected_file)
        
        if not os.path.isfile(archive_path):
            QMessageBox.warning(self, tr('test'), tr('invalid_archive_file'))
            return
        
        # Progress dialog göster
        progress = QProgressDialog(tr('extracting_file', file_name=selected_file), tr('cancel'), 0, 0, self)
        progress.setWindowTitle(tr('test_archive'))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        success = False
        error_message = ""
        
        def run_test():
            nonlocal success, error_message
            try:
                lower_path = archive_path.lower()
                
                if lower_path.endswith('.zip'):
                    with zipfile.ZipFile(archive_path, 'r') as zf:
                        bad_file = zf.testzip()
                        success = bad_file is None
                
                elif lower_path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')):
                    with tarfile.open(archive_path, 'r:*') as tf:
                        tf.getmembers()
                        success = True
                
                elif lower_path.endswith('.7z'):
                    if check_command_exists('7z'):
                        result = subprocess.run(['7z', 't', archive_path], 
                                              capture_output=True, text=True)
                        success = result.returncode == 0
                        if not success:
                            error_message = result.stderr or "Bilinmeyen hata"
                    else:
                        error_message = tr('external_tool_not_found', tool_name='7z')
                
                elif lower_path.endswith('.rar'):
                    if check_command_exists('rar'):
                        result = subprocess.run(['rar', 't', archive_path], 
                                              capture_output=True, text=True)
                        success = result.returncode == 0
                        if not success:
                            error_message = result.stderr or tr('error')
                    else:
                        error_message = tr('external_tool_not_found', tool_name='rar')
                
                else:
                    error_message = tr('unknown_format', format=os.path.splitext(archive_path)[1])
                    
            except Exception as e:
                error_message = str(e)
        
        # Thread'i başlat
        thread = Thread(target=run_test)
        thread.start()
        
        # Thread'in bitmesini bekle
        while thread.is_alive():
            QApplication.processEvents()
            thread.join(0.1)
        
        progress.close()
        
        if success:
            QMessageBox.information(self, tr('test_archive'), tr('test_success'))
        else:
            QMessageBox.warning(self, tr('test_archive'), tr('test_error') + f"\n\n{error_message}")
    
    def repair_selected_archive(self):
        """Seçili arşivi onarır"""
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, tr('repair'), tr('select_archive'))
            return
        
        selected_file = self.file_list_table.item(selected_items[0].row(), 0).text()
        current_dir = self.address_bar.text()
        archive_path = os.path.join(current_dir, selected_file)
        
        if not os.path.isfile(archive_path):
            QMessageBox.warning(self, tr('repair'), tr('invalid_archive_file'))
            return
        
        lower_path = archive_path.lower()
        
        # Onarma sadece RAR ve 7Z için destekleniyor
        if not (lower_path.endswith('.rar') or lower_path.endswith('.7z')):
            QMessageBox.information(self, tr('repair'), tr('repair_not_supported'))
            return
        
        # Progress dialog göster
        progress = QProgressDialog(tr('extracting_file', file_name=selected_file), tr('cancel'), 0, 0, self)
        progress.setWindowTitle(tr('repair_archive'))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        success = False
        error_message = ""
        
        def run_repair():
            nonlocal success, error_message
            try:
                if lower_path.endswith('.rar'):
                    if check_command_exists('rar'):
                        result = subprocess.run(['rar', 'r', archive_path], 
                                              capture_output=True, text=True, cwd=current_dir)
                        success = result.returncode == 0
                        if not success:
                            error_message = result.stderr or "Bilinmeyen hata"
                    else:
                        error_message = "rar programı bulunamadı"
                
                elif lower_path.endswith('.7z'):
                    if check_command_exists('7z'):
                        # 7z için onarma komutu yok, sadece test yapabiliriz
                        result = subprocess.run(['7z', 't', archive_path], 
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            success = True
                            error_message = "Arşiv zaten sağlam, onarma gerekmiyor"
                        else:
                            error_message = "7Z arşivleri için otomatik onarma desteklenmiyor"
                    else:
                        error_message = tr('external_tool_not_found', tool_name='7z')
                        
            except Exception as e:
                error_message = str(e)
        
        # Thread'i başlat
        thread = Thread(target=run_repair)
        thread.start()
        
        # Thread'in bitmesini bekle
        while thread.is_alive():
            QApplication.processEvents()
            thread.join(0.1)
        
        progress.close()
        
        if success:
            QMessageBox.information(self, tr('repair_archive'), tr('repair_success'))
            self.set_current_path(current_dir, add_to_history=False)
        else:
            QMessageBox.warning(self, tr('repair_archive'), tr('repair_error') + f"\n\n{error_message}")
    
    def search_in_archive(self):
        """Görüntülenen dizinde arama yapar"""
        search_term, ok = QInputDialog.getText(self, tr('search_title'), tr('search_prompt'))
        if not ok or not search_term:
            return
        
        # Tablodaki tüm seçimleri temizle
        self.file_list_table.clearSelection()
        
        found_count = 0
        search_lower = search_term.lower()
        
        # Tablodaki her satırı kontrol et
        for row in range(self.file_list_table.rowCount()):
            item_name = self.file_list_table.item(row, 0).text()
            
            if search_lower in item_name.lower():
                # Bulunan satırı seç
                self.file_list_table.selectRow(row)
                found_count += 1
        
        if found_count > 0:
            QMessageBox.information(self, tr('search_title'), tr('search_results', count=found_count, term=search_term))
        else:
            QMessageBox.information(self, tr('search_title'), tr('no_search_results', term=search_term))
    
    def delete_selected_files(self):
        """Seçili dosyaları siler (dosya sisteminden veya arşivden)"""
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, tr('delete_title'), tr('select_item'))
            return
        
        selected_rows = set(item.row() for item in selected_items)
        file_names = []
        
        for row in selected_rows:
            file_name = self.file_list_table.item(row, 0).text()
            file_names.append(file_name)
        
        reply = QMessageBox.question(self, tr('delete_confirm'), 
                                   tr('delete_prompt', count=len(file_names)) + "\n\n" + 
                                   "\n".join(file_names[:5]) + 
                                   ("\n..." if len(file_names) > 5 else ""),
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        log_command(tr('delete') + f": {len(file_names)}", f"{tr('file')}: {', '.join(file_names[:3])}..." if len(file_names) > 3 else f"{tr('file')}: {', '.join(file_names)}")
        
        if self.current_archive:
            # Arşiv içindeyiz - arşivden sil
            self.delete_from_archive(file_names)
        else:
            # Normal dosya sistemindeyiz
            current_dir = self.address_bar.text()
            deleted_count = 0
            
            for file_name in file_names:
                file_path = os.path.join(current_dir, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        deleted_count += 1
                except Exception as e:
                    QMessageBox.warning(self, tr('error'), tr('delete_error', item=file_name, error=str(e)))
            
            if deleted_count > 0:
                log_command(tr('delete_success', count=deleted_count), tr('success'))
                QMessageBox.information(self, tr('success'), tr('delete_success', count=deleted_count))
                self.set_current_path(current_dir, add_to_history=False)
    
    def delete_from_archive(self, file_names):
        """Arşivden dosya siler"""
        if not self.current_archive:
            return
        
        progress = QProgressDialog(tr('extracting_file', file_name=f"{len(file_names)} {tr('file')}"), tr('cancel'), 0, 0, self)
        progress.setWindowTitle(tr('delete_title'))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        success = False
        error_message = ""
        
        def run_delete():
            nonlocal success, error_message
            try:
                lower_path = self.current_archive.lower()
                
                if lower_path.endswith('.zip'):
                    # ZIP için: yeni arşiv oluştur, silinmeyecekleri kopyala
                    temp_archive = self.current_archive + '.tmp'
                    with zipfile.ZipFile(self.current_archive, 'r') as zf_old:
                        with zipfile.ZipFile(temp_archive, 'w', zipfile.ZIP_DEFLATED) as zf_new:
                            for item in zf_old.infolist():
                                if item.filename not in file_names:
                                    zf_new.writestr(item, zf_old.read(item.filename))
                    os.replace(temp_archive, self.current_archive)
                    success = True
                
                elif lower_path.endswith('.7z'):
                    if check_command_exists('7z'):
                        cmd = ['7z', 'd', self.current_archive] + file_names
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        success = result.returncode == 0
                        if not success:
                            error_message = result.stderr or "Bilinmeyen hata"
                    else:
                        error_message = tr('external_tool_not_found', tool_name='7z')
                
                elif lower_path.endswith('.rar'):
                    if check_command_exists('rar'):
                        cmd = ['rar', 'd', self.current_archive] + file_names
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        success = result.returncode == 0
                        if not success:
                            error_message = result.stderr or tr('error')
                    else:
                        error_message = tr('external_tool_not_found', tool_name='rar')
                
                else:
                    error_message = tr('unknown_format', format=os.path.splitext(self.current_archive)[1])
                    
            except Exception as e:
                error_message = str(e)
        
        thread = Thread(target=run_delete)
        thread.start()
        
        while thread.is_alive():
            QApplication.processEvents()
            thread.join(0.1)
        
        progress.close()
        
        if success:
            QMessageBox.information(self, tr('success'), f"{len(file_names)} {tr('items_deleted')}.")
            # Arşivi yeniden aç
            self.enter_archive(self.current_archive)
        else:
            QMessageBox.critical(self, tr('error'), f"{tr('delete')} {tr('error')}:\n{error_message}")
    
    def navigate_into_archive_folder(self, folder_name):
        """Arşiv içinde klasöre girer"""
        # Mevcut yolu güncelle
        if not hasattr(self, 'current_archive_path'):
            self.current_archive_path = ''
        
        if self.current_archive_path:
            self.current_archive_path += '/' + folder_name
        else:
            self.current_archive_path = folder_name
        
        # Tüm öğeleri yeniden yükle ve filtrele
        self.reload_archive_contents()
    
    def reload_archive_contents(self):
        """Arşiv içeriğini mevcut yola göre yeniden yükler"""
        try:
            all_items = []
            lower_path = self.current_archive.lower()
            
            if lower_path.endswith('.zip'):
                with zipfile.ZipFile(self.current_archive, 'r') as zf:
                    for info in zf.infolist():
                        name = info.filename.rstrip('/')
                        if name:
                            all_items.append({
                                'name': name,
                                'size': info.file_size,
                                'compressed_size': info.compress_size,
                                'date': datetime.datetime(*info.date_time).strftime('%Y-%m-%d %H:%M:%S'),
                                'type': 'Klasör' if info.filename.endswith('/') or info.is_dir() else 'Dosya'
                            })
            
            elif lower_path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')):
                with tarfile.open(self.current_archive, 'r:*') as tf:
                    for member in tf.getmembers():
                        name = member.name.rstrip('/')
                        if name:
                            all_items.append({
                                'name': name,
                                'size': member.size,
                                'compressed_size': member.size,
                                'date': datetime.datetime.fromtimestamp(member.mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                'type': 'Klasör' if member.isdir() else 'Dosya'
                            })
            
            elif lower_path.endswith('.7z'):
                if check_command_exists('7z'):
                    result = subprocess.run(['7z', 'l', '-slt', self.current_archive], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.parse_7z_listing(result.stdout, all_items)
            
            elif lower_path.endswith('.rar'):
                if check_command_exists('7z'):
                    result = subprocess.run(['7z', 'l', '-slt', self.current_archive], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.parse_7z_listing(result.stdout, all_items)
                elif check_command_exists('unrar'):
                    result = subprocess.run(['unrar', 'l', self.current_archive], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.parse_unrar_listing(result.stdout, all_items)
                elif check_command_exists('rar'):
                    result = subprocess.run(['rar', 'l', self.current_archive], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.parse_unrar_listing(result.stdout, all_items)
            
            # Mevcut yoldaki öğeleri filtrele
            prefix = self.current_archive_path + '/' if self.current_archive_path else ''
            current_level_items = {}
            
            for item in all_items:
                name = item['name']
                
                if prefix:
                    if name.startswith(prefix):
                        relative_name = name[len(prefix):]
                        if '/' in relative_name:
                            folder_name = relative_name.split('/')[0]
                            if folder_name not in current_level_items:
                                current_level_items[folder_name] = {
                                    'name': folder_name,
                                    'size': 0,
                                    'compressed_size': 0,
                                    'date': item.get('date', ''),
                                    'type': 'Klasör'
                                }
                        elif relative_name:
                            item['name'] = relative_name
                            current_level_items[relative_name] = item
                else:
                    if '/' in name:
                        root_name = name.split('/')[0]
                        if root_name not in current_level_items:
                            current_level_items[root_name] = {
                                'name': root_name,
                                'size': 0,
                                'compressed_size': 0,
                                'date': item.get('date', ''),
                                'type': 'Klasör'
                            }
                    else:
                        current_level_items[name] = item
            
            self.archive_contents = list(current_level_items.values())
            path_display = f"[ARŞİV] {os.path.basename(self.current_archive)}"
            if self.current_archive_path:
                path_display += f" / {self.current_archive_path}"
            self.address_bar.setText(path_display)
            self.display_archive_contents()
            self.update_navigation_buttons()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Arşiv içeriği yüklenemedi: {str(e)}")
    
    def enter_archive(self, archive_path):
        """Arşiv içine girer"""
        try:
            all_items = []
            lower_path = archive_path.lower()
            
            if lower_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    for info in zf.infolist():
                        name = info.filename.rstrip('/')
                        if name:
                            all_items.append({
                                'name': name,
                                'size': info.file_size,
                                'compressed_size': info.compress_size,
                                'date': datetime.datetime(*info.date_time).strftime('%Y-%m-%d %H:%M:%S'),
                                'type': 'Klasör' if info.filename.endswith('/') or info.is_dir() else 'Dosya'
                            })
            
            elif lower_path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')):
                with tarfile.open(archive_path, 'r:*') as tf:
                    for member in tf.getmembers():
                        name = member.name.rstrip('/')
                        if name:
                            all_items.append({
                                'name': name,
                                'size': member.size,
                                'compressed_size': member.size,
                                'date': datetime.datetime.fromtimestamp(member.mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                'type': 'Klasör' if member.isdir() else 'Dosya'
                            })
            
            elif lower_path.endswith('.7z'):
                if check_command_exists('7z'):
                    result = subprocess.run(['7z', 'l', '-slt', archive_path], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.parse_7z_listing(result.stdout, all_items)
            
            elif lower_path.endswith('.rar'):
                if check_command_exists('7z'):
                    result = subprocess.run(['7z', 'l', '-slt', archive_path], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.parse_7z_listing(result.stdout, all_items)
                elif check_command_exists('unrar'):
                    result = subprocess.run(['unrar', 'l', archive_path], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.parse_unrar_listing(result.stdout, all_items)
                elif check_command_exists('rar'):
                    result = subprocess.run(['rar', 'l', archive_path], 
                                          capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        self.parse_unrar_listing(result.stdout, all_items)
            
            if not all_items:
                QMessageBox.warning(self, tr('warning'), tr('archive_empty'))
                return
            
            # Kök seviyedeki öğeleri topla
            root_items = {}
            for item in all_items:
                name = item['name']
                if '/' in name:
                    root_name = name.split('/')[0]
                    if root_name not in root_items:
                        root_items[root_name] = {
                            'name': root_name,
                            'size': 0,
                            'compressed_size': 0,
                            'date': item.get('date', ''),
                            'type': 'Klasör'
                        }
                else:
                    root_items[name] = item
            
            self.current_archive = archive_path
            self.current_archive_path = ''
            self.archive_contents = list(root_items.values())
            self.address_bar.setText(f"[ARŞİV] {os.path.basename(archive_path)}")
            self.display_archive_contents()
            self.update_navigation_buttons()
            
        except Exception as e:
            QMessageBox.critical(self, tr('error'), tr('archive_error', error=str(e)))
    
    def parse_7z_listing(self, output, contents):
        """7z liste çıktısını parse eder"""
        current_file = {}
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('Path = '):
                if current_file and 'name' in current_file:
                    if 'type' not in current_file:
                        current_file['type'] = 'Dosya'
                    if 'size' not in current_file:
                        current_file['size'] = 0
                    if 'compressed_size' not in current_file:
                        current_file['compressed_size'] = 0
                    if 'date' not in current_file:
                        current_file['date'] = ''
                    contents.append(current_file)
                current_file = {'name': line.split('=', 1)[1].strip().rstrip('/')}
            elif line.startswith('Size = '):
                try:
                    current_file['size'] = int(line.split('=', 1)[1].strip())
                except:
                    current_file['size'] = 0
            elif line.startswith('Packed Size = '):
                try:
                    current_file['compressed_size'] = int(line.split('=', 1)[1].strip())
                except:
                    current_file['compressed_size'] = 0
            elif line.startswith('Modified = '):
                current_file['date'] = line.split('=', 1)[1].strip()
            elif line.startswith('Attributes = ') or line.startswith('Attr = '):
                attrs = line.split('=', 1)[1].strip()
                current_file['type'] = 'Klasör' if 'D' in attrs else 'Dosya'
        
        if current_file and 'name' in current_file:
            if 'type' not in current_file:
                current_file['type'] = 'Dosya'
            if 'size' not in current_file:
                current_file['size'] = 0
            if 'compressed_size' not in current_file:
                current_file['compressed_size'] = 0
            if 'date' not in current_file:
                current_file['date'] = ''
            contents.append(current_file)
    
    def parse_unrar_listing(self, output, contents):
        """unrar/rar liste çıktısını parse eder"""
        lines = output.split('\n')
        in_file_list = False
        
        for line in lines:
            if '----------' in line or '--------' in line:
                in_file_list = not in_file_list
                continue
            
            if not in_file_list or not line.strip():
                continue
            
            # unrar -v formatı: Attributes Size Packed Ratio Date Time Name
            # Örnek: -rw-r--r-- 11410 11410 100% 01-01-25 12:00 dosya.txt
            parts = line.split()
            if len(parts) < 7:
                continue
            
            try:
                # İlk kısım attributes (örn: -rw-r--r-- veya drwxr-xr-x)
                attrs = parts[0]
                
                # Boyut bilgileri (sayısal değerler)
                size = 0
                compressed_size = 0
                date = ''
                time = ''
                name_start_idx = 1
                
                # Sayısal değerleri bul
                for i in range(1, len(parts)):
                    if parts[i].isdigit():
                        if size == 0:
                            size = int(parts[i])
                        elif compressed_size == 0:
                            compressed_size = int(parts[i])
                    elif '%' in parts[i]:
                        # Ratio atla
                        continue
                    elif '-' in parts[i] or '.' in parts[i]:
                        # Tarih bulundu
                        date_parts = parts[i].replace('.', '-').split('-')
                        if len(date_parts) == 3 and all(p.isdigit() for p in date_parts):
                            date = parts[i]
                            if i + 1 < len(parts) and ':' in parts[i + 1]:
                                time = parts[i + 1]
                                name_start_idx = i + 2
                            break
                
                # Dosya adı tarih/saatten sonra
                if name_start_idx < len(parts):
                    filename = ' '.join(parts[name_start_idx:])
                    
                    # Klasör kontrolü
                    is_dir = attrs.startswith('d') or filename.endswith('/')
                    filename = filename.rstrip('/')
                    
                    if filename:
                        contents.append({
                            'name': filename,
                            'size': size,
                            'compressed_size': compressed_size,
                            'date': f"{date} {time}",
                            'type': 'Klasör' if is_dir else 'Dosya'
                        })
            except:
                pass
    
    def display_archive_contents(self):
        """Arşiv içeriğini görüntüler"""
        self.file_list_table.setRowCount(len(self.archive_contents))
        
        for row, item in enumerate(self.archive_contents):
            name_item = QTableWidgetItem(item['name'])
            is_folder = item.get('type') == 'Klasör'
            name_item.setIcon(self.get_file_icon(item['name'], is_folder))
            self.file_list_table.setItem(row, 0, name_item)
            self.file_list_table.setItem(row, 1, QTableWidgetItem(self.format_size(item.get('size', 0))))
            self.file_list_table.setItem(row, 2, QTableWidgetItem(self.format_size(item.get('compressed_size', 0))))
            self.file_list_table.setItem(row, 3, QTableWidgetItem(item.get('type', 'Dosya')))
            self.file_list_table.setItem(row, 4, QTableWidgetItem(item.get('date', '')))
            
            if item.get('size', 0) > 0 and item.get('compressed_size', 0) > 0:
                ratio = self.calculate_compression_ratio(item['size'], item['compressed_size'])
                self.file_list_table.setItem(row, 5, QTableWidgetItem(ratio))
            else:
                self.file_list_table.setItem(row, 5, QTableWidgetItem('N/A'))
    
    def extract_file_from_archive(self, filename):
        """Arşivden dosya çıkartıp varsayılan programla açar (resim, video, pdf, ofis vb.)"""
        if not self.current_archive:
            return
        
        temp_dir = tempfile.mkdtemp(prefix='lintar_')
        
        try:
            lower_path = self.current_archive.lower()
            extracted_path = None
            
            if lower_path.endswith('.zip'):
                with zipfile.ZipFile(self.current_archive, 'r') as zf:
                    zf.extract(filename, temp_dir)
                    extracted_path = os.path.join(temp_dir, filename)
            
            elif lower_path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')):
                with tarfile.open(self.current_archive, 'r:*') as tf:
                    member = tf.getmember(filename)
                    tf.extract(member, temp_dir)
                    extracted_path = os.path.join(temp_dir, filename)
            
            elif lower_path.endswith(('.7z', '.rar')):
                if check_command_exists('7z'):
                    result = subprocess.run(['7z', 'e', self.current_archive, f'-o{temp_dir}', filename], 
                                 capture_output=True, text=True)
                    if result.returncode == 0:
                        extracted_path = os.path.join(temp_dir, os.path.basename(filename))
            
            if extracted_path and os.path.exists(extracted_path):
                if sys.platform.startswith('linux'):
                    subprocess.Popen(['xdg-open', extracted_path])
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', extracted_path])
                elif sys.platform == 'win32':
                    os.startfile(extracted_path)
            else:
                QMessageBox.warning(self, "Hata", f"'{filename}' dosyası çıkartılamadı.")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya açılamadı: {str(e)}")
    
    def show_context_menu(self, position):
        """Sağ tık menüsünü gösterir"""
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            return
        
        menu = QMenu(self)
        
        if self.current_archive:
            # Arşiv içindeyiz
            menu.addAction("Çıkart", self.extract_selected_from_archive)
            menu.addAction("Sil", self.delete_selected_files)
            menu.addSeparator()
            menu.addAction("Bilgi", self.show_file_info)
        else:
            # Normal dosya sistemi
            menu.addAction("Sıkıştır", self.open_compression_dialog)
            menu.addAction("Çıkart", self.extract_selected_archive)
            menu.addSeparator()
            menu.addAction("Sil", self.delete_selected_files)
            menu.addAction("Bilgi", self.show_file_info)
        
        menu.exec_(self.file_list_table.mapToGlobal(position))
    
    def extract_selected_from_archive(self):
        """Seçili dosyaları arşivden çıkartır"""
        selected_items = self.file_list_table.selectedItems()
        if not selected_items or not self.current_archive:
            return
        
        selected_rows = set(item.row() for item in selected_items)
        filenames = []
        
        for row in selected_rows:
            filename = self.file_list_table.item(row, 0).text()
            filenames.append(filename)
        
        extract_to = QFileDialog.getExistingDirectory(self, "Dosyaları Çıkart", os.path.expanduser("~"))
        if not extract_to:
            return
        
        # Progress dialog göster
        progress = QProgressDialog(f"Çıkartılıyor: {len(filenames)} dosya", "İptal", 0, 0, self)
        progress.setWindowTitle("Çıkartma")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        def extract_files():
            try:
                lower_path = self.current_archive.lower()
                
                if lower_path.endswith('.zip'):
                    with zipfile.ZipFile(self.current_archive, 'r') as zf:
                        for filename in filenames:
                            zf.extract(filename, extract_to)
                
                elif lower_path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tar.xz')):
                    with tarfile.open(self.current_archive, 'r:*') as tf:
                        for filename in filenames:
                            member = tf.getmember(filename)
                            tf.extract(member, extract_to)
                
                elif lower_path.endswith(('.7z', '.rar')):
                    if check_command_exists('7z'):
                        cmd = ['7z', 'e', self.current_archive, f'-o{extract_to}'] + filenames
                        subprocess.run(cmd, capture_output=True, text=True)
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosyalar çıkartılamadı: {str(e)}")
        
        # Thread'i başlat
        thread = Thread(target=extract_files)
        thread.start()
        
        # Thread'in bitmesini bekle
        while thread.is_alive():
            QApplication.processEvents()
            thread.join(0.1)
        
        progress.close()
        QMessageBox.information(self, "Başarılı", f"{len(filenames)} dosya çıkartıldı.")
    
    def show_file_info(self):
        """Seçili dosyanın bilgilerini gösterir"""
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, tr('info'), tr('select_item'))
            return
        
        row = selected_items[0].row()
        selected_file = self.file_list_table.item(row, 0).text()
        
        # Arşiv içindeyiz
        if self.current_archive:
            # Arşiv içeriğinden bilgi al
            if row < len(self.archive_contents):
                item = self.archive_contents[row]
                
                info_html = "<html><body style='font-family: Arial, sans-serif;'>"
                info_html += f"<h2 style='color: #2c3e50; margin-bottom: 15px;'>{'📁' if item.get('type') == 'Klasör' else '📄'} {selected_file}</h2>"
                info_html += "<table style='width: 100%; border-collapse: collapse;'>"
                
                info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold; width: 40%;'>{tr('type')}:</td>"
                info_html += f"<td style='padding: 8px;'>{'📁 ' + tr('folder') if item.get('type') == 'Klasör' or item.get('type') == 'Folder' else '📄 ' + tr('file')}</td></tr>"
                
                info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('archive')}:</td>"
                info_html += f"<td style='padding: 8px;'><small>{os.path.basename(self.current_archive)}</small></td></tr>"
                
                if item.get('type') not in ['Klasör', 'Folder']:
                    info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('original_size')}:</td>"
                    info_html += f"<td style='padding: 8px; color: #27ae60; font-weight: bold;'>{self.format_size(item.get('size', 0))}</td></tr>"
                    
                    info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('table_header_compressed_size')}:</td>"
                    info_html += f"<td style='padding: 8px; color: #3498db; font-weight: bold;'>{self.format_size(item.get('compressed_size', 0))}</td></tr>"
                    
                    if item.get('size', 0) > 0:
                        ratio = self.calculate_compression_ratio(item.get('size', 0), item.get('compressed_size', 0))
                        info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('compression_ratio')}:</td>"
                        info_html += f"<td style='padding: 8px; color: #e74c3c; font-weight: bold;'>{ratio}</td></tr>"
                
                if item.get('date'):
                    info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('modified')}:</td>"
                    info_html += f"<td style='padding: 8px;'>{item.get('date')}</td></tr>"
                
                info_html += "</table></body></html>"
                
                msg = QMessageBox(self)
                msg.setWindowTitle("📋 " + tr('file_info'))
                msg.setTextFormat(Qt.RichText)
                msg.setText(info_html)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setMinimumWidth(500)
                msg.exec_()
            return
        
        # Normal dosya sistemi
        current_dir = self.address_bar.text()
        file_path = os.path.join(current_dir, selected_file)
        
        try:
            stat_info = os.stat(file_path)
            is_file = os.path.isfile(file_path)
            is_archive = file_path.lower().endswith(('.zip', '.tar.gz', '.tar.bz2', '.tar.xz', '.tar', '.rar', '.7z'))
            
            # Şık HTML formatında bilgi
            info_html = "<html><body style='font-family: Arial, sans-serif;'>"
            info_html += f"<h2 style='color: #2c3e50; margin-bottom: 15px;'>📄 {selected_file}</h2>"
            info_html += "<table style='width: 100%; border-collapse: collapse;'>"
            
            # Temel bilgiler
            info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold; width: 40%;'>{tr('type')}:</td>"
            info_html += f"<td style='padding: 8px;'>{'📄 ' + tr('file') if is_file else '📁 ' + tr('folder')}</td></tr>"
            
            info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('path')}:</td>"
            info_html += f"<td style='padding: 8px;'><small>{file_path}</small></td></tr>"
            
            info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('size')}:</td>"
            info_html += f"<td style='padding: 8px; color: #27ae60; font-weight: bold;'>{self.format_size(stat_info.st_size)}</td></tr>"
            
            # Arşiv ise ek bilgiler
            if is_file and is_archive:
                original_size = self.get_archive_original_size(file_path)
                if original_size > 0:
                    info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('original_size')}:</td>"
                    info_html += f"<td style='padding: 8px; color: #3498db; font-weight: bold;'>{self.format_size(original_size)}</td></tr>"
                    
                    ratio = self.calculate_compression_ratio(original_size, stat_info.st_size)
                    info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('compression_ratio')}:</td>"
                    info_html += f"<td style='padding: 8px; color: #e74c3c; font-weight: bold;'>{ratio}</td></tr>"
            
            # Tarih bilgileri
            info_html += f"<tr><td colspan='2' style='padding: 12px 8px 4px 8px; font-weight: bold; color: #34495e;'>⏰ {tr('date_info')}</td></tr>"
            
            info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('created')}:</td>"
            info_html += f"<td style='padding: 8px;'>{datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime('%d.%m.%Y %H:%M:%S')}</td></tr>"
            
            info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('modified')}:</td>"
            info_html += f"<td style='padding: 8px;'>{datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime('%d.%m.%Y %H:%M:%S')}</td></tr>"
            
            info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('accessed')}:</td>"
            info_html += f"<td style='padding: 8px;'>{datetime.datetime.fromtimestamp(stat_info.st_atime).strftime('%d.%m.%Y %H:%M:%S')}</td></tr>"
            
            # İzinler
            info_html += f"<tr><td style='padding: 8px; background: #ecf0f1; font-weight: bold;'>{tr('permissions')}:</td>"
            info_html += f"<td style='padding: 8px; font-family: monospace;'>{oct(stat_info.st_mode)[-3:]}</td></tr>"
            
            info_html += "</table></body></html>"
            
            msg = QMessageBox(self)
            msg.setWindowTitle("📋 " + tr('file_info'))
            msg.setTextFormat(Qt.RichText)
            msg.setText(info_html)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setMinimumWidth(500)
            msg.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, tr('error'), tr('cannot_open') + f": {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LinTARDummyApp()
    window.show()
    sys.exit(app.exec_())
