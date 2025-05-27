# ui/dialogs/profit_loss_report_dialog.py
import sqlite3
import os
from datetime import datetime
import traceback
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QFrame, QGridLayout, QComboBox, QAbstractItemView,
    QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

# استفاده از همان سیستم DB موجود
try:
    from config import DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')

def get_db_connection_profit_loss():
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

class ProfitLossReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("گزارش سود و زیان")
        self.setMinimumSize(1000, 700)
        
        self._setup_ui()
        self._load_report()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        compact_font = QFont()
        compact_font.setPointSize(9)
        
        header_font = QFont()
        header_font.setPointSize(10)
        header_font.setBold(True)

        # --- فریم فیلترها ---
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.Shape.StyledPanel)
        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(10, 10, 10, 10)

        # تاریخ شروع
        lbl_start = QLabel("از تاریخ:")
        lbl_start.setFont(compact_font)
        filter_layout.addWidget(lbl_start, 0, 0)
        
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setFont(compact_font)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy/MM/dd")
        filter_layout.addWidget(self.start_date_edit, 0, 1)

        # تاریخ پایان
        lbl_end = QLabel("تا تاریخ:")
        lbl_end.setFont(compact_font)
        filter_layout.addWidget(lbl_end, 0, 2)
        
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setFont(compact_font)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy/MM/dd")
        filter_layout.addWidget(self.end_date_edit, 0, 3)

        # نوع گزارش
        lbl_type = QLabel("نوع گزارش:")
        lbl_type.setFont(compact_font)
        filter_layout.addWidget(lbl_type, 1, 0)
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.setFont(compact_font)
        self.report_type_combo.addItems([
            "خلاصه کلی",
            "تفکیک روزانه", 
            "تفکیک ماهانه",
            "تفکیک بر اساس دارو"
        ])
        filter_layout.addWidget(self.report_type_combo, 1, 1)

        # دکمه تولید گزارش
        self.generate_btn = QPushButton("تولید گزارش")
        self.generate_btn.setFont(header_font)
        self.generate_btn.clicked.connect(self._load_report)
        filter_layout.addWidget(self.generate_btn, 1, 2)

        # دکمه خروجی
        self.export_btn = QPushButton("خروجی Excel")
        self.export_btn.setFont(compact_font)
        self.export_btn.clicked.connect(self._export_report)
        filter_layout.addWidget(self.export_btn, 1, 3)

        main_layout.addWidget(filter_frame)

        # --- بخش خلاصه ---
        summary_frame = QGroupBox("خلاصه کلی")
        summary_frame.setFont(header_font)
        summary_layout = QHBoxLayout(summary_frame)

        self.total_sales_lbl = QLabel("کل فروش: 0 ریال")
        self.total_cost_lbl = QLabel("کل هزینه: 0 ریال")
        self.total_profit_lbl = QLabel("کل سود: 0 ریال")
        self.profit_margin_lbl = QLabel("درصد سود: 0%")

        for lbl in [self.total_sales_lbl, self.total_cost_lbl, 
                   self.total_profit_lbl, self.profit_margin_lbl]:
            lbl.setFont(compact_font)
            summary_layout.addWidget(lbl)

        main_layout.addWidget(summary_frame)

        # --- جدول جزئیات ---
        self.detail_table = QTableWidget()
        self.detail_table.setFont(compact_font)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.detail_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.detail_table)

    def _load_report(self):
        """تولید گزارش بر اساس نوع انتخاب شده"""
        report_type = self.report_type_combo.currentText()
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        if report_type == "خلاصه کلی":
            self._load_summary_report(start_date, end_date)
        elif report_type == "تفکیک روزانه":
            self._load_daily_report(start_date, end_date)
        elif report_type == "تفکیک ماهانه":
            self._load_monthly_report(start_date, end_date)
        elif report_type == "تفکیک بر اساس دارو":
            self._load_drug_report(start_date, end_date)

    def _load_summary_report(self, start_date, end_date):
        """گزارش خلاصه کلی"""
        conn = None
        try:
            conn = get_db_connection_profit_loss()
            cursor = conn.cursor()
            
            # کوئری اصلاح شده - بدون استفاده از ستون ناموجود
            query = """
                SELECT 
                    SUM(total_sales) as total_sales,
                    COUNT(*) as total_transactions,
                    AVG(total_sales) as avg_transaction_value
                FROM (
                    -- فروش نسخه‌ای
                    SELECT 
                        pi.total_price as total_sales
                    FROM prescription_items pi
                    JOIN prescriptions p ON pi.prescription_id = p.id
                    WHERE p.date BETWEEN ? AND ?
                    
                    UNION ALL
                    
                    -- فروش آزاد (OTC)
                    SELECT 
                        osi.total_price as total_sales
                    FROM otc_sale_items osi
                    JOIN otc_sales os ON osi.otc_sale_id = os.id
                    WHERE os.sale_date BETWEEN ? AND ?
                ) as all_sales
            """
            
            cursor.execute(query, [start_date, end_date, start_date, end_date])
            result = cursor.fetchone()
            
            total_sales = result['total_sales'] or 0
            total_transactions = result['total_transactions'] or 0
            avg_transaction = result['avg_transaction_value'] or 0
            
            # فرض می‌کنیم هزینه 70% فروش باشد (قابل تنظیم)
            estimated_cost = total_sales * 0.7
            estimated_profit = total_sales - estimated_cost
            profit_margin = (estimated_profit / total_sales * 100) if total_sales > 0 else 0
            
            # به‌روزرسانی برچسب‌ها
            self.total_sales_lbl.setText(f"کل فروش: {total_sales:,.0f} ریال")
            self.total_cost_lbl.setText(f"تخمینی هزینه: {estimated_cost:,.0f} ریال")
            self.total_profit_lbl.setText(f"تخمینی سود: {estimated_profit:,.0f} ریال")
            self.profit_margin_lbl.setText(f"درصد سود: {profit_margin:.1f}%")
            
            # تنظیم جدول خلاصه
            self.detail_table.setColumnCount(2)
            self.detail_table.setHorizontalHeaderLabels(["شرح", "مقدار"])
            self.detail_table.setRowCount(4)
            
            items = [
                ("تعداد کل تراکنش‌ها", f"{total_transactions:,}"),
                ("میانگین ارزش تراکنش", f"{avg_transaction:,.0f} ریال"),
                ("کل فروش", f"{total_sales:,.0f} ریال"),
                ("تخمینی سود خالص", f"{estimated_profit:,.0f} ریال")
            ]
            
            for row, (desc, value) in enumerate(items):
                self.detail_table.setItem(row, 0, QTableWidgetItem(desc))
                self.detail_table.setItem(row, 1, QTableWidgetItem(value))
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش خلاصه: {e}")
            print(f"خطای دیتابیس: {traceback.format_exc()}")
        finally:
            if conn:
                conn.close()

    def _load_daily_report(self, start_date, end_date):
        """گزارش تفکیک روزانه - نسخه اصلاح شده"""
        conn = None
        try:
            conn = get_db_connection_profit_loss()
            cursor = conn.cursor()
            
            # کوئری اصلاح شده - بدون استفاده از ستون ناموجود
            query = """
                SELECT 
                    sale_date,
                    SUM(total_sales) as daily_sales,
                    COUNT(*) as transaction_count
                FROM (
                    -- فروش نسخه‌ای
                    SELECT 
                        p.date as sale_date,
                        pi.total_price as total_sales
                    FROM prescription_items pi
                    JOIN prescriptions p ON pi.prescription_id = p.id
                    WHERE p.date BETWEEN ? AND ?
                    
                    UNION ALL
                    
                    -- فروش آزاد
                    SELECT 
                        os.sale_date,
                        osi.total_price as total_sales
                    FROM otc_sale_items osi
                    JOIN otc_sales os ON osi.otc_sale_id = os.id
                    WHERE os.sale_date BETWEEN ? AND ?
                ) as daily_sales
                GROUP BY sale_date
                ORDER BY sale_date DESC
            """
            
            cursor.execute(query, [start_date, end_date, start_date, end_date])
            results = cursor.fetchall()
            
            # تنظیم جدول
            self.detail_table.setColumnCount(5)
            self.detail_table.setHorizontalHeaderLabels([
                "تاریخ", "تعداد تراکنش", "کل فروش", "تخمینی هزینه", "تخمینی سود"
            ])
            self.detail_table.setRowCount(len(results))
            
            total_sales = total_cost = total_profit = 0
            
            for row, data in enumerate(results):
                daily_sales = data['daily_sales'] or 0
                daily_cost = daily_sales * 0.7  # تخمین 70% هزینه
                daily_profit = daily_sales - daily_cost
                
                total_sales += daily_sales
                total_cost += daily_cost
                total_profit += daily_profit
                
                self.detail_table.setItem(row, 0, QTableWidgetItem(data['sale_date']))
                self.detail_table.setItem(row, 1, QTableWidgetItem(str(data['transaction_count'])))
                self.detail_table.setItem(row, 2, QTableWidgetItem(f"{daily_sales:,.0f}"))
                self.detail_table.setItem(row, 3, QTableWidgetItem(f"{daily_cost:,.0f}"))
                
                # رنگ‌بندی سود
                profit_item = QTableWidgetItem(f"{daily_profit:,.0f}")
                if daily_profit > 0:
                    profit_item.setBackground(QColor(232, 245, 232))  # سبز روشن
                elif daily_profit < 0:
                    profit_item.setBackground(QColor(255, 235, 238))  # قرمز روشن
                self.detail_table.setItem(row, 4, profit_item)
            
            # به‌روزرسانی خلاصه
            overall_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
            self.total_sales_lbl.setText(f"کل فروش: {total_sales:,.0f} ریال")
            self.total_cost_lbl.setText(f"تخمینی هزینه: {total_cost:,.0f} ریال")
            self.total_profit_lbl.setText(f"تخمینی سود: {total_profit:,.0f} ریال")
            self.profit_margin_lbl.setText(f"درصد سود: {overall_margin:.1f}%")
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش روزانه: {e}")
            print(f"خطای دیتابیس: {traceback.format_exc()}")
        finally:
            if conn:
                conn.close()

    def _load_monthly_report(self, start_date, end_date):
        """گزارش تفکیک ماهانه"""
        conn = None
        try:
            conn = get_db_connection_profit_loss()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    strftime('%Y-%m', sale_date) as month,
                    SUM(total_sales) as monthly_sales,
                    COUNT(*) as transaction_count
                FROM (
                    SELECT 
                        p.date as sale_date,
                        pi.total_price as total_sales
                    FROM prescription_items pi
                    JOIN prescriptions p ON pi.prescription_id = p.id
                    WHERE p.date BETWEEN ? AND ?
                    
                    UNION ALL
                    
                    SELECT 
                        os.sale_date,
                        osi.total_price as total_sales
                    FROM otc_sale_items osi
                    JOIN otc_sales os ON osi.otc_sale_id = os.id
                    WHERE os.sale_date BETWEEN ? AND ?
                ) as monthly_sales
                GROUP BY strftime('%Y-%m', sale_date)
                ORDER BY month DESC
            """
            
            cursor.execute(query, [start_date, end_date, start_date, end_date])
            results = cursor.fetchall()
            
            # تنظیم جدول
            self.detail_table.setColumnCount(5)
            self.detail_table.setHorizontalHeaderLabels([
                "ماه", "تعداد تراکنش", "کل فروش", "تخمینی هزینه", "تخمینی سود"
            ])
            self.detail_table.setRowCount(len(results))
            
            total_sales = total_cost = total_profit = 0
            
            for row, data in enumerate(results):
                monthly_sales = data['monthly_sales'] or 0
                monthly_cost = monthly_sales * 0.7
                monthly_profit = monthly_sales - monthly_cost
                
                total_sales += monthly_sales
                total_cost += monthly_cost
                total_profit += monthly_profit
                
                self.detail_table.setItem(row, 0, QTableWidgetItem(data['month']))
                self.detail_table.setItem(row, 1, QTableWidgetItem(str(data['transaction_count'])))
                self.detail_table.setItem(row, 2, QTableWidgetItem(f"{monthly_sales:,.0f}"))
                self.detail_table.setItem(row, 3, QTableWidgetItem(f"{monthly_cost:,.0f}"))
                self.detail_table.setItem(row, 4, QTableWidgetItem(f"{monthly_profit:,.0f}"))
            
            # به‌روزرسانی خلاصه
            overall_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
            self.total_sales_lbl.setText(f"کل فروش: {total_sales:,.0f} ریال")
            self.total_cost_lbl.setText(f"تخمینی هزینه: {total_cost:,.0f} ریال")
            self.total_profit_lbl.setText(f"تخمینی سود: {total_profit:,.0f} ریال")
            self.profit_margin_lbl.setText(f"درصد سود: {overall_margin:.1f}%")
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش ماهانه: {e}")
        finally:
            if conn:
                conn.close()

    def _load_drug_report(self, start_date, end_date):
        """گزارش تفکیک بر اساس دارو"""
        conn = None
        try:
            conn = get_db_connection_profit_loss()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    drug_name,
                    generic_code,
                    SUM(quantity) as total_quantity,
                    SUM(total_sales) as drug_sales,
                    COUNT(*) as sale_count
                FROM (
                    SELECT 
                        pi.drug_name,
                        pi.generic_code,
                        pi.quantity,
                        pi.total_price as total_sales
                    FROM prescription_items pi
                    JOIN prescriptions p ON pi.prescription_id = p.id
                    WHERE p.date BETWEEN ? AND ?
                    
                    UNION ALL
                    
                    SELECT 
                        osi.drug_name,
                        osi.generic_code,
                        osi.quantity,
                        osi.total_price as total_sales
                    FROM otc_sale_items osi
                    JOIN otc_sales os ON osi.otc_sale_id = os.id
                    WHERE os.sale_date BETWEEN ? AND ?
                ) as drug_sales
                GROUP BY generic_code, drug_name
                ORDER BY drug_sales DESC
            """
            
            cursor.execute(query, [start_date, end_date, start_date, end_date])
            results = cursor.fetchall()
            
            # تنظیم جدول
            self.detail_table.setColumnCount(6)
            self.detail_table.setHorizontalHeaderLabels([
                "نام دارو", "کد ژنریک", "تعداد فروخته شده", "تعداد فروش", "کل فروش", "تخمینی سود"
            ])
            self.detail_table.setRowCount(len(results))
            
            total_sales = total_profit = 0
            
            for row, data in enumerate(results):
                drug_sales = data['drug_sales'] or 0
                drug_profit = drug_sales * 0.3  # فرض 30% سود
                
                total_sales += drug_sales
                total_profit += drug_profit
                
                self.detail_table.setItem(row, 0, QTableWidgetItem(data['drug_name'] or ''))
                self.detail_table.setItem(row, 1, QTableWidgetItem(data['generic_code'] or ''))
                self.detail_table.setItem(row, 2, QTableWidgetItem(str(data['total_quantity'] or 0)))
                self.detail_table.setItem(row, 3, QTableWidgetItem(str(data['sale_count'] or 0)))
                self.detail_table.setItem(row, 4, QTableWidgetItem(f"{drug_sales:,.0f}"))
                self.detail_table.setItem(row, 5, QTableWidgetItem(f"{drug_profit:,.0f}"))
            
            # به‌روزرسانی خلاصه
            total_cost = total_sales - total_profit
            overall_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
            self.total_sales_lbl.setText(f"کل فروش: {total_sales:,.0f} ریال")
            self.total_cost_lbl.setText(f"تخمینی هزینه: {total_cost:,.0f} ریال")
            self.total_profit_lbl.setText(f"تخمینی سود: {total_profit:,.0f} ریال")
            self.profit_margin_lbl.setText(f"درصد سود: {overall_margin:.1f}%")
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش داروها: {e}")
        finally:
            if conn:
                conn.close()

    def _export_report(self):
        """خروجی Excel"""
        try:
            # این بخش می‌تواند با کتابخانه openpyxl پیاده‌سازی شود
            QMessageBox.information(self, "اطلاع", "قابلیت خروجی Excel در نسخه بعدی اضافه خواهد شد.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در خروجی: {e}")

