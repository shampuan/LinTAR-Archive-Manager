import sys
import os
import configparser
import subprocess
import datetime
import zipfile # Python'ın dahili zip desteği için (temel)
import tarfile # Python'ın dahili tar desteği için
import zlib # ZIP sıkıştırma seviyeleri için (varsayılan olarak ZIP_DEFLATED kullanılır)
import shutil # Harici komutların varlığını kontrol etmek için

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QToolButton,
    QLineEdit, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QSizePolicy, QMenu, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog,
    QPushButton, QTabWidget,
    QGroupBox, QFormLayout, QComboBox, QCheckBox, QSpinBox,
    QFileDialog # Dosya seçim diyalogları için
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QSize

# Resimlerin ve dil dosyasının yolu
IMAGE_DIR = os.path.dirname(__file__)
LANG_FILE = os.path.join(IMAGE_DIR, "language.ini")

class LanguageManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.translations = {}
        self.current_language = "en"

        # Varsayılan İngilizce çeviriler, eğer language.ini bulunamazsa veya eksikse kullanılır
        self.default_english_translations = {
            "app_title": "LinTAR - Linux Archiver (Demo)",
            "file_menu": "File", "edit_menu": "Edit", "view_menu": "View", "help_menu": "Help",
            "new_archive_menu": "New Archive...", "open_archive": "Open Archive...",
            "save_files": "Save Files", "save_as_files": "Save As...", "exit_app": "Exit",
            "select": "Select...", "select_all": "Select All", "rename": "Rename...",
            "large_icons": "Large Icons", "small_icons": "Small Icons", "list_view": "List",
            "details_view": "Details", "toolbar": "Toolbar", "statusbar": "Statusbar",
            "help_topics": "Help Topics", "license_info": "License...", "about_lintar": "About LinTAR...",
            "compress_button": "Compress", "extract_button": "Extract", "test_button": "Test",
            "repair_button": "Repair", "search_button": "Search", "delete_button": "Delete",
            "info_button": "Info", "terminal_button": "Terminal", "settings_button": "Settings",
            "back_button": "Back", "forward_button": "Forward", "up_button": "Up One Level",
            "address_label": "Address:", "address_placeholder": "Current directory path will appear here...",
            "table_header_name": "Name", "table_header_original_size": "Original Size",
            "table_header_compressed_size": "Compressed Size", "table_header_type": "Type",
            "table_header_modified_date": "Modified Date", "table_header_compression_ratio": "Compression Ratio",
            "table_header_type_folder": "Folder",
            "message_info_title": "Info", "message_info_text": "'{source_info}' clicked!\nThis function is not yet implemented.",
            "message_terminal_title": "Terminal", "message_terminal_text": "Terminal opening function will go here.\nOn Linux, commands like 'gnome-terminal', 'konsole', 'xterm' can be used.",
            "message_settings_apply_title": "Apply", "message_settings_apply_text": "Settings applied (dummy).",
            "settings_title": "LinTAR Settings",
            "settings_tab_general": "General",
            "settings_tab_compression": "Compression",
            "settings_tab_advanced": "Advanced",
            "settings_lang_label": "Language:",
            "settings_extract_path_label": "Default Extraction Path:",
            "settings_theme_label": "Application Theme:",
            "settings_default_format_label": "Default Format:",
            "settings_compression_level_label": "Compression Level:",
            "settings_recovery_record_label": "Add Recovery Record:",
            "settings_recovery_record_label_checkbox_text": "Yes",
            "settings_cpu_cores_label": "CPU Cores:",
            "settings_advanced_tab_text": "This tab will contain advanced settings.",
            "compression_level_store": "Store only",
            "compression_level_fast": "Fast",
            "compression_level_normal": "Normal",
            "compression_level_good": "Good",
            "compression_level_best": "Best compression",
            "button_ok": "OK",
            "button_cancel": "Cancel",
            "button_apply": "Apply",
            "settings_language_changed_restart_prompt": "Language setting saved. Please restart the application for changes to take effect.",
            "message_terminal_failure_text": "No compatible terminal found or could be opened. Please ensure you have a terminal application installed on your system (e.g., gnome-terminal, konsole, xterm).",
            "message_invalid_path": "Invalid Path", "message_path_not_found": "The specified path does not exist or is not a directory: {path}",
            # Yeni sıkıştırma diyaloğu metinleri
            "general_settings": "General Settings",
            "sources": "Sources:",
            "selected_files_folders_will_appear_here": "Selected Files/Folders Will Appear Here",
            "browse": "Browse...",
            "archive_name": "Archive Name:",
            "default_archive_name": "new_archive",
            "save_to": "Save To:",
            "compression_options": "Compression Options",
            "format": "Format:",
            "compression_level": "Compression Level:",
            "select_files_for_compression": "Select Files for Compression",
            "select_directory_for_compression": "Select Directory for Compression",
            "select_destination_directory": "Select Destination Directory",
            "no_sources_selected": "No sources selected for compression.",
            "archive_name_empty": "Archive name cannot be empty.",
            "invalid_destination_path": "Invalid or empty destination path.",
            "compression_started_dummy": "Compression started (dummy).",
            # Yeni eklenen ayarlar
            "encryption_options": "Encryption Options",
            "enable_encryption": "Enable Encryption",
            "password": "Password:",
            "verify_password": "Verify Password:",
            "passwords_do_not_match": "Passwords do not match!",
            "password_too_short": "Password must be at least 4 characters long!",
            "advanced_compression_options": "Advanced Compression Options",
            "solid_compression": "Solid Compression (7z, RAR only)",
            "split_to_volumes": "Split to volumes (e.g., 100MB)",
            "compression_success_title": "Compression Success",
            "compression_success_text": "Archive '{archive_name}' successfully created!",
            "compression_error_title": "Compression Error",
            "compression_error_text": "Error creating archive '{archive_name}':\n{error_message}",
            "password_empty": "Password cannot be empty.",
            "external_tool_required_title": "{tool_name} Gerekli",
            "external_tool_required_text": "Bu arşiv formatı ({format_name}) sahiplidir ve kullanılması için **{tool_name}** programının yüklenmesi gerekir.",
            "external_tool_required_info": "Lütfen terminalden aşağıdaki komutlardan uygun olanıyla yükleyiniz:\n\n{install_commands}\n\nAncak bu program, lisans sorunları nedeniyle bu eklentilerle gelmez.",
            "external_tool_not_found": "Gerekli harici araç '{tool_name}' sisteminizde bulunamadı.",
            "unknown_format": "Bilinmeyen format: {format}",
            "source_file_not_found": "Kaynak dosya veya dizin bulunamadı: '{source_path}'\nLütfen seçilen kaynakları kontrol edin.",
            "source_file_no_read_permission": "Kaynak dosya veya dizine okuma izni yok: '{source_path}'\nLütfen dosya izinlerini kontrol edin."
        }

        self.load_languages()

    def load_languages(self):
        self.translations = self.default_english_translations

        print(f"Bilgi: Dil dosyası yolu: {LANG_FILE}")
        if os.path.exists(LANG_FILE):
            try:
                self.config.read(LANG_FILE, encoding='utf-8')
                print(f"Bilgi: '{LANG_FILE}' dosyası bulundu ve okundu.")

                if 'settings' in self.config and 'default_language' in self.config['settings']:
                    requested_lang = self.config['settings']['default_language']
                    print(f"Bilgi: language.ini dosyasında istenen dil: '{requested_lang}'")

                    if requested_lang in self.config and requested_lang != 'settings':
                        self.current_language = requested_lang
                        # Önce varsayılan İngilizceyi yükle, sonra seçilen dille üzerine yaz
                        # Böylece seçilen dilde olmayan anahtarlar için İngilizceye düşer
                        self.translations.update(self.config[self.current_language])
                        print(f"Bilgi: Dil '{self.current_language}' başarıyla yüklendi.")
                    else:
                        print(f"Uyarı: '{requested_lang}' dil bölümü '{LANG_FILE}' dosyasında bulunamadı veya geçersiz. Varsayılan İngilizce kullanılacak (fallback).")
                else:
                    print(f"Uyarı: '{LANG_FILE}' dosyasında '[settings]' bölümü veya 'default_language' anahtarı bulunamadı. Varsayılan İngilizce kullanılacak (fallback).")

            except configparser.Error as e:
                print(f"Hata: '{LANG_FILE}' dosyasını okurken bir sorun oluştu (configparser hatası): {e}. Varsayılan İngilizce kullanılacak (fallback).")
            except Exception as e:
                print(f"Beklenmeyen bir hata oluştu: {e}. Varsayılan İngilizce kullanılacak (fallback).")
        else:
            print(f"Uyarı: '{LANG_FILE}' bulunamadı. Varsayılan İngilizce metinler kullanılacak (fallback).")

    def get_text(self, key, **kwargs):
        # Önce seçilen dilde ara, yoksa varsayılan İngilizcede ara, o da yoksa MISSING_TEXT göster
        text = self.translations.get(key, self.default_english_translations.get(key, f"MISSING_TEXT_{key}"))
        return text.format(**kwargs)

    def get_available_languages(self):
        languages = []
        for section in self.config.sections():
            if section != 'settings':
                languages.append(section)
        return sorted(languages)

    def set_language(self, lang_code):
        if lang_code in self.config and lang_code != 'settings':
            self.current_language = lang_code
            self.translations = self.default_english_translations.copy() # Önce varsayılanları al
            self.translations.update(self.config[self.current_language]) # Sonra seçileni ekle
            print(f"Bilgi: Dil '{self.current_language}' olarak ayarlandı.")
            if 'settings' not in self.config:
                self.config['settings'] = {}
            self.config['settings']['default_language'] = lang_code
            try:
                with open(LANG_FILE, 'w', encoding='utf-8') as configfile:
                    self.config.write(configfile)
                print(f"Bilgi: Varsayılan dil '{lang_code}' olarak '{LANG_FILE}' dosyasına kaydedildi.")
            except Exception as e:
                print(f"Hata: Varsayılan dil kaydedilemedi: {e}")
        else:
            print(f"Uyarı: '{lang_code}' dil kodu bulunamadı veya geçersiz. Dil değiştirilmedi.")


lang_manager = LanguageManager()

def check_command_exists(command):
    """Sistemde bir komutun varlığını kontrol eder."""
    return shutil.which(command) is not None

def get_install_commands(tool_name):
    """İşletim sistemine göre kurulum komutlarını döndürür."""
    if sys.platform.startswith('linux'):
        if tool_name == 'rar':
            return "sudo apt install rar (Debian/Ubuntu)\nsudo dnf install rar (Fedora)\nsudo pacman -S rar (Arch)"
        elif tool_name == '7z': # p7zip-full paketi 7z komutunu içerir
            return "sudo apt install p7zip-full (Debian/Ubuntu)\nsudo dnf install p7zip (Fedora)\nsudo pacman -S p7zip (Arch)"
        elif tool_name == 'zip': # zip komutu genellikle çoğu sistemde varsayılan olarak gelir
            return "sudo apt install zip (Debian/Ubuntu)\nsudo dnf install zip (Fedora)\nsudo pacman -S zip (Arch)"
    elif sys.platform == 'darwin': # macOS
        return f"brew install {tool_name}"
    elif sys.platform == 'win32': # Windows
        return f"Lütfen {tool_name} programını resmi web sitesinden indirip kurunuz."
    return f"Sisteminize uygun {tool_name} programını kurmanız gerekmektedir."

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

        # 1. Genel Sekmesi
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)

        self.language_combo = QComboBox()
        available_langs = lang_manager.get_available_languages()

        lang_display_names = {
            "tr": "Türkçe",
            "en": "English",
        }

        for lang_code in available_langs:
            display_name = lang_display_names.get(lang_code, lang_code.upper())
            self.language_combo.addItem(display_name, lang_code)

        current_lang_index = self.language_combo.findData(self.initial_language)
        if current_lang_index != -1:
            self.language_combo.setCurrentIndex(current_lang_index)

        self.language_combo.currentIndexChanged.connect(self.on_language_selected)

        general_layout.addRow(QLabel(lang_manager.get_text("settings_lang_label")), self.language_combo)
        general_layout.addRow(QLabel(lang_manager.get_text("settings_extract_path_label")), QLineEdit("~/.config/LinTAR/extracted"))
        general_layout.addRow(QLabel(lang_manager.get_text("settings_theme_label")), QComboBox())
        tab_widget.addTab(general_tab, lang_manager.get_text("settings_tab_general"))

        # 2. Sıkıştırma Sekmesi
        compression_tab = QWidget()
        comp_layout = QFormLayout(compression_tab)
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_default_format_label")), QComboBox())

        compression_level_combo = QComboBox()
        compression_level_combo.addItems([
            lang_manager.get_text("compression_level_store"),
            lang_manager.get_text("compression_level_fast"),
            lang_manager.get_text("compression_level_normal"),
            lang_manager.get_text("compression_level_good"),
            lang_manager.get_text("compression_level_best")
        ])
        compression_level_combo.setCurrentText(lang_manager.get_text("compression_level_normal"))
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_compression_level_label")), compression_level_combo)

        comp_layout.addRow(QLabel(lang_manager.get_text("settings_recovery_record_label")), QCheckBox(lang_manager.get_text("settings_recovery_record_label_checkbox_text")))

        cpu_cores_spinbox = QSpinBox()
        cpu_cores_spinbox.setMinimum(1)
        max_cores = os.cpu_count() if os.cpu_count() is not None else 8
        cpu_cores_spinbox.setMaximum(max_cores)
        cpu_cores_spinbox.setValue(max_cores // 2 if max_cores > 1 else 1)
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_cpu_cores_label")), cpu_cores_spinbox)

        tab_widget.addTab(compression_tab, lang_manager.get_text("settings_tab_compression"))

        # 3. Gelişmiş Sekmesi
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        advanced_layout.addWidget(QLabel(lang_manager.get_text("settings_advanced_tab_text")))
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
        print(f"Bilgi: Ayarlar diyalogunda seçilen dil: {self.selected_language}")

    def apply_settings(self):
        if self.selected_language != self.initial_language:
            lang_manager.set_language(self.selected_language)
            QMessageBox.information(self,
                                    lang_manager.get_text("message_info_title"),
                                    lang_manager.get_text("settings_language_changed_restart_prompt"))
            self.initial_language = self.selected_language
        else:
            QMessageBox.information(self,
                                    lang_manager.get_text("message_settings_apply_title"),
                                    lang_manager.get_text("message_settings_apply_text"))

    def accept_settings(self):
        self.apply_settings()
        self.accept()


class CompressionDialog(QDialog):
    def __init__(self, parent=None, current_path="~"):
        super().__init__(parent)
        self.setWindowTitle(lang_manager.get_text("compress_button"))
        self.setGeometry(200, 200, 600, 550) # Pencere boyutunu büyüttük

        self.current_path = os.path.abspath(os.path.expanduser(current_path))
        self.selected_sources = []

        self.init_ui()
        self.update_format_specific_options(self.format_combo.currentIndex()) # Başlangıçta format ayarlarını güncelle

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Genel Bilgiler Grubu
        general_group = QGroupBox(lang_manager.get_text("general_settings"))
        general_layout = QFormLayout(general_group)

        # 1. Sıkıştırılacak Kaynaklar
        self.source_path_label = QLabel(lang_manager.get_text("sources"))
        self.source_path_display = QLineEdit(lang_manager.get_text("selected_files_folders_will_appear_here"))
        self.source_path_display.setReadOnly(True)
        btn_select_sources = QPushButton(lang_manager.get_text("browse"))
        btn_select_sources.clicked.connect(self.select_sources)

        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_path_display)
        source_layout.addWidget(btn_select_sources)
        general_layout.addRow(self.source_path_label, source_layout)

        # 2. Arşiv Adı
        self.archive_name_label = QLabel(lang_manager.get_text("archive_name"))
        self.archive_name_edit = QLineEdit(lang_manager.get_text("default_archive_name"))
        general_layout.addRow(self.archive_name_label, self.archive_name_edit)

        # 3. Kaydedilecek Dizin
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

        # Sıkıştırma Seçenekleri Grubu
        compression_group = QGroupBox(lang_manager.get_text("compression_options"))
        compression_layout = QFormLayout(compression_group)

        # 1. Arşiv Formatı
        self.format_label = QLabel(lang_manager.get_text("format"))
        self.format_combo = QComboBox()
        # Yeni formatlar eklendi
        self.format_combo.addItems([".tar.gz", ".zip", ".tar.bz2", ".tar.xz", ".7z", ".rar"])
        self.format_combo.setCurrentText(".tar.gz") # Varsayılan olarak .tar.gz
        self.format_combo.currentIndexChanged.connect(self.update_format_specific_options) # Değişiklik sinyaline bağlandı
        compression_layout.addRow(self.format_label, self.format_combo)

        # 2. Sıkıştırma Seviyesi
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

        # Şifreleme Seçenekleri Grubu
        self.encryption_group = QGroupBox(lang_manager.get_text("encryption_options"))
        encryption_layout = QFormLayout(self.encryption_group)

        self.enable_encryption_checkbox = QCheckBox(lang_manager.get_text("enable_encryption"))
        self.enable_encryption_checkbox.stateChanged.connect(self.toggle_password_fields)
        encryption_layout.addRow(self.enable_encryption_checkbox)

        self.password_label = QLabel(lang_manager.get_text("password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        encryption_layout.addRow(self.password_label, self.password_input)

        self.verify_password_label = QLabel(lang_manager.get_text("verify_password"))
        self.verify_password_input = QLineEdit()
        self.verify_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        encryption_layout.addRow(self.verify_password_label, self.verify_password_input)

        main_layout.addWidget(self.encryption_group)

        # Gelişmiş Sıkıştırma Seçenekleri Grubu
        self.advanced_compression_group = QGroupBox(lang_manager.get_text("advanced_compression_options"))
        advanced_comp_layout = QFormLayout(self.advanced_compression_group)

        self.solid_compression_checkbox = QCheckBox(lang_manager.get_text("solid_compression"))
        advanced_comp_layout.addRow(self.solid_compression_checkbox)

        self.split_to_volumes_checkbox = QCheckBox(lang_manager.get_text("split_to_volumes"))
        self.split_volume_size_input = QLineEdit("100MB") # Örnek
        self.split_volume_size_input.setEnabled(False) # Başlangıçta pasif
        self.split_to_volumes_checkbox.stateChanged.connect(self.split_volume_size_input.setEnabled)
        advanced_comp_layout.addRow(self.split_to_volumes_checkbox, self.split_volume_size_input)

        main_layout.addWidget(self.advanced_compression_group)

        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_compress = QPushButton(lang_manager.get_text("compress_button"))
        self.btn_compress.clicked.connect(self.start_compression)
        button_layout.addWidget(self.btn_compress)

        self.btn_cancel = QPushButton(lang_manager.get_text("button_cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(button_layout)

        # Başlangıçta parola alanlarını pasif yap
        self.toggle_password_fields(Qt.CheckState.Unchecked.value)


    def toggle_password_fields(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.password_label.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.verify_password_label.setEnabled(enabled)
        self.verify_password_input.setEnabled(enabled)
        if not enabled:
            self.password_input.clear()
            self.verify_password_input.clear()

    def update_format_specific_options(self, index):
        selected_format = self.format_combo.currentText()

        # Şifreleme seçenekleri
        encryption_enabled_for_format = False
        if selected_format in [".zip", ".7z", ".rar"]: # Zip (7z üzerinden), 7z ve RAR için şifreleme aktif.
            encryption_enabled_for_format = True
            self.encryption_group.setToolTip("") # Tooltip'i temizle
        else:
            self.enable_encryption_checkbox.setChecked(False) # Şifrelemeyi kapat
            # self.encryption_group.setToolTip(f"{selected_format} {lang_manager.get_text('encryption_not_supported')}")
            # Bu satır kaldırıldı, dil dosyasından gelecek.

        self.encryption_group.setEnabled(encryption_enabled_for_format)

        # Gelişmiş sıkıştırma seçenekleri (Katı sıkıştırma, ciltlere bölme)
        solid_compression_enabled_for_format = False
        split_to_volumes_enabled_for_format = False

        if selected_format in [".7z", ".rar"]:
            solid_compression_enabled_for_format = True
            split_to_volumes_enabled_for_format = True
            self.solid_compression_checkbox.setToolTip("")
        else:
            self.solid_compression_checkbox.setChecked(False) # Katı sıkıştırmayı kapat
            self.split_to_volumes_checkbox.setChecked(False) # Ciltlere bölmeyi kapat
            self.split_volume_size_input.setEnabled(False) # Inputu pasif yap
            # self.solid_compression_checkbox.setToolTip(f"{selected_format} {lang_manager.get_text('solid_compression_not_supported')}")
            # Bu satır kaldırıldı, dil dosyasından gelecek.

        self.solid_compression_checkbox.setEnabled(solid_compression_enabled_for_format)
        self.split_to_volumes_checkbox.setEnabled(split_to_volumes_enabled_for_format)


    def select_sources(self):
        options = QFileDialog.Option.DontUseNativeDialog
        start_dir = self.parent().address_bar.text() if self.parent() else self.current_path

        # Kullanıcıya hem dosya hem dizin seçme olanağı sunan bir diyalog kullanabiliriz.
        # PyQt'de tek seferde ikisini birden seçmek doğrudan bir metotla zor,
        # ancak getOpenFileNames ve getExistingDirectory'yi birleştirerek yapabiliriz.
        # Ya da sadece dizin seçimi veya çoklu dosya seçimi sunarız.
        # Şimdilik, çoklu dosya ve tek dizin seçeneğini ayrı ayrı sunalım.

        selected_files, _ = QFileDialog.getOpenFileNames(self,
                                                lang_manager.get_text("select_files_for_compression"),
                                                start_dir,
                                                "Tüm Dosyalar (*);;Arşiv Dosyaları (*.zip *.tar.gz)",
                                                options=options)

        selected_dir = QFileDialog.getExistingDirectory(self,
                                                    lang_manager.get_text("select_directory_for_compression"),
                                                    start_dir,
                                                    options=options)

        self.selected_sources = []
        if selected_files:
            self.selected_sources.extend(selected_files)
        if selected_dir:
            if selected_dir not in self.selected_sources: # Aynı dizinin iki kez eklenmemesi için
                self.selected_sources.append(selected_dir)

        if self.selected_sources:
            display_text = ", ".join([os.path.basename(p) for p in self.selected_sources])
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            self.source_path_display.setText(display_text)
        else:
            self.source_path_display.setText(lang_manager.get_text("selected_files_folders_will_appear_here"))


    def select_destination(self):
        options = QFileDialog.Option.DontUseNativeDialog
        start_dir = self.destination_path_edit.text() if self.destination_path_edit.text() else self.current_path

        directory = QFileDialog.getExistingDirectory(self,
                                                    lang_manager.get_text("select_destination_directory"),
                                                    start_dir,
                                                    options=options)
        if directory:
            self.destination_path_edit.setText(directory)

    # --- Sıkıştırma Fonksiyonları Başlangıcı ---
    def _get_zip_compression_level(self, level_text):
        # Python'ın zipfile modülü için sıkıştırma seviyeleri
        # zlib.Z_NO_COMPRESSION (0), zlib.Z_BEST_SPEED (1), zlib.Z_DEFAULT_COMPRESSION (-1), zlib.Z_BEST_COMPRESSION (9)
        if level_text == lang_manager.get_text("compression_level_store"):
            return zipfile.ZIP_STORED, zlib.Z_NO_COMPRESSION
        elif level_text == lang_manager.get_text("compression_level_fast"):
            return zipfile.ZIP_DEFLATED, zlib.Z_BEST_SPEED
        elif level_text == lang_manager.get_text("compression_level_normal"):
            return zipfile.ZIP_DEFLATED, zlib.Z_DEFAULT_COMPRESSION
        elif level_text == lang_manager.get_text("compression_level_good"):
            return zipfile.ZIP_DEFLATED, 6 # Z_DEFAULT_COMPRESSION (6) veya özel bir değer
        elif level_text == lang_manager.get_text("compression_level_best"):
            return zipfile.ZIP_DEFLATED, zlib.Z_BEST_COMPRESSION
        return zipfile.ZIP_DEFLATED, zlib.Z_DEFAULT_COMPRESSION

    def _create_python_zip_archive(self, archive_path, sources, password=None, compression_level_text="Normal"):
        """Python'ın dahili zipfile modülünü kullanarak ZIP arşivi oluşturur.
        Bu metod, parola korumasını desteklese de AES şifrelemesi gibi gelişmiş özellikleri sağlamaz."""
        zip_compression_method, zlib_compression_level = self._get_zip_compression_level(compression_level_text)
        try:
            with zipfile.ZipFile(archive_path, 'w',
                                 compression=zip_compression_method,
                                 compresslevel=zlib_compression_level) as zf:
                if password:
                    # zipfile modülünün şifreleme özelliği bytes bekler (ZipCrypto)
                    # Modern AES şifrelemesi için 7z veya pyzipper gibi harici bir kütüphane gerekir
                    zf.setpassword(password.encode('utf-8'))

                for source in sources:
                    if os.path.isfile(source):
                        zf.write(source, arcname=os.path.basename(source))
                    elif os.path.isdir(source):
                        # Dizinin kendisini eklemek için
                        for root, _, files in os.walk(source):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Arşivdeki yolu belirle
                                # Örnek: kaynak: /home/user/myfolder, dosya: /home/user/myfolder/sub/file.txt
                                # arcname: myfolder/sub/file.txt
                                arcname = os.path.relpath(file_path, os.path.dirname(source))
                                zf.write(file_path, arcname=arcname)
                    else:
                        print(f"Uyarı: {source} geçersiz bir kaynak, atlanıyor.")
            return True, None
        except Exception as e:
            return False, str(e)


    def _create_tar_archive(self, archive_path, sources, compression_mode="gz"):
        # tarfile modülü için compression_mode: 'gz', 'bz2', 'xz' veya boş (tar için)
        mode = f"w:{compression_mode}" if compression_mode else "w"
        try:
            with tarfile.open(archive_path, mode) as tar:
                for source in sources:
                    # Kaynakları arşivin kök dizinine ekle
                    tar.add(source, arcname=os.path.basename(source))
            return True, None
        except Exception as e:
            return False, str(e)

    def _run_external_command(self, command_parts, cwd, password=None):
        """Harici bir komutu çalıştırır."""
        try:
            print(f"Executing: {' '.join(command_parts)} in CWD: {cwd}") # Hata ayıklama için
            
            process = subprocess.run(
                command_parts,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True # Hata durumunda CalledProcessError fırlatır
            )
            print(f"Stdout: {process.stdout}")
            print(f"Stderr: {process.stderr}")
            return True, None
        except subprocess.CalledProcessError as e:
            # RAR'ın ve 7z'nin hata çıktısını kullanıcıya göster
            error_output = e.stderr if e.stderr else e.stdout
            return False, f"Komut hatası: {error_output}"
        except FileNotFoundError:
            # command_parts[0] komutun adıdır (örn: "7z", "rar")
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
            return False, "7z programı bulunamadı."

        args = ["a", archive_path]
        
        # Sıkıştırma seviyesi (7z için -mx)
        if level_text == lang_manager.get_text("compression_level_store"):
            args.extend(["-mx0"]) # Sadece depola
        elif level_text == lang_manager.get_text("compression_level_fast"):
            args.extend(["-mx1"]) # Hızlı
        elif level_text == lang_manager.get_text("compression_level_normal"):
            args.extend(["-mx5"]) # Normal (varsayılan 5-7 arası)
        elif level_text == lang_manager.get_text("compression_level_good"):
            args.extend(["-mx7"]) # İyi
        elif level_text == lang_manager.get_text("compression_level_best"):
            args.extend(["-mx9"]) # En iyi

        # Şifreleme
        if password:
            args.append(f"-p{password}") # Parola argümanı
            args.append("-mhe=on") # Dosya adlarını şifrele (7z için)

        # Katı sıkıştırma (sadece 7z ve RAR için)
        if solid:
            args.append("-ms=on")
        
        # Ciltlere bölme
        if split_volumes:
            args.append(f"-v{split_volumes}")

        # Kaynak dosyaları/dizinleri ekle
        # 7z, kaynakları tam yollarıyla işleyebilir
        for source in sources:
            args.append(source)
        
        # RAR'daki gibi karmaşık bir CWD yönetimine gerek yok, 7z tam yolları daha iyi işler.
        # Arşivin oluşturulacağı dizini CWD yapalım.
        command_cwd = os.path.dirname(archive_path)
        if not command_cwd: # Örneğin, sadece "arsiv.7z" ise ve CWD'den alınacaksa
            command_cwd = os.getcwd()

        return self._run_external_command([command_name] + args, command_cwd)

    def _create_rar_archive(self, archive_path, sources, password=None, level_text="Normal", solid=False, split_volumes=None):
        command_name = "rar"
        if not check_command_exists(command_name):
            install_cmds = get_install_commands(command_name)
            QMessageBox.warning(self, lang_manager.get_text("external_tool_required_title", tool_name=command_name),
                                lang_manager.get_text("external_tool_required_text", format_name=".rar", tool_name=command_name) +
                                "\n\n" + lang_manager.get_text("external_tool_required_info", install_commands=install_cmds))
            return False, "rar programı bulunamadı."

        args = ["a", "-ep1"] # a: add, -ep1: do not add empty paths (relative paths from CWD)
        
        # Sıkıştırma seviyesi (RAR için -m)
        rar_levels = {
            lang_manager.get_text("compression_level_store"): "-m0", # Sadece depola
            lang_manager.get_text("compression_level_fast"): "-m1",  # En hızlı
            lang_manager.get_text("compression_level_normal"): "-m3", # Normal
            lang_manager.get_text("compression_level_good"): "-m4",  # İyi
            lang_manager.get_text("compression_level_best"): "-m5"   # En iyi
        }
        args.append(rar_levels.get(level_text, "-m3")) # Varsayılan -m3

        # Şifreleme
        if password:
            args.append(f"-p{password}") # Parola argümanı (RAR için -p)
            args.append("-hp") # Encrypt file names (RAR header encryption)

        # Katı sıkıştırma (RAR için -s)
        if solid:
            args.append("-s")
        
        # Ciltlere bölme (RAR için -v)
        if split_volumes:
            args.append(f"-v{split_volumes}")

        # Arşiv yolu
        args.append(archive_path) # Arşivin kendisi

        # Kaynak dosyaları/dizinleri ekle
        # RAR komutu, genellikle CWD'ye göre göreceli yolları daha iyi işler.
        # Bu yüzden, sıkıştırılacak tüm kaynakların ortak bir üst dizinini bulup CWD olarak kullanacağız.
        
        common_parent_dir = None
        if sources:
            # En az bir kaynak varsa, commonpath hesapla
            # os.path.commonpath, ortak kök dizini verir.
            # Örneğin: ['/a/b/c', '/a/b/d'] -> '/a/b'
            # Eğer tek bir dosya ise, o dosyanın dizini olur.
            # Örneğin: ['/a/b/c.txt'] -> '/a/b'
            common_parent_dir = os.path.commonpath(sources)
            
            # Eğer common_parent_dir bir dosya ise (tek dosya seçildiyse)
            # o dosyanın dizinini CWD olarak almalıyız.
            if os.path.isfile(common_parent_dir):
                common_parent_dir = os.path.dirname(common_parent_dir)

            # Şimdi, kaynakları bu ortak dizine göre göreceli hale getir
            rar_sources = []
            for source in sources:
                rel_path = os.path.relpath(source, common_parent_dir)
                if os.path.isdir(source):
                    # RAR, dizinleri rekürsif olarak eklemek için sonunda / veya \* bekleyebilir.
                    # Linux'ta '/' çoğu zaman yeterlidir. Windows'ta '\*'.
                    # cross-platform uyumluluğu için basitçe rel_path'i ekleyelim.
                    rar_sources.append(rel_path)
                else:
                    rar_sources.append(rel_path)
            
            args.extend(rar_sources)
        else:
            return False, lang_manager.get_text("no_sources_selected")

        # CWD olarak ortak üst dizini kullan
        command_cwd = common_parent_dir if common_parent_dir else os.getcwd()
        
        return self._run_external_command([command_name] + args, command_cwd)

    # --- Sıkıştırma Fonksiyonları Sonu ---


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
            if len(password) < 4: # Minimum şifre uzunluğu
                QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                    lang_manager.get_text("password_too_short"))
                return
        
        # --- Kaynak dosyaların varlığını ve okunabilirliğini kontrol et ---
        for source_path in self.selected_sources:
            if not os.path.exists(source_path):
                QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                    lang_manager.get_text("source_file_not_found", source_path=source_path))
                return
            if not os.access(source_path, os.R_OK):
                QMessageBox.warning(self, lang_manager.get_text("message_info_title"),
                                    lang_manager.get_text("source_file_no_read_permission", source_path=source_path))
                return
        # --- Kaynak kontrolü sonu ---

        full_archive_path = os.path.join(destination, archive_name + selected_format)
        
        # Arşivin kaydedileceği nihai dizini al ve gerekirse oluştur
        archive_directory = os.path.dirname(full_archive_path)
        try:
            if archive_directory and not os.path.exists(archive_directory):
                os.makedirs(archive_directory, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, lang_manager.get_text("compression_error_title"),
                                 f"Hedef dizin oluşturulurken hata oluştu: '{archive_directory}'\n{e}")
            return

        success = False
        error_message = ""

        if selected_format == ".zip":
            # ZIP için 7z kullanmayı tercih edelim (daha iyi sıkıştırma/şifreleme)
            if check_command_exists("7z"):
                success, error_message = self._create_7z_archive(full_archive_path, self.selected_sources,
                                                                  password if enable_encryption else None,
                                                                  selected_level,
                                                                  solid_compression, split_volumes)
            else:
                install_cmds = get_install_commands("7z")
                QMessageBox.warning(self, lang_manager.get_text("external_tool_required_title", tool_name="7z"),
                                    lang_manager.get_text("external_tool_required_text", format_name=".zip (gelişmiş)", tool_name="7z") +
                                    "\n\n" + lang_manager.get_text("external_tool_required_info", install_commands=install_cmds))
                return
            
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
        else:
            QMessageBox.warning(self, lang_manager.get_text("compression_error_title"),
                                lang_manager.get_text("unknown_format", format=selected_format))
            return


        if success:
            QMessageBox.information(self, lang_manager.get_text("compression_success_title"),
                                    lang_manager.get_text("compression_success_text", archive_name=archive_name + selected_format))
            self.accept()
        else:
            QMessageBox.critical(self, lang_manager.get_text("compression_error_title"),
                                 lang_manager.get_text("compression_error_text", archive_name=archive_name + selected_format, error_message=error_message))


class LinTARDummyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(lang_manager.get_text("app_title"))
        self.setGeometry(100, 100, 850, 600)

        icon_path = os.path.join(IMAGE_DIR, "ZeusArchiver.png")
        self.setWindowIcon(QIcon(icon_path))

        self.history = []
        self.history_index = -1

        self.init_ui()
        self.set_current_path(os.path.expanduser("~"), add_to_history=True)

    def init_ui(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu(lang_manager.get_text("file_menu"))
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("new_archive_menu"), "new_archive_menu"))
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("open_archive"), "open_archive"))
        file_menu.addSeparator()
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("save_files"), "save_files"))
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("save_as_files"), "save_as_files"))
        file_menu.addSeparator()
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("exit_app"), "exit_app"))

        edit_menu = menubar.addMenu(lang_manager.get_text("edit_menu"))
        edit_menu.addAction(self.create_dummy_action(lang_manager.get_text("select"), "select"))
        edit_menu.addAction(self.create_dummy_action(lang_manager.get_text("select_all"), "select_all"))
        edit_menu.addSeparator()
        edit_menu.addAction(self.create_dummy_action(lang_manager.get_text("rename"), "rename"))

        view_menu = menubar.addMenu(lang_manager.get_text("view_menu"))
        view_menu.addAction(self.create_dummy_action(lang_manager.get_text("large_icons"), "large_icons"))
        view_menu.addAction(self.create_dummy_action(lang_manager.get_text("small_icons"), "small_icons"))
        view_menu.addAction(self.create_dummy_action(lang_manager.get_text("list_view"), "list_view"))

        details_action = self.create_dummy_action(lang_manager.get_text("details_view"), "details_view")
        details_action.setCheckable(True)
        details_action.setChecked(True)
        view_menu.addAction(details_action)

        view_menu.addSeparator()

        toolbar_action = self.create_dummy_action(lang_manager.get_text("toolbar"), "toggle_toolbar")
        toolbar_action.setCheckable(True)
        toolbar_action.setChecked(True)
        view_menu.addAction(toolbar_action)

        statusbar_action = self.create_dummy_action(lang_manager.get_text("statusbar"), "toggle_statusbar")
        statusbar_action.setCheckable(True)
        statusbar_action.setChecked(True)
        view_menu.addAction(statusbar_action)

        help_menu = menubar.addMenu(lang_manager.get_text("help_menu"))
        help_menu.addAction(self.create_dummy_action(lang_manager.get_text("help_topics"), "help_topics"))
        help_menu.addAction(self.create_dummy_action(lang_manager.get_text("license_info"), "license_info"))
        help_menu.addSeparator()
        help_menu.addAction(self.create_dummy_action(lang_manager.get_text("about_lintar"), "about_lintar"))

        toolbar = QToolBar(lang_manager.get_text("toolbar"))
        toolbar.setIconSize(QSize(64, 64))
        self.addToolBar(toolbar)

        self.add_toolbar_button(toolbar, lang_manager.get_text("compress_button"), "Add.png", self.open_compression_dialog)
        self.add_toolbar_button(toolbar, lang_manager.get_text("extract_button"), "Extract.png", self.extract_selected_archive)
        self.add_toolbar_button(toolbar, lang_manager.get_text("test_button"), "Test.png", lambda: self.dummy_action(lang_manager.get_text("test_button")))
        self.add_toolbar_button(toolbar, lang_manager.get_text("repair_button"), "Repair.png", lambda: self.dummy_action(lang_manager.get_text("repair_button")))
        self.add_toolbar_button(toolbar, lang_manager.get_text("search_button"), "Search.png", lambda: self.dummy_action(lang_manager.get_text("search_button")))
        self.add_toolbar_button(toolbar, lang_manager.get_text("delete_button"), "Delete.png", lambda: self.dummy_action(lang_manager.get_text("delete_button")))
        self.add_toolbar_button(toolbar, lang_manager.get_text("info_button"), "Information.png", lambda: self.dummy_action(lang_manager.get_text("info_button")))

        self.add_toolbar_button(toolbar, lang_manager.get_text("terminal_button"), "Terminal.png", self.open_terminal)

        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer_widget)

        self.add_toolbar_button(toolbar, lang_manager.get_text("settings_button"), "Settings.png", self.open_settings)

        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(10, 0, 10, 0)

        nav_icon_size = QSize(24, 24)

        self.back_button = QToolButton(self)
        self.back_button.setIcon(QIcon.fromTheme("go-previous", QIcon(os.path.join(IMAGE_DIR, "back_arrow.png") if os.path.exists(os.path.join(IMAGE_DIR, "back_arrow.png")) else "")))
        self.back_button.setIconSize(nav_icon_size)
        self.back_button.setToolTip(lang_manager.get_text("back_button"))
        self.back_button.clicked.connect(self.back_button_clicked)
        nav_layout.addWidget(self.back_button)

        self.forward_button = QToolButton(self)
        self.forward_button.setIcon(QIcon.fromTheme("go-next", QIcon(os.path.join(IMAGE_DIR, "forward_arrow.png") if os.path.exists(os.path.join(IMAGE_DIR, "forward_arrow.png")) else "")))
        self.forward_button.setIconSize(nav_icon_size)
        self.forward_button.setToolTip(lang_manager.get_text("forward_button"))
        self.forward_button.clicked.connect(self.forward_button_clicked)
        nav_layout.addWidget(self.forward_button)

        self.up_button = QToolButton(self)
        self.up_button.setIcon(QIcon.fromTheme("go-up", QIcon(os.path.join(IMAGE_DIR, "up_arrow.png") if os.path.exists(os.path.join(IMAGE_DIR, "up_arrow.png")) else "")))
        self.up_button.setIconSize(nav_icon_size)
        self.up_button.setToolTip(lang_manager.get_text("up_button"))
        self.up_button.clicked.connect(self.up_button_clicked)
        nav_layout.addWidget(self.up_button)

        lbl_address = QLabel(lang_manager.get_text("address_label"))
        nav_layout.addWidget(lbl_address)

        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText(lang_manager.get_text("address_placeholder"))
        self.address_bar.setReadOnly(False)
        self.address_bar.returnPressed.connect(self.on_address_bar_return_pressed)
        self.address_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        nav_layout.addWidget(self.address_bar)

        self.file_list_table = QTableWidget()

        self.file_list_table.setGridStyle(Qt.PenStyle.SolidLine)
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

        self.file_list_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.file_list_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_list_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

        self.file_list_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_list_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.file_list_table.doubleClicked.connect(self.on_item_double_clicked)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.file_list_table)

        self.setCentralWidget(central_widget)

        self.update_navigation_buttons()

    def create_dummy_action(self, text, action_id):
        action = QAction(text, self)
        action.triggered.connect(lambda: self.dummy_action(lang_manager.get_text(action_id, source_info=text)))
        return action

    def add_toolbar_button(self, toolbar, text, icon_filename, slot):
        icon_path = os.path.join(IMAGE_DIR, icon_filename)
        button_icon = QIcon(icon_path)

        tool_button = QToolButton(self)
        tool_button.setText(text)
        tool_button.setIcon(button_icon)
        tool_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        tool_button.clicked.connect(slot)
        tool_button.setToolTip(text)

        toolbar.addWidget(tool_button)

    def dummy_action(self, source_info="Bilinmeyen Kaynak"):
        QMessageBox.information(self, lang_manager.get_text("message_info_title"), lang_manager.get_text("message_info_text", source_info=source_info))

    # YENİ EKLENEN FONKSİYON: Sıkıştırma oranını hesaplar
    def calculate_compression_ratio(self, original_size, compressed_size):
        """
        Orijinal ve sıkıştırılmış boyutları kullanarak sıkıştırma oranını hesaplar.
        """
        if original_size == 0:
            return "N/A" # Orijinal boyut sıfır ise oran tanımsız
        
        # Sıkıştırma oranı formülü: (1 - (Sıkıştırılmış Boyut / Orijinal Boyut)) * 100
        # Eğer sıkıştırılmış boyut orijinal boyuttan büyükse (nadiren olabilir veya sıkıştırma yoksa)
        # Oranı buna göre hesaplarız. Normal dosyalar için sıkıştırılmış boyut = orijinal boyut olacağından %0 döner.
        try:
            ratio = (1 - (compressed_size / original_size)) * 100
            return f"{ratio:.2f}%"
        except ZeroDivisionError:
            return "N/A" # Bölme hatası durumunda
        except Exception:
            return "Hesaplama Hatası"


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

                self.file_list_table.setItem(row, 0, QTableWidgetItem(item_name))

                if os.path.isdir(item_path):
                    self.file_list_table.setItem(row, 1, QTableWidgetItem("")) # Original Size
                    self.file_list_table.setItem(row, 2, QTableWidgetItem("")) # Compressed Size
                    self.file_list_table.setItem(row, 3, QTableWidgetItem(lang_manager.get_text("table_header_type_folder")))
                    self.file_list_table.setItem(row, 4, QTableWidgetItem(self.get_modified_date(item_path)))
                    self.file_list_table.setItem(row, 5, QTableWidgetItem("N/A")) # Klasörler için sıkıştırma oranı uygulanamaz
                else:
                    original_size = os.path.getsize(item_path)
                    compressed_size = original_size # Normal bir dosya için sıkıştırılmış boyut, orijinal boyuta eşittir.
                                                    # Eğer bu bir arşiv dosyası olsaydı ve içeriğini gösterseydik,
                                                    # o zaman gerçek sıkıştırılmış boyutunu kullanırdık.
                    
                    self.file_list_table.setItem(row, 1, QTableWidgetItem(self.format_size(original_size)))
                    self.file_list_table.setItem(row, 2, QTableWidgetItem(self.format_size(compressed_size)))
                    self.file_list_table.setItem(row, 3, QTableWidgetItem(self.get_file_type(item_name)))
                    self.file_list_table.setItem(row, 4, QTableWidgetItem(self.get_modified_date(item_path)))
                    
                    # Sıkıştırma oranını hesapla ve tabloya ekle
                    compression_ratio_text = self.calculate_compression_ratio(original_size, compressed_size)
                    self.file_list_table.setItem(row, 5, QTableWidgetItem(compression_ratio_text))
                row += 1

        except PermissionError:
            QMessageBox.warning(self, lang_manager.get_text("message_info_title"), f"'{absolute_path}' dizinine erişim izniniz yok.")
        except Exception as e:
            QMessageBox.critical(self, lang_manager.get_text("message_info_title"), f"Dizin okunurken bir hata oluştu: {e}")


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
            return ext[1:].upper() + " Dosyası"
        return "Dosya"

    def open_terminal(self):
        current_path = self.address_bar.text()

        if not os.path.isdir(current_path):
            current_path = os.path.expanduser("~")
            if not os.path.isdir(current_path):
                current_path = os.path.dirname(__file__)
            print(f"Uyarı: Adres çubuğundaki yol geçersizdi. Terminal '{current_path}' dizininde açılıyor.")

        terminal_commands = [
            "gnome-terminal", "konsole", "xterm", "xfce4-terminal",
            "lxterminal", "mate-terminal", "urxvt", "alacritty", "kitty"
        ]

        terminal_opened = False
        for cmd in terminal_commands:
            try:
                subprocess.Popen([cmd], cwd=current_path)
                terminal_opened = True
                print(f"Bilgi: Terminal '{cmd}' ile '{current_path}' dizininde açıldı.")
                break
            except FileNotFoundError:
                print(f"Uyarı: Terminal komutu '{cmd}' bulunamadı.")
            except Exception as e:
                print(f"Hata: Terminal '{cmd}' '{current_path}' dizininde açılırken bir sorun oluştu: {e}")

        if not terminal_opened:
            QMessageBox.warning(self,
                                lang_manager.get_text("message_terminal_title"),
                                lang_manager.get_text("message_terminal_failure_text"))

    def on_item_double_clicked(self, index):
        item_name = self.file_list_table.item(index.row(), 0).text()
        current_dir = self.address_bar.text()
        new_path = os.path.join(current_dir, item_name)

        if os.path.isdir(new_path):
            self.set_current_path(new_path, add_to_history=True)
        else:
            QMessageBox.information(self,
                                    lang_manager.get_text("message_info_title"),
                                    f"'{item_name}' dosyasına çift tıkladınız. Gerçek uygulamada açılacaktır.")

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def open_compression_dialog(self):
        selected_items = self.file_list_table.selectedItems()
        selected_paths_for_dialog = []
        if selected_items:
            current_dir = self.address_bar.text()
            selected_rows = set()
            for item in selected_items:
                selected_rows.add(item.row())

            for row in selected_rows:
                item_name = self.file_list_table.item(row, 0).text()
                selected_paths_for_dialog.append(os.path.join(current_dir, item_name))

        dialog = CompressionDialog(self, current_path=self.address_bar.text())

        if selected_paths_for_dialog:
            dialog.selected_sources = selected_paths_for_dialog
            display_text = ", ".join([os.path.basename(p) for p in dialog.selected_sources])
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            dialog.source_path_display.setText(display_text)

        # BURASI GÜNCELLENDİ: exec() bir değer döndürür (Accepted veya Rejected)
        if dialog.exec() in [QDialog.DialogCode.Accepted, QDialog.DialogCode.Rejected]: # Sıkıştırma diyalogu başarılı ise
            # Mevcut dizini yeniden yükleyerek listeyi güncelle
            self.set_current_path(self.address_bar.text(), add_to_history=False)
            print("Bilgi: Sıkıştırma işlemi tamamlandı, dosya listesi güncellendi.")
        else: # Diyalog iptal edildi veya başarısız olduysa
            print("Bilgi: Sıkıştırma işlemi iptal edildi veya başarısız oldu.")


    def update_navigation_buttons(self):
        self.back_button.setEnabled(self.history_index > 0)
        self.forward_button.setEnabled(self.history_index < len(self.history) - 1)

        current_path = self.address_bar.text()
        parent_path = os.path.dirname(current_path)
        self.up_button.setEnabled(parent_path != current_path)

    def back_button_clicked(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.set_current_path(self.history[self.history_index], add_to_history=False)

    def forward_button_clicked(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.set_current_path(self.history[self.history_index], add_to_history=False)

    def up_button_clicked(self):
        current_path = self.address_bar.text()
        parent_path = os.path.dirname(current_path)
        if parent_path != current_path and os.path.isdir(parent_path):
            self.set_current_path(parent_path, add_to_history=True)



    def extract_selected_archive(self):
        selected_items = self.file_list_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, lang_manager.get_text("extraction_error_title"),
                                 lang_manager.get_text("no_archive_selected"))
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

        try:
            if archive_path.endswith(".zip"):
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(extract_to)
            elif archive_path.endswith((".tar.gz", ".tar.bz2", ".tar.xz", ".tar")):
                with tarfile.open(archive_path, 'r:*') as tf:
                    tf.extractall(extract_to)
            else:
                QMessageBox.warning(self, lang_manager.get_text("extraction_error_title"),
                                    lang_manager.get_text("unknown_format", format=os.path.splitext(archive_path)[1]))
                return

            QMessageBox.information(self, lang_manager.get_text("extraction_success_title"),
                                     lang_manager.get_text("extraction_success_text",
                                                           archive_name=os.path.basename(archive_path),
                                                           destination_path=extract_to))
        except Exception as e:
            QMessageBox.critical(self, lang_manager.get_text("extraction_error_title"),
                                 lang_manager.get_text("extraction_error_text",
                                                       archive_name=os.path.basename(archive_path),
                                                       error_message=str(e)))

    def on_address_bar_return_pressed(self):
        new_path = self.address_bar.text()
        self.set_current_path(new_path, add_to_history=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LinTARDummyApp()
    window.show()
    sys.exit(app.exec())

