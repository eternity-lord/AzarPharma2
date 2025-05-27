# dialogs/sales_report_dialog.py

import sqlite3
import os
from datetime import datetime
import traceback # برای نمایش جزئیات خطا
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QFrame, QGridLayout, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

# به مسیر دهی DB_PATH توجه کنید.
try:
    from config import DB_PATH
    # اطمینان از اینکه get_connection از database.db ایمپورت می‌شود (اگر لازم است)
    # from database.db import get_connection as central_get_connection 
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')
    # print(f"Warning: Using default DB_PATH in SalesReportDialog: {DB_PATH}")

# تابع اتصال به دیتابیس (بهتر است از database.db ایمپورت شود)
# این تابع باید row_factory را تنظیم کند.
def get_db_connection_local_sales_report(): # نامگذاری مجزا برای این فایل
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row 
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# استراتژی ایمپورت مشابه سایر دیالوگ‌ها برای یکنواختی
CENTRAL_IMPORT_SUCCESSFUL_SR = False
try:
    from config import DB_PATH as CENTRAL_DB_PATH_SR
    from database.db import get_connection as central_get_connection_sr
    # print("SalesReportDialog: Using central DB_PATH and get_connection.")
    CENTRAL_IMPORT_SUCCESSFUL_SR = True
except ImportError:
    # print("SalesReportDialog: Central import failed. Using local fallback.")
    pass # از get_db_connection_local_sales_report و DB_PATH بالا استفاده خواهد شد

if CENTRAL_IMPORT_SUCCESSFUL_SR:
    current_DB_PATH_for_sr = CENTRAL_DB_PATH_SR
    get_current_sr_db_connection = lambda: central_get_connection_sr(current_DB_PATH_for_sr)
else:
    current_DB_PATH_for_sr = DB_PATH # DB_PATH تعریف شده در بالای فایل (fallback یا از config اگر فقط DB_PATH ایمپورت شده)
    get_current_sr_db_connection = get_db_connection_local_sales_report


class SalesReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("گزارش فروش")
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._load_report()

    def _setup_ui(self):
        # ... (بخش UI این متد بدون تغییر از پاسخ قبلی - شماره ۵۵) ...
        # فقط برای کامل بودن، اینجا تکرار می‌شود
        main_layout = QVBoxLayout(self)
        compact_font = QFont(); compact_font.setPointSize(8)
        label_font = QFont(); label_font.setPointSize(9); label_font.setBold(True)

        filter_frame = QFrame(); filter_frame.setFrameShape(QFrame.Shape.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame); filter_layout.setContentsMargins(5,5,5,5)
        lbl_start_date = QLabel("از تاریخ:"); lbl_start_date.setFont(compact_font); filter_layout.addWidget(lbl_start_date)
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(1-QDate.currentDate().day()))
        self.start_date_edit.setFont(compact_font); self.start_date_edit.setCalendarPopup(True); self.start_date_edit.setDisplayFormat("yyyy/MM/dd")
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addSpacing(15)
        lbl_end_date = QLabel("تا تاریخ:"); lbl_end_date.setFont(compact_font); filter_layout.addWidget(lbl_end_date)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setFont(compact_font); self.end_date_edit.setCalendarPopup(True); self.end_date_edit.setDisplayFormat("yyyy/MM/dd")
        filter_layout.addWidget(self.end_date_edit)
        filter_layout.addStretch(1)
        self.show_report_button = QPushButton("نمایش گزارش"); self.show_report_button.setFont(compact_font)
        self.show_report_button.clicked.connect(self._load_report); filter_layout.addWidget(self.show_report_button)
        main_layout.addWidget(filter_frame)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(10) 
        self.sales_table.setHorizontalHeaderLabels(["تاریخ", "زمان", "نوع فروش", "شماره سند", "نام کالا/دارو", "تعداد", "قیمت واحد", "جمع ردیف", "بیمار", "پزشک"])
        self.sales_table.setFont(compact_font); self.sales_table.horizontalHeader().setFont(compact_font)
        self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.sales_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sales_table.setAlternatingRowColors(True); self.sales_table.setStyleSheet("QTableWidget { alternate-background-color: #f8f8f8; } QHeaderView::section { background-color: #e8e8e8; padding: 3px; }")
        self.sales_table.setSortingEnabled(True)
        header = self.sales_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive); header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive); header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch); header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive); header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch); header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)
        self.sales_table.setColumnWidth(0, 75); self.sales_table.setColumnWidth(1, 60); self.sales_table.setColumnWidth(2, 70); self.sales_table.setColumnWidth(3, 80)
        self.sales_table.setColumnWidth(5, 50); self.sales_table.setColumnWidth(6, 80); self.sales_table.setColumnWidth(7, 90)
        main_layout.addWidget(self.sales_table, 1)

        summary_totals_frame = QFrame(); summary_totals_layout = QGridLayout(summary_totals_frame); summary_totals_layout.setContentsMargins(5,8,5,8)
        self.total_sales_count_label = QLabel("تعداد کل فروش‌ها (فاکتور/نسخه): ۰"); self.total_sales_count_label.setFont(label_font)
        summary_totals_layout.addWidget(self.total_sales_count_label, 0, 0, Qt.AlignmentFlag.AlignRight)
        self.total_sales_amount_label = QLabel("جمع کل مبلغ فروش: ۰ ریال"); self.total_sales_amount_label.setFont(label_font)
        self.total_sales_amount_label.setStyleSheet("color: blue;"); summary_totals_layout.addWidget(self.total_sales_amount_label, 0, 1, Qt.AlignmentFlag.AlignRight)
        summary_totals_layout.setColumnStretch(0,1); main_layout.addWidget(summary_totals_frame)
        close_button = QPushButton("بستن"); close_button.setFont(compact_font); close_button.clicked.connect(self.accept)
        close_button_layout = QHBoxLayout(); close_button_layout.addStretch(1); close_button_layout.addWidget(close_button); main_layout.addLayout(close_button_layout)


    def _format_date_for_display(self, date_str_gregorian):
        # ... (این متد بدون تغییر از پاسخ قبلی) ...
        if not date_str_gregorian: return ""
        try:
            dt_obj = datetime.strptime(date_str_gregorian, "%Y/%m/%d")
            # از persiantools.jdatetime import JalaliDate  باید در ابتدای فایل باشد
            # برای سادگی اینجا فرض میکنیم ایمپورت شده
            from persiantools.jdatetime import JalaliDate 
            jalali_date = JalaliDate(dt_obj.year, dt_obj.month, dt_obj.day)
            return jalali_date.strftime("%Y/%m/%d")
        except ValueError: return date_str_gregorian
        except NameError: return date_str_gregorian # اگر JalaliDate ایمپورت نشده بود


    def _load_report(self):
        self.sales_table.setSortingEnabled(False)
        self.sales_table.setRowCount(0)
        
        start_date_q = self.start_date_edit.date()
        end_date_q = self.end_date_edit.date()
        start_date_str = start_date_q.toString("yyyy/MM/dd")
        end_date_str = end_date_q.toString("yyyy/MM/dd")

        all_sale_items = []
        total_amount_sum = 0
        unique_sales_ids = set()

        conn = None
        try:
            conn = get_current_sr_db_connection() # استفاده از تابع اتصال مدیریت شده
            cursor = conn.cursor()

            # ۱. خواندن اقلام فروش نسخه‌ای
            query_rx = """
                SELECT 
                    p.date AS sale_date, 
                    'نسخه' AS sale_type,
                    p.prescription_number AS document_number,
                    pi.drug_name AS item_name, -- <--- اصلاح شده: pi.drug_name به جای pi.item_name_snapshot
                    pi.generic_code,
                    pi.quantity,
                    pi.unit_price,
                    pi.total_price,
                    p.patient_first_name || ' ' || p.patient_last_name AS patient_name,
                    IFNULL(d.first_name, '') || ' ' || IFNULL(d.last_name, '') AS doctor_name, -- استفاده از IFNULL برای جلوگیری از None
                    p.id AS sale_id 
                FROM prescription_items pi
                JOIN prescriptions p ON pi.prescription_id = p.id
                LEFT JOIN doctors d ON p.doctor_id = d.id
                WHERE p.date >= ? AND p.date <= ?
            """
            cursor.execute(query_rx, (start_date_str, end_date_str))
            for row in cursor.fetchall(): # row اینجا باید از نوع sqlite3.Row باشد
                all_sale_items.append(dict(row)) # تبدیل به دیکشنری برای یکنواختی با OTC
                total_amount_sum += row["total_price"] or 0
                unique_sales_ids.add(f"rx_{row['sale_id']}")

            # ۲. خواندن اقلام فروش OTC
            query_otc = """
                SELECT
                    os.sale_date,
                    os.sale_time,
                    'OTC' AS sale_type,
                    os.id AS document_number, 
                    osi.item_name_snapshot, -- اینجا item_name_snapshot صحیح است
                    osi.generic_code,
                    osi.quantity,
                    osi.unit_price,
                    osi.total_price,
                    NULL AS patient_name, 
                    NULL AS doctor_name,   
                    os.id AS sale_id 
                FROM otc_sale_items osi
                JOIN otc_sales os ON osi.otc_sale_id = os.id
                WHERE os.sale_date >= ? AND os.sale_date <= ?
            """
            cursor.execute(query_otc, (start_date_str, end_date_str))
            for row in cursor.fetchall(): # row اینجا هم باید از نوع sqlite3.Row باشد
                item_dict = dict(row) # تبدیل به دیکشنری
                item_dict["item_name"] = item_dict.pop("item_name_snapshot") # تغییر نام کلید برای یکنواختی
                # ایجاد فیلد برای مرتب‌سازی
                item_dict["_sort_datetime"] = datetime.strptime(f"{row['sale_date']} {row['sale_time'] or '00:00:00'}", "%Y/%m/%d %H:%M:%S")
                all_sale_items.append(item_dict)
                total_amount_sum += row["total_price"] or 0
                unique_sales_ids.add(f"otc_{row['sale_id']}")
            
            # مرتب‌سازی تمام اقلام
            all_sale_items.sort(key=lambda x: x.get("_sort_datetime", datetime.strptime(x["sale_date"], "%Y/%m/%d")))

            if not all_sale_items:
                QMessageBox.information(self, "گزارش", f"هیچ فروش یا نسخه ای در بازه زمانی انتخاب شده یافت نشد.")
            
            for row_num, item_data in enumerate(all_sale_items):
                self.sales_table.insertRow(row_num)
                self.sales_table.setItem(row_num, 0, QTableWidgetItem(item_data["sale_date"]))
                self.sales_table.setItem(row_num, 1, QTableWidgetItem(item_data.get("sale_time", "")))
                self.sales_table.setItem(row_num, 2, QTableWidgetItem(item_data["sale_type"]))
                self.sales_table.setItem(row_num, 3, QTableWidgetItem(str(item_data["document_number"])))
                self.sales_table.setItem(row_num, 4, QTableWidgetItem(item_data["item_name"]))
                self.sales_table.setItem(row_num, 5, QTableWidgetItem(str(item_data.get("quantity",0))))
                self.sales_table.setItem(row_num, 6, QTableWidgetItem(f"{item_data.get('unit_price',0):,.0f}"))
                self.sales_table.setItem(row_num, 7, QTableWidgetItem(f"{item_data.get('total_price',0):,.0f}"))
                self.sales_table.setItem(row_num, 8, QTableWidgetItem(item_data.get("patient_name", "")))
                self.sales_table.setItem(row_num, 9, QTableWidgetItem(item_data.get("doctor_name", "").strip())) # .strip() برای حذف فضاهای اضافی احتمالی

            self.total_sales_count_label.setText(f"تعداد کل فاکتور/نسخه: {len(unique_sales_ids)}")
            self.total_sales_amount_label.setText(f"جمع کل مبلغ فروش: {total_amount_sum:,.0f} ریال")

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در تهیه گزارش فروش: {e}\n{traceback.format_exc()}")
        except Exception as ex:
            QMessageBox.critical(self, "خطای ناشناخته", f"یک خطای پیش بینی نشده رخ داد: {ex}\n{traceback.format_exc()}")
        finally:
            if conn:
                conn.close()
            self.sales_table.setSortingEnabled(True)