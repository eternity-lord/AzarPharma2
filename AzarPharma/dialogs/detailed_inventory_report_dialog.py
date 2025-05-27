# dialogs/detailed_inventory_report_dialog.py

import sqlite3
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta # این ایمپورت datetime باید وجود داشته باشد
from persiantools.jdatetime import JalaliDate # <--- این خط را اضافه کنید
import traceback #

# به مسیر دهی DB_PATH توجه کنید.
try:
    from config import DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')
    # print(f"Warning: Using default DB_PATH in DetailedInventoryReportDialog: {DB_PATH}")

# تابع اتصال به دیتابیس
def get_db_connection_local():
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row # دسترسی به ستون‌ها با نام
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

class DetailedInventoryReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("گزارش کامل موجودی انبار (به تفکیک بچ)")
        self.setMinimumSize(950, 600) # اندازه بزرگتر برای نمایش ستون‌های بیشتر

        self._setup_ui()
        self._load_report()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        compact_font = QFont(); compact_font.setPointSize(8)

        # --- بخش فیلترها (اختیاری، برای آینده می‌توان اضافه کرد) ---
        filter_layout = QHBoxLayout()
        self.search_drug_edit = QLineEdit()
        self.search_drug_edit.setFont(compact_font)
        self.search_drug_edit.setPlaceholderText("جستجوی نام دارو یا کد ژنریک...")
        self.search_drug_edit.textChanged.connect(self._load_report) # جستجوی آنی
        
        lbl_search = QLabel("جستجو:")
        lbl_search.setFont(compact_font)
        filter_layout.addWidget(lbl_search)
        filter_layout.addWidget(self.search_drug_edit, 1)
        
        self.refresh_button = QPushButton("به‌روزرسانی گزارش")
        self.refresh_button.setFont(compact_font)
        self.refresh_button.clicked.connect(self._load_report)
        filter_layout.addWidget(self.refresh_button)
        main_layout.addLayout(filter_layout)

        # --- جدول نمایش موجودی ---
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(9) 
        self.inventory_table.setHorizontalHeaderLabels([
            "کد ژنریک", "نام دارو (snapshot)", "شماره بچ", "تاریخ انقضا (شمسی)", 
            "تعداد بسته", "تعداد واحد", "فی خرید بسته", "تامین کننده", "تاریخ خرید"
        ])
        self.inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.setStyleSheet(
            "QTableWidget { alternate-background-color: #f8f8f8; font-size: 8pt; }"
            "QHeaderView::section { background-color: #e8e8e8; padding: 3px; font-size: 8pt; }"
        )
        self.inventory_table.horizontalHeader().setFont(compact_font) # فونت برای هدر

        # فعال کردن قابلیت مرتب‌سازی با کلیک روی هدر ستون‌ها
        self.inventory_table.setSortingEnabled(True)


        header = self.inventory_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive) # Generic Code
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)     # Drug Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Batch
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Expiry
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # Package Count
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive) # Unit Count
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive) # Purchase Price
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)     # Supplier
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive) # Purchase Date
        
        self.inventory_table.setColumnWidth(0, 90)
        self.inventory_table.setColumnWidth(2, 100)
        self.inventory_table.setColumnWidth(3, 90)
        self.inventory_table.setColumnWidth(4, 70)
        self.inventory_table.setColumnWidth(5, 70)
        self.inventory_table.setColumnWidth(6, 90)
        self.inventory_table.setColumnWidth(8, 90)


        main_layout.addWidget(self.inventory_table, 1)

        # --- دکمه بستن ---
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch(1)
        self.close_button = QPushButton("بستن")
        self.close_button.setFont(compact_font)
        self.close_button.clicked.connect(self.accept)
        close_button_layout.addWidget(self.close_button)
        main_layout.addLayout(close_button_layout)

    def _format_date_for_display(self, date_str_gregorian):
        """تاریخ میلادی YYYY/MM/DD را به شمسی خوانا تبدیل می‌کند."""
        if not date_str_gregorian:
            return ""
        try:
            dt_obj = datetime.strptime(date_str_gregorian, "%Y/%m/%d")
            jalali_date = JalaliDate(dt_obj.year, dt_obj.month, dt_obj.day)
            return jalali_date.strftime("%Y/%m/%d") # فرمت شمسی
        except ValueError:
            return date_str_gregorian # اگر فرمت ناشناخته بود، خود رشته را برگردان

    def _load_report(self):
        self.inventory_table.setSortingEnabled(False) # غیرفعال کردن موقت مرتب‌سازی هنگام پر کردن جدول
        self.inventory_table.setRowCount(0)
        search_term = self.search_drug_edit.text().strip()
        conn = None
        try:
            conn = get_db_connection_local()
            cursor = conn.cursor()
            
            # کوئری برای خواندن تمام اقلام موجود در انبار (تعداد واحد یا بسته > 0)
            # به همراه نام تامین کننده و تاریخ خرید از فاکتور مربوطه
            query = """
                SELECT 
                    cpi.generic_code,
                    cpi.drug_name_snapshot, 
                    cpi.batch_number, 
                    cpi.expiry_date_gregorian, -- برای مرتب‌سازی استفاده می‌شود، نمایش شمسی خواهد بود
                    cpi.expiry_date_jalali,    -- برای نمایش مستقیم
                    cpi.package_count, 
                    cpi.unit_count,
                    cpi.purchase_price_per_package,
                    cp.supplier_name,
                    cp.invoice_date -- یا cp.registration_date اگر تاریخ ثبت سند مدنظر است
                FROM company_purchase_items cpi
                LEFT JOIN company_purchases cp ON cpi.purchase_document_id = cp.id
                WHERE (cpi.package_count > 0 OR cpi.unit_count > 0)
            """
            params = []
            if search_term:
                query += """ AND (cpi.drug_name_snapshot LIKE ? OR cpi.generic_code LIKE ?) """
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            
            # مرتب‌سازی پیش‌فرض بر اساس نام دارو و سپس تاریخ انقضا
            query += " ORDER BY cpi.drug_name_snapshot ASC, cpi.expiry_date_gregorian ASC"
            
            cursor.execute(query, params)
            items = cursor.fetchall()

            if not items and not search_term: # فقط اگر جستجو خالی بود و نتیجه‌ای نبود پیام بده
                QMessageBox.information(self, "گزارش", "موردی در انبار (با موجودی مثبت) یافت نشد.")
                self.inventory_table.setSortingEnabled(True)
                return

            for row_num, item_row in enumerate(items):
                self.inventory_table.insertRow(row_num)
                
                # دسترسی به ستون‌ها با نام (چون conn.row_factory = sqlite3.Row تنظیم شده)
                self.inventory_table.setItem(row_num, 0, QTableWidgetItem(item_row["generic_code"] or ""))
                self.inventory_table.setItem(row_num, 1, QTableWidgetItem(item_row["drug_name_snapshot"] or ""))
                self.inventory_table.setItem(row_num, 2, QTableWidgetItem(item_row["batch_number"] or ""))
                
                # نمایش تاریخ انقضای شمسی (که از قبل در دیتابیس داریم)
                self.inventory_table.setItem(row_num, 3, QTableWidgetItem(item_row["expiry_date_jalali"] or ""))
                
                self.inventory_table.setItem(row_num, 4, QTableWidgetItem(str(item_row["package_count"] or 0)))
                self.inventory_table.setItem(row_num, 5, QTableWidgetItem(str(item_row["unit_count"] or 0)))
                
                purchase_price = item_row["purchase_price_per_package"] or 0
                self.inventory_table.setItem(row_num, 6, QTableWidgetItem(f"{purchase_price:,.0f}"))

                self.inventory_table.setItem(row_num, 7, QTableWidgetItem(item_row["supplier_name"] or "نامشخص"))
                
                # نمایش تاریخ خرید شمسی (با تبدیل از میلادی)
                invoice_date_display = self._format_date_for_display(item_row["invoice_date"])
                self.inventory_table.setItem(row_num, 8, QTableWidgetItem(invoice_date_display))
        
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در تهیه گزارش موجودی انبار: {e}")
        except Exception as ex:
            QMessageBox.critical(self, "خطا", f"یک خطای پیش بینی نشده رخ داد: {str(ex)}\n{traceback.format_exc()}")
        finally:
            if conn:
                conn.close()
            self.inventory_table.setSortingEnabled(True) # فعال کردن مجدد مرتب‌سازی