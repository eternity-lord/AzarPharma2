# dialogs/low_stock_report_dialog.py

import sqlite3
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox ,QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont # برای تنظیم فونت

# به مسیر دهی DB_PATH توجه کنید.
try:
    from config import DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')
    # print(f"Warning: Using default DB_PATH in LowStockReportDialog: {DB_PATH}")

# تابع اتصال به دیتابیس
def get_db_connection_local():
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

class LowStockReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("گزارش داروهای با موجودی کم (نیاز به سفارش)")
        self.setMinimumSize(750, 450)

        self._setup_ui()
        self._load_report() # بارگذاری اولیه گزارش

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        compact_font = QFont(); compact_font.setPointSize(8)

        # --- بخش دکمه به‌روزرسانی ---
        top_layout = QHBoxLayout()
        top_layout.addStretch(1)
        self.refresh_button = QPushButton("به‌روزرسانی گزارش")
        self.refresh_button.setFont(compact_font)
        self.refresh_button.clicked.connect(self._load_report)
        top_layout.addWidget(self.refresh_button)
        main_layout.addLayout(top_layout)

        # --- جدول نمایش داروها ---
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(5) 
        self.report_table.setHorizontalHeaderLabels([
            "نام دارو (ژنریک)", "کد ژنریک", "موجودی فعلی", 
            "سطح هشدار موجودی", "میزان کمبود/نیاز"
        ])
        self.report_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.report_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setStyleSheet(
            "QTableWidget { alternate-background-color: #f8f8f8; font-size: 8pt; }"
            "QHeaderView::section { background-color: #e8e8e8; padding: 3px; font-size: 8pt; }"
        ) # فونت برای جدول و هدر هم کوچک شد
        # self.report_table.setFont(compact_font) # این هم کار می‌کند
        # self.report_table.horizontalHeader().setFont(compact_font)

        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)     # Drug Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # Generic Code
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Current Stock
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Min Stock Level
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # Difference
        
        self.report_table.setColumnWidth(1, 100) # کد ژنریک
        self.report_table.setColumnWidth(2, 90)  # موجودی فعلی
        self.report_table.setColumnWidth(3, 110) # سطح هشدار
        self.report_table.setColumnWidth(4, 100) # کمبود

        main_layout.addWidget(self.report_table, 1)

        # --- دکمه بستن ---
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch(1)
        self.close_button = QPushButton("بستن")
        self.close_button.setFont(compact_font)
        self.close_button.clicked.connect(self.accept)
        close_button_layout.addWidget(self.close_button)
        main_layout.addLayout(close_button_layout)

    def _load_report(self):
        self.report_table.setRowCount(0)
        conn = None
        try:
            conn = get_db_connection_local()
            cursor = conn.cursor()
            
            # انتخاب داروهایی که موجودی آنها کمتر یا مساوی سطح هشدار است
            # و سطح هشدار آنها بزرگتر از صفر است (برای جلوگیری از نمایش همه داروها اگر سطح هشدار 0 باشد)
            query = """
                SELECT 
                    generic_name, 
                    en_brand_name,
                    generic_code, 
                    stock, 
                    min_stock_alert_level
                FROM drugs
                WHERE stock <= min_stock_alert_level AND min_stock_alert_level > 0
                ORDER BY (min_stock_alert_level - stock) DESC, generic_name ASC 
                -- مرتب‌سازی بر اساس بیشترین کمبود، سپس بر اساس نام دارو
            """
            
            cursor.execute(query)
            items = cursor.fetchall()

            if not items:
                QMessageBox.information(self, "گزارش", "هیچ دارویی با موجودی کمتر از سطح هشدار یافت نشد.")
                return

            for row_num, item_data in enumerate(items):
                self.report_table.insertRow(row_num)
                
                drug_display_name = f"{item_data[0]} ({item_data[1]})" # generic_name (en_brand_name)
                generic_code = item_data[2]
                current_stock = item_data[3]
                min_level = item_data[4]
                difference = min_level - current_stock # کمبود (اگر مثبت باشد یعنی کمبود دارد)

                self.report_table.setItem(row_num, 0, QTableWidgetItem(drug_display_name))
                self.report_table.setItem(row_num, 1, QTableWidgetItem(generic_code))
                self.report_table.setItem(row_num, 2, QTableWidgetItem(str(current_stock)))
                self.report_table.setItem(row_num, 3, QTableWidgetItem(str(min_level)))
                
                diff_item = QTableWidgetItem(str(difference if difference > 0 else 0)) # نمایش 0 اگر کمبود ندارد
                if difference > 0:
                    # می‌توانید رنگ متن را برای کمبودها تغییر دهید (مثلا قرمز)
                    # diff_item.setForeground(Qt.GlobalColor.red) # نیاز به ایمپورت Qt.GlobalColor
                    pass 
                self.report_table.setItem(row_num, 4, diff_item)
        
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در تهیه گزارش داروهای با موجودی کم: {e}")
        except Exception as ex:
            QMessageBox.critical(self, "خطا", f"یک خطای پیش بینی نشده رخ داد: {str(ex)}")
        finally:
            if conn:
                conn.close()