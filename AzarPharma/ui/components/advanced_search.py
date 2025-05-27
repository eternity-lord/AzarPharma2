# ui/components/advanced_search.py (نسخه کامل با drug_selected signal)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                           QPushButton, QFrame, QLabel, QListWidget, QListWidgetItem,
                           QCompleter, QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QStringListModel
from PyQt6.QtGui import QFont, QIcon
import sqlite3
from config import DB_PATH

class AdvancedSearchWidget(QFrame):
    """ویجت جستجوی پیشرفته با پیشنهادات خودکار"""
    
    search_performed = pyqtSignal(str, str)  # search_term, search_type
    drug_selected = pyqtSignal(dict)  # اضافه شد
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AdvancedSearchWidget")
        self.setup_ui()
        self.setup_style()
        self.load_suggestions()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # عنوان
        title_label = QLabel("🔍 جستجوی پیشرفته")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # نوار جستجو
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("نام دارو، کد دارو، یا شرکت سازنده...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self.on_text_changed)
        self.search_input.returnPressed.connect(self.perform_search)
        
        search_btn = QPushButton("🔍 جستجو")
        search_btn.setFixedHeight(40)
        search_btn.clicked.connect(self.perform_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        # لیست پیشنهادات
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(200)
        self.suggestions_list.itemClicked.connect(self.select_suggestion)
        self.suggestions_list.hide()
        layout.addWidget(self.suggestions_list)
        
        layout.addStretch()
    
    def setup_style(self):
        self.setStyleSheet("""
            #AdvancedSearchWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95),
                    stop:1 rgba(248, 249, 250, 0.95));
                border: 2px solid #e9ecef;
                border-radius: 15px;
                margin: 10px;
            }
            
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
                background: white;
            }
            
            QLineEdit:focus {
                border-color: #3498db;
                background: #f8f9fa;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 15px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
            
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background: white;
                font-size: 11px;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            
            QListWidget::item:hover {
                background: #e3f2fd;
            }
            
            QListWidget::item:selected {
                background: #2196f3;
                color: white;
            }
        """)
    
    def load_suggestions(self):
        """بارگذاری پیشنهادات از دیتابیس"""
        self.suggestions = []
        self.suggestions_data = {}  # برای ذخیره اطلاعات کامل داروها
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # بررسی ستونهای جدول drugs
            cursor.execute("PRAGMA table_info(drugs)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Available columns in drugs table: {columns}")
            
            # استفاده از ستونهای موجود
            if 'drug_name' in columns:
                cursor.execute("SELECT * FROM drugs WHERE drug_name IS NOT NULL LIMIT 100")
                drugs = cursor.fetchall()
                # دریافت نام ستونها
                cursor.execute("PRAGMA table_info(drugs)")
                col_names = [col[1] for col in cursor.fetchall()]
                
                for drug in drugs:
                    drug_dict = dict(zip(col_names, drug))
                    drug_name = drug_dict.get('drug_name', '')
                    if drug_name:
                        self.suggestions.append(drug_name)
                        self.suggestions_data[drug_name] = drug_dict
                        
            elif 'name' in columns:
                cursor.execute("SELECT * FROM drugs WHERE name IS NOT NULL LIMIT 100")
                drugs = cursor.fetchall()
                cursor.execute("PRAGMA table_info(drugs)")
                col_names = [col[1] for col in cursor.fetchall()]
                
                for drug in drugs:
                    drug_dict = dict(zip(col_names, drug))
                    drug_name = drug_dict.get('name', '')
                    if drug_name:
                        self.suggestions.append(drug_name)
                        self.suggestions_data[drug_name] = drug_dict
            
            conn.close()
            
            # حذف تکراری‌ها
            self.suggestions = list(set(self.suggestions))
            print(f"Loaded {len(self.suggestions)} suggestions")
            
        except Exception as e:
            print(f"Error loading suggestions: {e}")
            self.suggestions = ["نمونه دارو 1", "نمونه دارو 2", "شرکت نمونه"]
            self.suggestions_data = {}
    
    def on_text_changed(self, text):
        """نمایش پیشنهادات هنگام تایپ"""
        if len(text) < 2:
            self.suggestions_list.hide()
            return
        
        # فیلتر پیشنهادات
        filtered = [s for s in self.suggestions if text.lower() in s.lower()][:10]
        
        if filtered:
            self.suggestions_list.clear()
            for suggestion in filtered:
                item = QListWidgetItem(suggestion)
                self.suggestions_list.addItem(item)
            self.suggestions_list.show()
        else:
            self.suggestions_list.hide()
    
    def select_suggestion(self, item):
        """انتخاب پیشنهاد"""
        drug_name = item.text()
        self.search_input.setText(drug_name)
        self.suggestions_list.hide()
        
        # ارسال سیگنال drug_selected
        if drug_name in self.suggestions_data:
            self.drug_selected.emit(self.suggestions_data[drug_name])
        
        self.perform_search()
    
    def perform_search(self):
        """انجام جستجو"""
        search_term = self.search_input.text().strip()
        if search_term:
            self.search_performed.emit(search_term, "general")
            self.suggestions_list.hide()

class CompactSearchWidget(QFrame):
    """نوار جستجوی فشرده برای top bar"""
    
    search_performed = pyqtSignal(str)
    drug_selected = pyqtSignal(dict)  # 🔥 سیگنال مورد نیاز اضافه شد
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CompactSearchWidget")
        self.setFixedHeight(35)
        self.suggestions_data = {}  # برای ذخیره اطلاعات داروها
        self.setup_ui()
        self.setup_style()
        self.load_drug_data()  # بارگذاری داده‌های داروها
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو...")
        self.search_input.setFixedHeight(30)
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_input.textChanged.connect(self.on_text_changed)
        
        search_btn = QPushButton("🔍")
        search_btn.setFixedSize(30, 30)
        search_btn.clicked.connect(self.perform_search)
        
        layout.addWidget(self.search_input)
        layout.addWidget(search_btn)
        
        # لیست پیشنهادات (مخفی)
        self.suggestions_list = QListWidget(self)
        self.suggestions_list.setMaximumHeight(150)
        self.suggestions_list.itemClicked.connect(self.select_suggestion)
        self.suggestions_list.hide()
        self.suggestions_list.setParent(self.parent() if self.parent() else self)
        
    def setup_style(self):
        self.setStyleSheet("""
            #CompactSearchWidget {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid #ddd;
                border-radius: 6px;
            }
            
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                background: white;
            }
            
            QLineEdit:focus {
                border-color: #3498db;
            }
            
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background: #2980b9;
            }
            
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background: white;
                font-size: 10px;
                position: absolute;
                z-index: 1000;
            }
            
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            
            QListWidget::item:hover {
                background: #e3f2fd;
            }
        """)
    
    def load_drug_data(self):
        """بارگذاری داده‌های داروها"""
        self.drugs_list = []
        self.suggestions_data = {}
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # بررسی ستونهای جدول
            cursor.execute("PRAGMA table_info(drugs)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # انتخاب ستون نام مناسب
            name_column = 'drug_name' if 'drug_name' in columns else 'name'
            
            if name_column in columns:
                cursor.execute(f"SELECT * FROM drugs WHERE {name_column} IS NOT NULL LIMIT 200")
                drugs = cursor.fetchall()
                
                # دریافت نام ستونها
                cursor.execute("PRAGMA table_info(drugs)")
                col_names = [col[1] for col in cursor.fetchall()]
                
                for drug in drugs:
                    drug_dict = dict(zip(col_names, drug))
                    drug_name = drug_dict.get(name_column, '')
                    if drug_name:
                        self.drugs_list.append(drug_name)
                        self.suggestions_data[drug_name] = drug_dict
            
            conn.close()
            print(f"CompactSearch: Loaded {len(self.drugs_list)} drugs")
            
        except Exception as e:
            print(f"Error loading drug data for compact search: {e}")
    
    def on_text_changed(self, text):
        """نمایش پیشنهادات هنگام تایپ"""
        if len(text) < 2:
            self.suggestions_list.hide()
            return
        
        # فیلتر پیشنهادات
        filtered = [drug for drug in self.drugs_list if text.lower() in drug.lower()][:8]
        
        if filtered:
            self.suggestions_list.clear()
            for drug in filtered:
                item = QListWidgetItem(drug)
                self.suggestions_list.addItem(item)
            
            # موقعیت‌یابی لیست
            search_pos = self.search_input.mapToGlobal(self.search_input.rect().bottomLeft())
            self.suggestions_list.move(search_pos)
            self.suggestions_list.resize(self.search_input.width(), 150)
            self.suggestions_list.show()
            self.suggestions_list.raise_()
        else:
            self.suggestions_list.hide()
    
    def select_suggestion(self, item):
        """انتخاب پیشنهاد"""
        drug_name = item.text()
        self.search_input.setText(drug_name)
        self.suggestions_list.hide()
        
        # ارسال سیگنال drug_selected 🔥
        if drug_name in self.suggestions_data:
            self.drug_selected.emit(self.suggestions_data[drug_name])
        
        self.perform_search()
    
    def perform_search(self):
        """انجام جستجو"""
        search_term = self.search_input.text().strip()
        if search_term:
            self.search_performed.emit(search_term)
            self.suggestions_list.hide()
    
    def hideEvent(self, event):
        """مخفی کردن لیست پیشنهادات هنگام مخفی شدن ویجت"""
        self.suggestions_list.hide()
        super().hideEvent(event)
