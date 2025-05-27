# dialogs/near_expiry_report_dialog.py

import sqlite3
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate
from persiantools.jdatetime import JalaliDate # برای نمایش تاریخ شمسی

# به مسیر دهی DB_PATH توجه کنید.
try:
    from config import DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')
    # print(f"Warning: Using default DB_PATH in NearExpiryReportDialog: {DB_PATH}")

# تابع اتصال به دیتابیس
def get_db_connection_local():
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

class NearExpiryReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("گزارش داروهای نزدیک به تاریخ انقضاء")
        self.setMinimumSize(800, 500)

        self._setup_ui()
        self._load_report() # بارگذاری اولیه گزارش با مقدار پیش‌فرض

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        compact_font = self.font(); compact_font.setPointSize(8)

        # --- بخش تنظیمات گزارش ---
        settings_layout = QHBoxLayout()
        
        lbl_period = QLabel("هشدار برای داروهایی که در")
        lbl_period.setFont(compact_font)
        settings_layout.addWidget(lbl_period)

        self.period_combo = QComboBox()
        self.period_combo.setFont(compact_font)
        self.period_combo.addItems(["۱ ماه آینده", "۲ ماه آینده", "۳ ماه آینده", "۶ ماه آینده", "۱۲ ماه آینده"])
        self.period_combo.setCurrentIndex(2) # پیش‌فرض ۳ ماه
        self.period_combo.setFixedWidth(120)
        settings_layout.addWidget(self.period_combo)

        lbl_expire = QLabel("منقضی می‌شوند:")
        lbl_expire.setFont(compact_font)
        settings_layout.addWidget(lbl_expire)
        settings_layout.addStretch(1)

        self.refresh_button = QPushButton("به‌روزرسانی گزارش")
        self.refresh_button.setFont(compact_font)
        self.refresh_button.clicked.connect(self._load_report)
        settings_layout.addWidget(self.refresh_button)
        main_layout.addLayout(settings_layout)

        # --- جدول نمایش داروها ---
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(6) # نام دارو، شماره بچ، تاریخ انقضا شمسی، تعداد بسته، تعداد واحد، نام تامین کننده
        self.report_table.setHorizontalHeaderLabels([
            "نام دارو (snapshot)", "شماره بچ", "تاریخ انقضا (شمسی)", 
            "تعداد بسته مانده", "تعداد واحد مانده", "تامین کننده"
        ])
        self.report_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.report_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setStyleSheet("QTableWidget { alternate-background-color: #f8f8f8; } QHeaderView::section { background-color: #e8e8e8; padding: 3px; }")
        self.report_table.setFont(compact_font)
        self.report_table.horizontalHeader().setFont(compact_font)


        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)     # Drug Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # Batch
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Expiry
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Package Count
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # Unit Count
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch) # Supplier
        
        self.report_table.setColumnWidth(1, 100)
        self.report_table.setColumnWidth(2, 100)
        self.report_table.setColumnWidth(3, 110)
        self.report_table.setColumnWidth(4, 110)

        main_layout.addWidget(self.report_table, 1)

        # --- دکمه بستن ---
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch(1)
        self.close_button = QPushButton("بستن")
        self.close_button.setFont(compact_font)
        self.close_button.clicked.connect(self.accept)
        close_button_layout.addWidget(self.close_button)
        main_layout.addLayout(close_button_layout)

    def _get_months_from_selection(self):
        """بازگرداندن تعداد ماه‌ها بر اساس انتخاب کاربر در کامبوباکس."""
        current_text = self.period_combo.currentText()
        if "۱ ماه" in current_text: return 1
        if "۲ ماه" in current_text: return 2
        if "۳ ماه" in current_text: return 3
        if "۶ ماه" in current_text: return 6
        if "۱۲ ماه" in current_text: return 12
        return 3 # پیش‌فرض

    def _load_report(self):
        self.report_table.setRowCount(0)
        months_to_expiry = self._get_months_from_selection()
        
        today_date = datetime.now().date()
        # برای محاسبه تاریخ هدف، به تاریخ امروز به تعداد ماه‌های انتخاب شده روز اضافه می‌کنیم (تقریبی)
        # راه دقیق‌تر استفاده از dateutil.relativedelta است، اما برای سادگی فعلی از timedelta استفاده می‌کنیم.
        # این تقریب برای ماه‌های با تعداد روز متفاوت ممکن است کاملا دقیق نباشد، اما برای گزارش کلی مناسب است.
        try:
            # یک روش ساده‌تر و معمولاً کافی برای محاسبه تاریخ آینده برای ماه‌های مختلف:
            target_year = today_date.year
            target_month = today_date.month + months_to_expiry
            target_day = today_date.day

            while target_month > 12:
                target_month -= 12
                target_year += 1
            
            # اطمینان از معتبر بودن روز در ماه هدف (مثلا اگر امروز ۳۱ فروردین است و ماه بعد ۳۰ روزه باشد)
            max_days_in_target_month = (QDate(target_year, target_month, 1).addMonths(1).addDays(-1)).day()
            target_day = min(target_day, max_days_in_target_month)

            target_expiry_date_dt = datetime(target_year, target_month, target_day).date()

        except ValueError: # برای مدیریت سال کبیسه و ... اگر محاسبات پیچیده شود
             target_expiry_date_dt = today_date + timedelta(days=months_to_expiry * 30) # تقریب ساده‌تر

        target_expiry_date_str = target_expiry_date_dt.strftime("%Y/%m/%d")
        today_date_str = today_date.strftime("%Y/%m/%d")

        conn = None
        try:
            conn = get_db_connection_local()
            cursor = conn.cursor()
            
            # انتخاب داروهایی که تاریخ انقضای میلادی آنها بین امروز و تاریخ هدف است
            # و تعداد بسته یا واحد آنها بیشتر از صفر است.
            # همچنین نام تامین‌کننده را از جدول company_purchases دریافت می‌کنیم.
            query = """
                SELECT 
                    cpi.drug_name_snapshot, 
                    cpi.batch_number, 
                    cpi.expiry_date_jalali, -- یا cpi.expiry_date_gregorian اگر می‌خواهید آن را تبدیل کنید
                    cpi.package_count, 
                    cpi.unit_count,
                    cp.supplier_name
                FROM company_purchase_items cpi
                JOIN company_purchases cp ON cpi.purchase_document_id = cp.id
                WHERE cpi.expiry_date_gregorian >= ? 
                  AND cpi.expiry_date_gregorian <= ?
                  AND (cpi.package_count > 0 OR cpi.unit_count > 0)
                ORDER BY cpi.expiry_date_gregorian ASC
            """
            
            cursor.execute(query, (today_date_str, target_expiry_date_str))
            items = cursor.fetchall()

            if not items:
                QMessageBox.information(self, "گزارش", f"هیچ دارویی با تاریخ انقضای نزدیک (در {months_to_expiry} ماه آینده) یافت نشد.")
                return

            for row_num, item_data in enumerate(items):
                self.report_table.insertRow(row_num)
                self.report_table.setItem(row_num, 0, QTableWidgetItem(item_data[0])) # drug_name_snapshot
                self.report_table.setItem(row_num, 1, QTableWidgetItem(item_data[1])) # batch_number
                self.report_table.setItem(row_num, 2, QTableWidgetItem(item_data[2])) # expiry_date_jalali
                self.report_table.setItem(row_num, 3, QTableWidgetItem(str(item_data[3]))) # package_count
                self.report_table.setItem(row_num, 4, QTableWidgetItem(str(item_data[4]))) # unit_count
                self.report_table.setItem(row_num, 5, QTableWidgetItem(item_data[5])) # supplier_name
        
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در تهیه گزارش داروهای تاریخ نزدیک: {e}")
        except Exception as ex:
            QMessageBox.critical(self, "خطا", f"یک خطای پیش بینی نشده رخ داد: {str(ex)}")
        finally:
            if conn:
                conn.close()