import sys
import os
import configparser
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QToolButton,
    QLineEdit, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QSizePolicy, QMenu, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QPushButton, QTabWidget,
    QGroupBox, QFormLayout, QComboBox, QCheckBox, QSpinBox
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QSize

# Resimlerin bulunduğu dizin (LinTAR.py ile aynı dizin)
IMAGE_DIR = os.path.dirname(__file__)
# Dil dosyası yolu
LANG_FILE = os.path.join(IMAGE_DIR, "language.ini")

# Dil ayarlarını yüklemek için global bir sözlük veya sınıf
class LanguageManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.translations = {}
        self.current_language = "en" # Varsayılan dil (eğer language.ini okunamazsa)

        # language.ini okunamadığında veya seçilen dil bulunamadığında kullanılacak sabit İngilizce metinler (Fallback)
        self.default_english_translations = {
            "app_title": "LinTAR - Linux Archiver (Demo)",
            "file_menu": "File", "edit_menu": "Edit", "view_menu": "View", "help_menu": "Help",
            "new_archive": "New Archive...", "open_archive": "Open Archive...",
            "save_files": "Save Files", "save_as_files": "Save As...", "exit_app": "Exit",
            "select": "Select...", "select_all": "Select All", "rename": "Rename...",
            "large_icons": "Large Icons", "small_icons": "Small Icons", "list_view": "List",
            "details_view": "Details", "toolbar": "Toolbar", "statusbar": "Statusbar",
            "help_topics": "Help Topics", "license_info": "License...", "about_LinTAR": "About LinTAR...",
            "compress_button": "Compress", "extract_button": "Extract", "test_button": "Test",
            "repair_button": "Repair", "search_button": "Search", "delete_button": "Delete",
            "info_button": "Info", "terminal_button": "Terminal", "settings_button": "Settings",
            "back_button": "Back", "forward_button": "Forward", "up_button": "Up One Level",
            "address_label": "Address:", "address_placeholder": "Current directory path will appear here...",
            "table_header_name": "Name", "table_header_original_size": "Original Size",
            "table_header_compressed_size": "Compressed Size", "table_header_type": "Type",
            "table_header_modified_date": "Modified Date", "table_header_compression_ratio": "Compression Ratio",
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
            "settings_language_changed_restart_prompt": "Language setting saved. Please restart the application for changes to take effect."
        }

        self.load_languages()

    def load_languages(self):
        # Başlangıçta her zaman İngilizce fallback kullan, sonra dosyadan yüklemeyi dene
        self.translations = self.default_english_translations 

        print(f"Bilgi: Dil dosyası yolu: {LANG_FILE}") # Dosya yolunu konsola yazdır
        if os.path.exists(LANG_FILE):
            try:
                self.config.read(LANG_FILE, encoding='utf-8')
                print(f"Bilgi: '{LANG_FILE}' dosyası bulundu ve okundu.")
                
                # Ayarlar bölümünden varsayılan dili almaya çalış
                if 'settings' in self.config and 'default_language' in self.config['settings']:
                    requested_lang = self.config['settings']['default_language']
                    print(f"Bilgi: language.ini dosyasında istenen dil: '{requested_lang}'")
                    
                    if requested_lang in self.config and requested_lang != 'settings': # İstenen dil bölümünün varlığını kontrol et
                        self.current_language = requested_lang
                        self.translations = self.config[self.current_language]
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
        # Önce mevcut dildeki çeviriyi dene, yoksa sabit İngilizce çeviriyi dene,
        # hala yoksa MISSING_TEXT göster.
        text = self.translations.get(key, self.default_english_translations.get(key, f"MISSING_TEXT_{key}"))
        return text.format(**kwargs)

    def get_available_languages(self):
        """language.ini dosyasındaki kullanılabilir dilleri döndürür."""
        languages = []
        for section in self.config.sections():
            if section != 'settings': # 'settings' bölümünü dil olarak saymıyoruz
                languages.append(section)
        return sorted(languages) # Alfabetik sıraya göre sırala

    def set_language(self, lang_code):
        """Programın dilini değiştirir ve çevirileri yeniden yükler."""
        if lang_code in self.config and lang_code != 'settings':
            self.current_language = lang_code
            self.translations = self.config[self.current_language]
            print(f"Bilgi: Dil '{self.current_language}' olarak ayarlandı.")
            # Seçilen dili settings bölümüne kaydet (kalıcı olması için)
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


# LanguageManager örneğini oluştur
lang_manager = LanguageManager()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(lang_manager.get_text("settings_title"))
        self.setMinimumSize(400, 300)

        # Mevcut dil ayarını almak için ekledik
        self.initial_language = lang_manager.current_language
        self.selected_language = self.initial_language # Başlangıçta seçilen dil

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        tab_widget = QTabWidget(self)

        # 1. Genel Sekmesi
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        # Dil ComboBox'ı (Şimdi seçeneklerle dolduruyoruz!)
        self.language_combo = QComboBox()
        available_langs = lang_manager.get_available_languages()
        
        # Dil kodlarını daha anlaşılır isimlerle eşleştirme (isteğe bağlı, ama kullanıcı dostu)
        lang_display_names = {
            "tr": "Türkçe",
            "en": "English",
            # Gelecekte ekleyeceğiniz diller için buraya devam edebilirsiniz:
            # "de": "Deutsch",
            # "fr": "Français",
        }

        # ComboBox'a dilleri ekle
        for lang_code in available_langs:
            display_name = lang_display_names.get(lang_code, lang_code.upper()) # Eğer display_name yoksa kodun kendisini göster
            self.language_combo.addItem(display_name, lang_code) # İtem text, item data
        
        # Şu anki dili seçili hale getir
        current_lang_index = self.language_combo.findData(self.initial_language)
        if current_lang_index != -1:
            self.language_combo.setCurrentIndex(current_lang_index)
        
        # Dil değiştirildiğinde tetiklenecek fonksiyonu bağla
        self.language_combo.currentIndexChanged.connect(self.on_language_selected)

        general_layout.addRow(QLabel(lang_manager.get_text("settings_lang_label")), self.language_combo)
        general_layout.addRow(QLabel(lang_manager.get_text("settings_extract_path_label")), QLineEdit("~/.config/LinTAR/extracted")) # Dummy QLineEdit
        general_layout.addRow(QLabel(lang_manager.get_text("settings_theme_label")), QComboBox()) # Dummy ComboBox
        tab_widget.addTab(general_tab, lang_manager.get_text("settings_tab_general"))

        # 2. Sıkıştırma Sekmesi
        compression_tab = QWidget()
        comp_layout = QFormLayout(compression_tab)
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_default_format_label")), QComboBox()) # Dummy ComboBox
        
        # Sıkıştırma Seviyesi (QComboBox olarak güncellendi)
        compression_level_combo = QComboBox()
        compression_level_combo.addItems([
            lang_manager.get_text("compression_level_store"),
            lang_manager.get_text("compression_level_fast"),
            lang_manager.get_text("compression_level_normal"),
            lang_manager.get_text("compression_level_good"),
            lang_manager.get_text("compression_level_best")
        ])
        compression_level_combo.setCurrentText(lang_manager.get_text("compression_level_normal")) # Varsayılan olarak "Normal" seçili gelsin
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_compression_level_label")), compression_level_combo)
        
        comp_layout.addRow(QLabel(lang_manager.get_text("settings_recovery_record_label")), QCheckBox(lang_manager.get_text("settings_recovery_record_label_checkbox_text"))) # Dummy CheckBox

        # Yeni: İşlemci Çekirdeği Sayısı (QSpinBox)
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

        # Butonlar (Tamam, İptal, Uygula) - Bağlantıları güncelle
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_ok = QPushButton(lang_manager.get_text("button_ok"))
        btn_ok.clicked.connect(self.accept_settings) # accept yerine accept_settings çağır
        button_layout.addWidget(btn_ok)

        btn_cancel = QPushButton(lang_manager.get_text("button_cancel"))
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_apply = QPushButton(lang_manager.get_text("button_apply"))
        btn_apply.clicked.connect(self.apply_settings) # apply yerine apply_settings çağır
        button_layout.addWidget(btn_apply)

        main_layout.addLayout(button_layout)

    # Yeni metod: ComboBox'tan dil seçildiğinde
    def on_language_selected(self, index):
        self.selected_language = self.language_combo.itemData(index)
        print(f"Bilgi: Ayarlar diyalogunda seçilen dil: {self.selected_language}")

    # Yeni metod: Ayarları uygulama (Uygula butonu için)
    def apply_settings(self):
        # Dil değiştiyse kaydet
        if self.selected_language != self.initial_language:
            lang_manager.set_language(self.selected_language)
            QMessageBox.information(self, 
                                    lang_manager.get_text("message_info_title"), 
                                    lang_manager.get_text("settings_language_changed_restart_prompt"))
            self.initial_language = self.selected_language # Yeni dili başlangıç dili olarak ayarla
        else:
            QMessageBox.information(self, 
                                    lang_manager.get_text("message_settings_apply_title"), 
                                    lang_manager.get_text("message_settings_apply_text")) # Eski dummy mesajı kullan

    # Yeni metod: Ayarları kabul etme (Tamam butonu için)
    def accept_settings(self):
        self.apply_settings() # Önce ayarları uygula
        self.accept() # Sonra diyalogu kapat


class LinTARDummyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(lang_manager.get_text("app_title"))
        self.setGeometry(100, 100, 850, 600) 
        
        icon_path = os.path.join(IMAGE_DIR, "ZeusArchiver.png") 
        self.setWindowIcon(QIcon(icon_path)) 

        self.init_ui()

    def init_ui(self):
        # --- 0. Menü Çubuğu ---
        menubar = self.menuBar()

        # Dosya Menüsü
        file_menu = menubar.addMenu(lang_manager.get_text("file_menu"))
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("new_archive"), "new_archive"))
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("open_archive"), "open_archive"))
        file_menu.addSeparator()
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("save_files"), "save_files"))
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("save_as_files"), "save_as_files"))
        file_menu.addSeparator()
        file_menu.addAction(self.create_dummy_action(lang_manager.get_text("exit_app"), "exit_app"))

        # Düzenle Menüsü
        edit_menu = menubar.addMenu(lang_manager.get_text("edit_menu"))
        edit_menu.addAction(self.create_dummy_action(lang_manager.get_text("select"), "select"))
        edit_menu.addAction(self.create_dummy_action(lang_manager.get_text("select_all"), "select_all"))
        edit_menu.addSeparator()
        edit_menu.addAction(self.create_dummy_action(lang_manager.get_text("rename"), "rename"))

        # Görünüm Menüsü
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


        # Yardım Menüsü
        help_menu = menubar.addMenu(lang_manager.get_text("help_menu"))
        help_menu.addAction(self.create_dummy_action(lang_manager.get_text("help_topics"), "help_topics"))
        help_menu.addAction(self.create_dummy_action(lang_manager.get_text("license_info"), "license_info"))
        help_menu.addSeparator()
        help_menu.addAction(self.create_dummy_action(lang_manager.get_text("about_LinTAR"), "about_LinTAR"))


        # --- 1. Buton Satırı (Araç Çubuğu) ---
        toolbar = QToolBar(lang_manager.get_text("toolbar")) # ToolBar başlığını da çeviriyoruz
        toolbar.setIconSize(QSize(64, 64)) 
        self.addToolBar(toolbar)

        self.add_toolbar_button(toolbar, lang_manager.get_text("compress_button"), "Add.png", lambda: self.dummy_action(lang_manager.get_text("compress_button")))
        self.add_toolbar_button(toolbar, lang_manager.get_text("extract_button"), "Extract.png", lambda: self.dummy_action(lang_manager.get_text("extract_button")))
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


        # --- 2. Gezinme ve Adres Kutucuğu ---
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(10, 0, 10, 0)
        
        nav_icon_size = QSize(24, 24)

        btn_back = QToolButton(self)
        btn_back.setIcon(QIcon.fromTheme("go-previous", QIcon(os.path.join(IMAGE_DIR, "back_arrow.png") if os.path.exists(os.path.join(IMAGE_DIR, "back_arrow.png")) else "")))
        btn_back.setIconSize(nav_icon_size)
        btn_back.setToolTip(lang_manager.get_text("back_button"))
        btn_back.clicked.connect(lambda: self.dummy_action(lang_manager.get_text("back_button")))
        nav_layout.addWidget(btn_back)

        btn_forward = QToolButton(self)
        btn_forward.setIcon(QIcon.fromTheme("go-next", QIcon(os.path.join(IMAGE_DIR, "forward_arrow.png") if os.path.exists(os.path.join(IMAGE_DIR, "forward_arrow.png")) else "")))
        btn_forward.setIconSize(nav_icon_size)
        btn_forward.setToolTip(lang_manager.get_text("forward_button"))
        btn_forward.clicked.connect(lambda: self.dummy_action(lang_manager.get_text("forward_button")))
        nav_layout.addWidget(btn_forward)
        
        btn_up = QToolButton(self)
        btn_up.setIcon(QIcon.fromTheme("go-up", QIcon(os.path.join(IMAGE_DIR, "up_arrow.png") if os.path.exists(os.path.join(IMAGE_DIR, "up_arrow.png")) else "")))
        btn_up.setIconSize(nav_icon_size)
        btn_up.setToolTip(lang_manager.get_text("up_button"))
        btn_up.clicked.connect(lambda: self.dummy_action(lang_manager.get_text("up_button")))
        nav_layout.addWidget(btn_up)

        # Adres etiketi
        lbl_address = QLabel(lang_manager.get_text("address_label"))
        nav_layout.addWidget(lbl_address)

        # Adres kutucuğu
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText(lang_manager.get_text("address_placeholder"))
        self.address_bar.setReadOnly(True)
        self.address_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        nav_layout.addWidget(self.address_bar)

        # --- 3. Ana İçerik Alanı (Dosya Listesi) ---
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
        self.file_list_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.file_list_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_list_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.file_list_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        # Örnek dummy veri ekle (Bunları da language.ini'ye taşıyabiliriz ama şimdilik sabit kalsın)
        self.file_list_table.setRowCount(5)

        self.file_list_table.setItem(0, 0, QTableWidgetItem("rapor.docx"))
        self.file_list_table.setItem(0, 1, QTableWidgetItem("1250 KB"))
        self.file_list_table.setItem(0, 2, QTableWidgetItem("350 KB"))
        self.file_list_table.setItem(0, 3, QTableWidgetItem("DOCX Dosyası"))
        self.file_list_table.setItem(0, 4, QTableWidgetItem("2024-01-15 10:30"))
        self.file_list_table.setItem(0, 5, QTableWidgetItem("%72"))

        self.file_list_table.setItem(1, 0, QTableWidgetItem("Resimler/"))
        self.file_list_table.setItem(1, 1, QTableWidgetItem(""))
        self.file_list_table.setItem(1, 2, QTableWidgetItem(""))
        self.file_list_table.setItem(1, 3, QTableWidgetItem("Klasör"))
        self.file_list_table.setItem(1, 4, QTableWidgetItem("2024-07-11 15:00"))
        self.file_list_table.setItem(1, 5, QTableWidgetItem(""))
        
        self.file_list_table.setItem(2, 0, QTableWidgetItem("video.mp4"))
        self.file_list_table.setItem(2, 1, QTableWidgetItem("50 MB"))
        self.file_list_table.setItem(2, 2, QTableWidgetItem("48 MB"))
        self.file_list_table.setItem(2, 3, QTableWidgetItem("MP4 Video"))
        self.file_list_table.setItem(2, 4, QTableWidgetItem("2023-12-01 09:00"))
        self.file_list_table.setItem(2, 5, QTableWidgetItem("%4"))

        self.file_list_table.setItem(3, 0, QTableWidgetItem("script.py"))
        self.file_list_table.setItem(3, 1, QTableWidgetItem("12 KB"))
        self.file_list_table.setItem(3, 2, QTableWidgetItem("3 KB"))
        self.file_list_table.setItem(3, 3, QTableWidgetItem("Python Kodu"))
        self.file_list_table.setItem(3, 4, QTableWidgetItem("2024-06-20 11:45"))
        self.file_list_table.setItem(3, 5, QTableWidgetItem("%75"))

        # --- Genel Düzen ---
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.file_list_table)

        self.setCentralWidget(central_widget)

    def create_dummy_action(self, text, action_id):
        action = QAction(text, self)
        # Dummy aksiyon metnini de language.ini'den çekiyoruz
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
        # Mesaj kutusu metinlerini language.ini'den çekiyoruz
        QMessageBox.information(self, lang_manager.get_text("message_info_title"), lang_manager.get_text("message_info_text", source_info=source_info))

    def open_terminal(self):
        # Terminal mesajını language.ini'den çekiyoruz
        QMessageBox.information(self, lang_manager.get_text("message_terminal_title"), lang_manager.get_text("message_terminal_text"))

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LinTARDummyApp()
    window.show()
    sys.exit(app.exec())
