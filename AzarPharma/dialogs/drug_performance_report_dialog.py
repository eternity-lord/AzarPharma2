# dialogs/drug_performance_report_dialog.py

import sqlite3
import os
from datetime import datetime
import traceback
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QFrame, QGridLayout, QComboBox, QSpinBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

# به مسیر دهی DB_PATH توجه کنید.
try:
    from config import DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')

def get_db_connection_local_perf_report(): # نامگذاری مجزا
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir): os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row 
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

CENTRAL_IMPORT_SUCCESSFUL_DPR = False
try:
    from config import DB_PATH as CENTRAL_DB_PATH_DPR
    from database.db import get_connection as central_get_connection_dpr
    CENTRAL_IMPORT_SUCCESSFUL_DPR = True
except ImportError:
    pass

if CENTRAL_IMPORT_SUCCESSFUL_DPR:
    current_DB_PATH_for_dpr = CENTRAL_DB_PATH_DPR
    get_current_dpr_db_connection = lambda: central_get_connection_dpr(current_DB_PATH_for_dpr)
else:
    current_DB_PATH_for_dpr = DB_PATH 
    get_current_dpr_db_connection = get_db_connection_local_perf_report


class DrugPerformanceReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("گزارش عملکرد داروها (پرفروش/کم‌فروش)")
        self.setMinimumSize(800, 550)

        self._setup_ui()
        self._load_report() # بارگذاری اولیه

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        compact_font = QFont(); compact_font.setPointSize(8)
        
        filter_frame = QFrame(); filter_frame.setFrameShape(QFrame.Shape.StyledPanel)
        filter_layout = QGridLayout(filter_frame); filter_layout.setContentsMargins(5,5,5,5)
        filter_layout.setHorizontalSpacing(10); filter_layout.setVerticalSpacing(5)

        lbl_start_date = QLabel("از تاریخ:"); lbl_start_date.setFont(compact_font)
        filter_layout.addWidget(lbl_start_date, 0, 0)
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(1-QDate.currentDate().day()))
        self.start_date_edit.setFont(compact_font); self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy/MM/dd"); filter_layout.addWidget(self.start_date_edit, 0, 1)

        lbl_end_date = QLabel("تا تاریخ:"); lbl_end_date.setFont(compact_font)
        filter_layout.addWidget(lbl_end_date, 0, 2)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setFont(compact_font); self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy/MM/dd"); filter_layout.addWidget(self.end_date_edit, 0, 3)

        lbl_report_type = QLabel("نوع گزارش:"); lbl_report_type.setFont(compact_font)
        filter_layout.addWidget(lbl_report_type, 1, 0)
        self.report_type_combo = QComboBox(); self.report_type_combo.setFont(compact_font)
        self.report_type_combo.addItems([
            "پرفروش‌ترین‌ها (تعدادی)", 
            "پرفروش‌ترین‌ها (مبلغی)",
            "کم‌فروش‌ترین‌ها (تعدادی)",
            # "کم‌فروش‌ترین‌ها (مبلغی)" # می‌توان اضافه کرد
        ])
        filter_layout.addWidget(self.report_type_combo, 1, 1, 1, 2) # Span 2 columns

        lbl_count = QLabel("تعداد نمایش:"); lbl_count.setFont(compact_font)
        filter_layout.addWidget(lbl_count, 1, 3, Qt.AlignmentFlag.AlignRight)
        self.item_count_spin = QSpinBox(); self.item_count_spin.setFont(compact_font)
        self.item_count_spin.setRange(5, 100); self.item_count_spin.setValue(10) # نمایش ۱۰ آیتم برتر/بدتر
        self.item_count_spin.setFixedWidth(70)
        filter_layout.addWidget(self.item_count_spin, 1, 4)
        
        filter_layout.setColumnStretch(2, 1) # ایجاد کمی فاصله قبل از تعداد نمایش

        self.show_report_button = QPushButton("نمایش گزارش"); self.show_report_button.setFont(compact_font)
        self.show_report_button.clicked.connect(self._load_report)
        filter_layout.addWidget(self.show_report_button, 0, 4, 1, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight) # دکمه در انتها
        main_layout.addWidget(filter_frame)

        self.report_table = QTableWidget()
        self.report_table.setColumnCount(5) 
        self.report_table.setHorizontalHeaderLabels(["رتبه", "کد ژنریک", "نام دارو", "تعداد کل فروش", "مبلغ کل فروش"])
        self.report_table.setFont(compact_font); self.report_table.horizontalHeader().setFont(compact_font)
        self.report_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.report_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.report_table.setAlternatingRowColors(True); self.report_table.setStyleSheet("QTableWidget { alternate-background-color: #f8f8f8; } QHeaderView::section { background-color: #e8e8e8; padding: 3px; }")
        self.report_table.setSortingEnabled(False) # مرتب‌سازی توسط کوئری انجام می‌شود

        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive) # رتبه
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # کد ژنریک
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)     # نام دارو
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # تعداد
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # مبلغ
        self.report_table.setColumnWidth(0, 40); self.report_table.setColumnWidth(1, 100)
        self.report_table.setColumnWidth(3, 100); self.report_table.setColumnWidth(4, 120)
        main_layout.addWidget(self.report_table, 1)

        close_button = QPushButton("بستن"); close_button.setFont(compact_font)
        close_button.clicked.connect(self.accept)
        close_button_layout = QHBoxLayout(); close_button_layout.addStretch(1); close_button_layout.addWidget(close_button)
        main_layout.addLayout(close_button_layout)

    def _load_report(self):
        self.report_table.setRowCount(0)
        
        start_date_str = self.start_date_edit.date().toString("yyyy/MM/dd")
        end_date_str = self.end_date_edit.date().toString("yyyy/MM/dd")
        report_type_text = self.report_type_combo.currentText()
        limit_count = self.item_count_spin.value()

        order_by_column = "total_quantity_sold"
        order_direction = "DESC" # پیش‌فرض برای پرفروش‌ترین‌ها

        if "مبلغی" in report_type_text:
            order_by_column = "total_amount_sold"
        
        if "کم‌فروش" in report_type_text:
            order_direction = "ASC"

        conn = None
        try:
            conn = get_current_dpr_db_connection()
            cursor = conn.cursor()

            # کوئری برای جمع‌آوری فروش از هر دو جدول اقلام نسخه و اقلام فروش OTC
            # و اتصال به جدول داروها برای گرفتن نام استاندارد دارو
            query = f"""
                SELECT
                    s.generic_code,
                    IFNULL(d.generic_name, s.item_name_snapshot) || ' (' || IFNULL(d.en_brand_name, '') || ')' as drug_display_name,
                    SUM(s.quantity_sold) as total_quantity_sold,
                    SUM(s.amount_sold) as total_amount_sold
                FROM (
                    SELECT 
                        pi.generic_code,
                        pi.drug_name as item_name_snapshot, -- نام دارو از آیتم نسخه
                        pi.quantity as quantity_sold,
                        pi.total_price as amount_sold
                    FROM prescription_items pi
                    JOIN prescriptions p ON pi.prescription_id = p.id
                    WHERE p.date BETWEEN ? AND ? AND pi.generic_code IS NOT NULL AND pi.generic_code != ''
                    
                    UNION ALL
                    
                    SELECT 
                        osi.generic_code, 
                        osi.item_name_snapshot,
                        osi.quantity as quantity_sold,
                        osi.total_price as amount_sold
                    FROM otc_sale_items osi
                    JOIN otc_sales os ON osi.otc_sale_id = os.id
                    WHERE os.sale_date BETWEEN ? AND ? AND osi.generic_code IS NOT NULL AND osi.generic_code != ''
                ) AS s
                LEFT JOIN drugs d ON s.generic_code = d.generic_code 
                WHERE s.generic_code IS NOT NULL AND s.generic_code != ''
                GROUP BY s.generic_code, drug_display_name 
                ORDER BY {order_by_column} {order_direction}
                LIMIT ?
            """
            
            # پارامترها برای کوئری (تاریخ‌ها دو بار تکرار می‌شوند برای UNION)
            params = [start_date_str, end_date_str, start_date_str, end_date_str, limit_count]
            
            cursor.execute(query, params)
            items = cursor.fetchall()

            if not items:
                QMessageBox.information(self, "گزارش", f"داده‌ای برای گزارش '{report_type_text}' در بازه زمانی انتخاب شده یافت نشد.")
                return

            for row_num, item_data in enumerate(items):
                self.report_table.insertRow(row_num)
                self.report_table.setItem(row_num, 0, QTableWidgetItem(str(row_num + 1))) # رتبه
                self.report_table.setItem(row_num, 1, QTableWidgetItem(item_data["generic_code"]))
                self.report_table.setItem(row_num, 2, QTableWidgetItem(item_data["drug_display_name"]))
                self.report_table.setItem(row_num, 3, QTableWidgetItem(str(item_data["total_quantity_sold"] or 0)))
                self.report_table.setItem(row_num, 4, QTableWidgetItem(f"{item_data['total_amount_sold'] or 0:,.0f}"))
        
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در تهیه گزارش عملکرد داروها: {e}\n{traceback.format_exc()}")
        except Exception as ex:
            QMessageBox.critical(self, "خطای ناشناخته", f"یک خطای پیش بینی نشده رخ داد: {ex}\n{traceback.format_exc()}")
        finally:
            if conn:
                conn.close()