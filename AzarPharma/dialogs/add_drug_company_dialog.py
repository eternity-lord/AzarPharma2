# dialogs/add_drug_company_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFrame, QGridLayout, QLabel, QComboBox, QDateEdit, QLineEdit, QHBoxLayout,
    QPushButton, QCheckBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QMessageBox
)
import sqlite3 # برای مدیریت خطاهای احتمالی دیتابیس
import os
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIntValidator, QDoubleValidator
from PyQt6.QtGui import QAction
import os
from database.db import get_connection
from dialogs.suppliers_management_dialog import SuppliersManagementDialog
from dialogs.add_drug_to_invoice_dialog import AddDrugToInvoiceDialog
from persiantools.jdatetime import JalaliDate

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmacy.db')

try:
    from config import DB_PATH
    from database.db import get_connection
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')
    print(f"Warning: Using local DB_PATH in AddDrugFromCompanyDialog: {DB_PATH}")
    def get_connection(db_path_param): # تعریف محلی در صورت عدم موفقیت ایمپورت
        db_dir = os.path.dirname(db_path_param)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(db_path_param, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


class AddDrugFromCompanyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ورود دارو به انبار / قفسه")
        self.setMinimumSize(1000, 700)

        self.invoice_items_data = [{
            "generic_code": "", "brand_code": "", "drug_name_snapshot": "", "quantity_in_package": 1,
            "package_count": 1, "unit_count": 0, "expiry_date_gregorian": "", "expiry_date_jalali": "",
            "purchase_price_per_package": 0, "profit_percentage": 0, "sale_price_per_package": 0,
            "item_vat": 9, "item_discount_rial": 0, "batch_number": "",
            "main_warehouse_location": "", "main_warehouse_min_stock": 0, "main_warehouse_max_stock": 0,
            "main_shelf_location": "", "main_shelf_min_stock": 0, "main_shelf_max_stock": 0
        }]

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- بخش مشخصات عمومی سند ---
        general_spec_frame = QFrame()
        general_spec_frame.setObjectName("SectionFrame")
        general_spec_layout = QGridLayout(general_spec_frame)
        general_spec_layout.setHorizontalSpacing(15)
        general_spec_layout.setVerticalSpacing(10)

        # نوع سند
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems(["خرید از شرکت‌ها", "برگشت از فروش", "انتقال انبار"])
        general_spec_layout.addWidget(QLabel("نوع سند:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        general_spec_layout.addWidget(self.doc_type_combo, 0, 1)

        # تاریخ ثبت
        self.reg_date_edit = QDateEdit(QDate.currentDate())
        self.reg_date_edit.setCalendarPopup(True)
        self.reg_date_edit.setDisplayFormat("yyyy/MM/dd")
        general_spec_layout.addWidget(QLabel("تاریخ ثبت:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        general_spec_layout.addWidget(self.reg_date_edit, 0, 3)
        
        # لیبل تاریخ شمسی
        self.reg_date_jalali_label = QLabel("")
        general_spec_layout.addWidget(self.reg_date_jalali_label, 0, 4)

        # شماره ردیف
        self.doc_id_display = QLineEdit()
        self.doc_id_display.setReadOnly(True)
        self.doc_id_display.setFixedWidth(100)
        general_spec_layout.addWidget(QLabel("شماره ردیف:"), 0, 5, Qt.AlignmentFlag.AlignRight)
        general_spec_layout.addWidget(self.doc_id_display, 0, 6)

        # طرف انبار
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("انتخاب کنید**")
        self.load_suppliers_to_combo()
        
        self.supplier_list_button = QPushButton("لیست طرف انبار")
        self.supplier_list_button.clicked.connect(self.show_supplier_list_dialog)
        
        supplier_layout = QHBoxLayout()
        supplier_layout.addWidget(self.supplier_combo, 1)
        supplier_layout.addWidget(self.supplier_list_button)
        
        general_spec_layout.addWidget(QLabel("طرف انبار:**"), 1, 0, Qt.AlignmentFlag.AlignRight)
        general_spec_layout.addLayout(supplier_layout, 1, 1, 1, 3)

        # توضیحات
        self.description_edit = QLineEdit()
        general_spec_layout.addWidget(QLabel("توضیحات:"), 1, 5, Qt.AlignmentFlag.AlignRight)
        general_spec_layout.addWidget(self.description_edit, 1, 6)

        main_layout.addWidget(general_spec_frame)

        # --- 2. چک باکس اعمال مستقیم در قفسه ---
        self.apply_direct_checkbox = QCheckBox("اعمال مستقیم تغییرات در موجودی قفسه")
        main_layout.addWidget(self.apply_direct_checkbox, alignment=Qt.AlignmentFlag.AlignRight)

        # --- 3. بخش مشخصات فاکتور ---
        invoice_frame = QFrame()
        invoice_frame.setObjectName("SectionFrame")
        invoice_layout = QGridLayout(invoice_frame)
        invoice_layout.setHorizontalSpacing(15)
        invoice_layout.setVerticalSpacing(10)

        self.invoice_type_combo = QComboBox()
        self.invoice_type_combo.addItems(["فاکتور عادی", "فاکتور رسمی"])
        invoice_layout.addWidget(QLabel("نوع فاکتور:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        invoice_layout.addWidget(self.invoice_type_combo, 0, 1)

        self.invoice_num_edit = QLineEdit()
        invoice_layout.addWidget(QLabel("شماره فاکتور:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        invoice_layout.addWidget(self.invoice_num_edit, 0, 3)

        self.invoice_date_edit = QDateEdit(QDate.currentDate())
        self.invoice_date_edit.setCalendarPopup(True)
        self.invoice_date_edit.setDisplayFormat("yyyy/MM/dd")
        invoice_layout.addWidget(QLabel("تاریخ فاکتور:"), 0, 4, Qt.AlignmentFlag.AlignRight)
        invoice_layout.addWidget(self.invoice_date_edit, 0, 5)

        self.invoice_date_jalali_label = QLabel("")
        invoice_layout.addWidget(self.invoice_date_jalali_label, 0, 6)

        self.settlement_days_edit = QLineEdit("0")
        self.settlement_days_edit.setValidator(QIntValidator(0, 1000))
        self.settlement_days_edit.setFixedWidth(70)
        invoice_layout.addWidget(QLabel("مدت تسویه (روز):"), 0, 7, Qt.AlignmentFlag.AlignRight)
        invoice_layout.addWidget(self.settlement_days_edit, 0, 8)

        self.settlement_date_edit = QDateEdit(QDate.currentDate())
        self.settlement_date_edit.setCalendarPopup(True)
        self.settlement_date_edit.setDisplayFormat("yyyy/MM/dd")
        invoice_layout.addWidget(QLabel("تاریخ تسویه:"), 0, 9, Qt.AlignmentFlag.AlignRight)
        invoice_layout.addWidget(self.settlement_date_edit, 0, 10)

        self.settlement_date_jalali_label = QLabel("")
        invoice_layout.addWidget(self.settlement_date_jalali_label, 0, 11)

        main_layout.addWidget(invoice_frame)

        # --- 4. جدول اقلام فاکتور ---
        items_frame = QFrame()
        items_frame.setObjectName("SectionFrame")
        items_layout = QVBoxLayout(items_frame)

        table_buttons_layout = QHBoxLayout()
        add_row_button = QPushButton("ردیف جدید")
        add_row_button.clicked.connect(self.add_invoice_item_row)
        table_buttons_layout.addWidget(add_row_button)
        edit_row_button = QPushButton("ویرایش ردیف")
        edit_row_button.clicked.connect(self.edit_selected_invoice_item_row)
        table_buttons_layout.addWidget(edit_row_button)
        delete_row_button = QPushButton("حذف ردیف")
        delete_row_button.clicked.connect(self.delete_selected_invoice_item_row)
        table_buttons_layout.addWidget(delete_row_button)
        table_buttons_layout.addStretch(1)
        items_layout.addLayout(table_buttons_layout)

        self.items_table = QTableWidget()
        # افزایش تعداد ستون‌ها برای شماره بچ و تاریخ انقضا
        self.items_table.setColumnCount(10) # قبلا 8 بود
        self.items_table.setHorizontalHeaderLabels([
            "کد ژنریک", "نام دارو", "شکل", "دوز", 
            "تعداد بسته", "فی خرید", "فی فروش", "قیمت کل خرید", # عنوان قیمت کل کمی دقیق‌تر شد
            "شماره بچ", "تاریخ انقضا" # ستون‌های جدید
        ])
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # ویرایش مستقیم غیرفعال
        self.items_table.cellDoubleClicked.connect(self.open_add_drug_to_invoice_dialog) # با دابل کلیک ویرایش می‌شود
        for i, width in enumerate([100, 200, 80, 80, 80, 100, 100, 120]):
            self.items_table.setColumnWidth(i, width)
        items_layout.addWidget(self.items_table, 1)
        main_layout.addWidget(items_frame, 1)

        # --- 5. بخش محاسبات نهایی ---
        summary_frame = QFrame()
        summary_frame.setObjectName("SectionFrame")
        summary_layout = QGridLayout(summary_frame)
        summary_layout.setHorizontalSpacing(15)
        summary_layout.setVerticalSpacing(10)

        self.total_purchase_price_label = QLabel("0 ریال")
        summary_layout.addWidget(QLabel("جمع کل قیمت خرید اقلام:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        summary_layout.addWidget(self.total_purchase_price_label, 0, 1, Qt.AlignmentFlag.AlignLeft)

        self.total_sale_price_label = QLabel("0 ریال")
        summary_layout.addWidget(QLabel("جمع کل قیمت فروش اقلام:"), 0, 2, Qt.AlignmentFlag.AlignRight)
        summary_layout.addWidget(self.total_sale_price_label, 0, 3, Qt.AlignmentFlag.AlignLeft)

        self.overall_discount_percent_edit = QLineEdit("0")
        self.overall_discount_percent_edit.setValidator(QDoubleValidator(0, 100, 2))
        self.overall_discount_percent_edit.setFixedWidth(70)
        summary_layout.addWidget(QLabel("تخفیف درصدی کلی (%):"), 1, 0, Qt.AlignmentFlag.AlignRight)
        summary_layout.addWidget(self.overall_discount_percent_edit, 1, 1, Qt.AlignmentFlag.AlignLeft)

        self.overall_discount_rial_edit = QLineEdit("0")
        self.overall_discount_rial_edit.setValidator(QIntValidator(0, 1000000000))
        summary_layout.addWidget(QLabel("تخفیف ریالی کلی:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        summary_layout.addWidget(self.overall_discount_rial_edit, 1, 3, Qt.AlignmentFlag.AlignLeft)

        self.total_tax_edit = QLineEdit("0")
        self.total_tax_edit.setValidator(QDoubleValidator(0, 100, 2))
        summary_layout.addWidget(QLabel("مالیات و عوارض کل (%):"), 2, 0, Qt.AlignmentFlag.AlignRight)
        summary_layout.addWidget(self.total_tax_edit, 2, 1, Qt.AlignmentFlag.AlignLeft)

        self.shipping_cost_edit = QLineEdit("0")
        self.shipping_cost_edit.setValidator(QIntValidator(0, 1000000000))
        summary_layout.addWidget(QLabel("هزینه حمل (ریال):"), 2, 2, Qt.AlignmentFlag.AlignRight)
        summary_layout.addWidget(self.shipping_cost_edit, 2, 3, Qt.AlignmentFlag.AlignLeft)

        self.payable_amount_label = QLabel("0 ریال")
        summary_layout.addWidget(QLabel("مبلغ قابل پرداخت:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        summary_layout.addWidget(self.payable_amount_label, 3, 1, 1, 3, Qt.AlignmentFlag.AlignLeft)

        main_layout.addWidget(summary_frame)

        # --- 6. دکمه‌های نهایی ---
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("ثبت سند")
        save_button.clicked.connect(self.save_document)
        buttons_layout.addWidget(save_button)
        cancel_button = QPushButton("انصراف")
        cancel_button.clicked.connect(self.close)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addStretch(1)
        main_layout.addLayout(buttons_layout)
        
        # اتصال تغییر تاریخ‌ها به تبدیل شمسی
        self.reg_date_edit.dateChanged.connect(self.update_date_edits_to_jalali)
        self.invoice_date_edit.dateChanged.connect(self.update_date_edits_to_jalali)
        self.settlement_date_edit.dateChanged.connect(self.update_date_edits_to_jalali)
        
        self.overall_discount_percent_edit.textChanged.connect(self.calculate_document_summary)
        self.overall_discount_rial_edit.textChanged.connect(self.calculate_document_summary)
        self.total_tax_edit.textChanged.connect(self.calculate_document_summary)
        self.shipping_cost_edit.textChanged.connect(self.calculate_document_summary)
        self.update_date_edits_to_jalali()
        self._update_items_table()
        self.calculate_document_summary()

    def update_date_edits_to_jalali(self):
        try:
            reg_date_g = self.reg_date_edit.date().toPyDate()
            reg_date_j = JalaliDate.to_jalali(reg_date_g.year, reg_date_g.month, reg_date_g.day)
            self.reg_date_jalali_label.setText(f"({reg_date_j.year}/{reg_date_j.month:02d}/{reg_date_j.day:02d})")
            invoice_date_g = self.invoice_date_edit.date().toPyDate()
            invoice_date_j = JalaliDate.to_jalali(invoice_date_g.year, invoice_date_g.month, invoice_date_g.day)
            self.invoice_date_jalali_label.setText(f"({invoice_date_j.year}/{invoice_date_j.month:02d}/{invoice_date_j.day:02d})")
            settlement_date_g = self.settlement_date_edit.date().toPyDate()
            settlement_date_j = JalaliDate.to_jalali(settlement_date_g.year, settlement_date_g.month, settlement_date_g.day)
            self.settlement_date_jalali_label.setText(f"({settlement_date_j.year}/{settlement_date_j.month:02d}/{settlement_date_j.day:02d})")
        except Exception as e:
            print(f"خطا در تبدیل تاریخ میلادی به شمسی: {e}")

    def show_supplier_list_dialog(self):
        dialog = SuppliersManagementDialog(self)
        if dialog.exec():
            self.load_suppliers_to_combo()
    
    def load_suppliers_to_combo(self):
        self.supplier_combo.clear()
        self.supplier_combo.addItem("انتخاب کنید**")
        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM suppliers ORDER BY name")
            suppliers = cursor.fetchall()
            for supplier in suppliers:
                self.supplier_combo.addItem(supplier[0])
            conn.close()
        except Exception as e:
            print(f"خطا در بارگذاری لیست شرکت‌ها: {e}")

    def add_invoice_item_row(self):
        try:
            row = len(self.invoice_items_data) - 1
            self.open_add_drug_to_invoice_dialog(row, 0)
        except Exception as e:
            import traceback
            print(f"خطا در افزودن ردیف جدید: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "خطا", f"خطا در افزودن ردیف جدید: {e}")

    def edit_selected_invoice_item_row(self):
        try:
            selected_rows = self.items_table.selectionModel().selectedRows()
            if selected_rows:
                row = selected_rows[0].row()
                if 0 <= row < len(self.invoice_items_data):
                    self.open_add_drug_to_invoice_dialog(row, 0)
                else:
                    QMessageBox.warning(self, "خطا", "ردیف انتخابی نامعتبر است.")
            else:
                QMessageBox.information(self, "انتخاب نشده", "لطفاً یک ردیف را برای ویرایش انتخاب کنید.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ویرایش ردیف: {e}")

    def delete_selected_invoice_item_row(self):
        try:
            selected_rows = self.items_table.selectionModel().selectedRows()
            if selected_rows:
                row = selected_rows[0].row()
                if 0 <= row < len(self.invoice_items_data):
                    if len(self.invoice_items_data) > 1:
                        del self.invoice_items_data[row]
                        self._update_items_table()
                        self.calculate_document_summary()
                    else:
                        QMessageBox.warning(self, "خطا", "آخرین ردیف را نمی‌توان حذف کرد.")
                else:
                    QMessageBox.warning(self, "خطا", "ردیف انتخابی نامعتبر است.")
            else:
                QMessageBox.information(self, "انتخاب نشده", "لطفاً یک ردیف را برای حذف انتخاب کنید.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در حذف ردیف: {e}")

    def open_add_drug_to_invoice_dialog(self, row, column):
        try:
            if not (0 <= row < len(self.invoice_items_data)):
                print(f"خطا: شاخص ردیف نامعتبر است - row={row}, total rows={len(self.invoice_items_data)}")
                return
            current_item_data = self.invoice_items_data[row]
            dialog = AddDrugToInvoiceDialog(self, current_item_data, row_index_in_invoice=row)
            if dialog.exec():
                updated_item_data = dialog.get_data()
                if updated_item_data:
                    self.invoice_items_data[row] = updated_item_data
                    if row == len(self.invoice_items_data) - 1 and updated_item_data.get("generic_code"):
                        empty_item_template = {
                            "generic_code": "", "brand_code": "", "drug_name_snapshot": "", "quantity_in_package": 1,
                            "package_count": 1, "unit_count": 0, "expiry_date_gregorian": "", "expiry_date_jalali": "",
                            "purchase_price_per_package": 0, "profit_percentage": 0, "sale_price_per_package": 0,
                            "item_vat": 9, "item_discount_rial": 0, "batch_number": "",
                            "main_warehouse_location": "", "main_warehouse_min_stock": 0, "main_warehouse_max_stock": 0,
                            "main_shelf_location": "", "main_shelf_min_stock": 0, "main_shelf_max_stock": 0,
                        }
                        self.invoice_items_data.append(empty_item_template)
                    self._update_items_table()
                    self.calculate_document_summary()
        except Exception as e:
            import traceback
            error_message = f"خطا در باز کردن دیالوگ افزودن دارو: {str(e)}\n{traceback.format_exc()}"
            print(error_message)
            QMessageBox.critical(self, "خطا", f"مشکلی در باز کردن پنجره افزودن دارو رخ داد: {str(e)}")

    def _update_items_table(self):
        try:
            self.items_table.setRowCount(0)
            for i, item in enumerate(self.invoice_items_data):
                if not item:
                    continue
                self.items_table.insertRow(i)
                generic_code = item.get('generic_code', '')
                if generic_code:
                    self.items_table.setItem(i, 0, QTableWidgetItem(generic_code))
                    self.items_table.setItem(i, 1, QTableWidgetItem(item.get('drug_name_snapshot', '')))
                    self.items_table.setItem(i, 2, QTableWidgetItem(item.get('form', '')))
                    self.items_table.setItem(i, 3, QTableWidgetItem(item.get('dosage', '')))
                    self.items_table.setItem(i, 4, QTableWidgetItem(str(item.get('package_count', 0))))
                    purchase_price = item.get('purchase_price_per_package', 0)
                    self.items_table.setItem(i, 5, QTableWidgetItem(f"{purchase_price:,}"))
                    sale_price = item.get('sale_price_per_package', 0)
                    self.items_table.setItem(i, 6, QTableWidgetItem(f"{sale_price:,}"))
                    total_price = purchase_price * item.get('package_count', 0)
                    self.items_table.setItem(i, 7, QTableWidgetItem(f"{total_price:,}"))
        except Exception as e:
            print(f"خطا در به‌روزرسانی جدول اقلام فاکتور: {e}")

    def calculate_document_summary(self):
        try:
            total_purchase_price = 0
            total_sale_price = 0
            for item in self.invoice_items_data:
                if item.get('generic_code'):
                    package_count = item.get('package_count', 0)
                    purchase_price = item.get('purchase_price_per_package', 0)
                    sale_price = item.get('sale_price_per_package', 0)
                    total_purchase_price += package_count * purchase_price
                    total_sale_price += package_count * sale_price
            self.total_purchase_price_label.setText(f"{total_purchase_price:,} ریال")
            self.total_sale_price_label.setText(f"{total_sale_price:,} ریال")
            try:
                discount_percent = float(self.overall_discount_percent_edit.text() or "0")
                discount_rial = int(self.overall_discount_rial_edit.text() or "0")
                tax_percent = float(self.total_tax_edit.text() or "0")
                shipping_cost = int(self.shipping_cost_edit.text() or "0")
            except ValueError:
                discount_percent = 0
                discount_rial = 0
                tax_percent = 0
                shipping_cost = 0
            discount_from_percent = (total_purchase_price * discount_percent) / 100
            tax_amount = (total_purchase_price * tax_percent) / 100
            payable_amount = total_purchase_price - discount_from_percent - discount_rial + tax_amount + shipping_cost
            if payable_amount < 0:
                payable_amount = 0
            self.payable_amount_label.setText(f"{payable_amount:,} ریال")
        except Exception as e:
            print(f"خطا در محاسبه خلاصه سند: {e}")

    def save_document(self):
        # --- 1. اعتبارسنجی داده‌های هدر سند ---
        if self.supplier_combo.currentIndex() == 0 or self.supplier_combo.currentText() == "انتخاب کنید**":
            QMessageBox.warning(self, "خطای ورودی", "لطفاً 'طرف انبار (تأمین کننده)' را انتخاب کنید.")
            self.supplier_combo.setFocus()
            return
        
        invoice_number = self.invoice_num_edit.text().strip()
        if not invoice_number:
            QMessageBox.warning(self, "خطای ورودی", "لطفاً 'شماره فاکتور' را وارد کنید.")
            self.invoice_num_edit.setFocus()
            return

        # بررسی اینکه حداقل یک آیتم دارو با کد ژنریک معتبر در لیست وجود دارد
        valid_invoice_items = [
            item for item in self.invoice_items_data 
            if item.get('generic_code') and item.get('package_count', 0) > 0
        ]
        if not valid_invoice_items:
            QMessageBox.warning(self, "خطای ورودی", "حداقل یک قلم دارو با کد ژنریک و تعداد معتبر باید در فاکتور وجود داشته باشد.")
            return

        # --- 2. جمع‌آوری داده‌های هدر سند از UI ---
        doc_type = self.doc_type_combo.currentText()
        reg_date = self.reg_date_edit.date().toString("yyyy/MM/dd")
        supplier_name = self.supplier_combo.currentText()
        description = self.description_edit.text().strip()
        apply_to_shelf_directly = 1 if self.apply_direct_checkbox.isChecked() else 0
        
        invoice_type = self.invoice_type_combo.currentText()
        invoice_date = self.invoice_date_edit.date().toString("yyyy/MM/dd")
        try:
            settlement_period_days = int(self.settlement_days_edit.text() or "0")
        except ValueError:
            settlement_period_days = 0
        settlement_date = self.settlement_date_edit.date().toString("yyyy/MM/dd")

        # خواندن مقادیر عددی از لیبل‌های بخش محاسبات نهایی
        # این بخش نیاز به دقت دارد چون لیبل‌ها شامل " ریال" و جداکننده هزارگان هستند
        # بهتر است مقادیر خام عددی در self نگهداری شوند یا از calculate_document_summary بازیابی شوند.
        # برای سادگی فعلی، فرض می‌کنیم این مقادیر به نحوی در دسترس هستند یا از self.invoice_items_data محاسبه می‌شوند.
        
        total_items_purchase_price_val = 0
        total_items_sale_price_val = 0
        for item in valid_invoice_items:
            total_items_purchase_price_val += item.get('purchase_price_per_package', 0) * item.get('package_count', 0)
            # قیمت فروش ممکن است در این مرحله هنوز به طور دقیق برای همه آیتم‌ها محاسبه نشده باشد
            # یا باید از `sale_price_per_package` در `item` خوانده شود.
            total_items_sale_price_val += item.get('sale_price_per_package', 0) * item.get('package_count', 0)

        try:
            # مقادیر تخفیف، مالیات و هزینه حمل از فیلدهای ورودی خوانده می‌شوند
            overall_doc_discount_percent = float(self.overall_discount_percent_edit.text() or "0")
            overall_doc_discount_rial = float(self.overall_discount_rial_edit.text().replace(',', '') or "0")
            
            # محاسبه تخفیف کلی بر اساس درصد اگر تخفیف ریالی وارد نشده باشد
            # این منطق باید با calculate_document_summary هماهنگ باشد
            final_overall_discount = overall_doc_discount_rial
            if overall_doc_discount_percent > 0 and overall_doc_discount_rial == 0:
                 final_overall_discount = (total_items_purchase_price_val * overall_doc_discount_percent) / 100
            
            # مالیات و عوارض کلی (این می‌تواند به عنوان document_tax_levies یا items_tax_levies تفسیر شود)
            # فعلا فرض می‌کنیم این مالیات کلی سند است.
            total_tax_percent = float(self.total_tax_edit.text() or "0")
            document_total_tax_amount = (total_items_purchase_price_val * total_tax_percent) / 100 # مثال

            shipping_cost_val = float(self.shipping_cost_edit.text().replace(',', '') or "0")
            
            # محاسبه مبلغ قابل پرداخت نهایی (باید با calculate_document_summary هماهنگ باشد)
            payable_amount_val = (total_items_purchase_price_val - 
                                 final_overall_discount + 
                                 document_total_tax_amount + # یا مجموع مالیات آیتم‌ها
                                 shipping_cost_val)
            if payable_amount_val < 0: payable_amount_val = 0

        except ValueError:
            QMessageBox.critical(self, "خطای مقادیر عددی", "لطفاً مقادیر عددی مربوط به تخفیف، مالیات و هزینه حمل را به درستی وارد کنید.")
            return

        # --- 3. تایید نهایی از کاربر ---
        reply = QMessageBox.question(self, "تأیید ثبت سند", 
                                     f"آیا از ثبت سند خرید فاکتور شماره {invoice_number} اطمینان دارید؟\n"
                                     f"مبلغ قابل پرداخت: {payable_amount_val:,.0f} ریال",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.No:
            return

        # --- 4. عملیات ذخیره‌سازی در دیتابیس ---
        conn = None
        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            conn.execute("BEGIN TRANSACTION") # شروع تراکنش

            # --- 4.1. ذخیره در جدول company_purchases ---
            cursor.execute("""
                INSERT INTO company_purchases (
                    document_row_number, registration_date, document_type, supplier_name, 
                    description, apply_to_shelf_directly, invoice_type, invoice_number, 
                    invoice_date, settlement_period_days, settlement_date, 
                    total_items_purchase_price, total_items_sale_price, 
                    overall_document_discount, document_product_discount, 
                    document_tax_levies, items_tax_levies, shipping_cost, payable_amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                None, # document_row_number - اگر مقدار خاصی دارد باید تولید شود، فعلا None میگذاریم یا از ID استفاده میکنیم
                reg_date, doc_type, supplier_name, description, apply_to_shelf_directly,
                invoice_type, invoice_number, invoice_date, settlement_period_days, settlement_date,
                total_items_purchase_price_val,
                total_items_sale_price_val, # این مقدار باید دقیق محاسبه شود
                final_overall_discount, # تخفیف کلی سند
                0, # document_product_discount - فعلا صفر، مجموع تخفیف آیتم‌ها می‌تواند باشد
                document_total_tax_amount, # document_tax_levies - مالیات کلی سند
                sum(item.get('item_vat', 0) * item.get('purchase_price_per_package',0) * item.get('package_count',0) / 100 for item in valid_invoice_items), # items_tax_levies - مجموع مالیات آیتم‌ها
                shipping_cost_val,
                payable_amount_val
            ))
            purchase_document_id = cursor.lastrowid

            # --- 4.2. ذخیره در جدول company_purchase_items ---
            for item_data in valid_invoice_items:
                cursor.execute("""
                    INSERT INTO company_purchase_items (
                        purchase_document_id, generic_code, brand_code, drug_name_snapshot,
                        quantity_in_package, package_count, unit_count,
                        expiry_date_gregorian, expiry_date_jalali, batch_number,
                        purchase_price_per_package, profit_percentage, sale_price_per_package,
                        item_vat, item_discount_rial,
                        main_warehouse_location, main_warehouse_min_stock, main_warehouse_max_stock,
                        main_shelf_location, main_shelf_min_stock, main_shelf_max_stock
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    purchase_document_id,
                    item_data.get('generic_code'),
                    item_data.get('brand_code', item_data.get('generic_code')), # اگر brand_code جدا نیست
                    item_data.get('drug_name_snapshot'),
                    item_data.get('quantity_in_package', 1),
                    item_data.get('package_count', 0),
                    item_data.get('unit_count', item_data.get('package_count', 0) * item_data.get('quantity_in_package', 1)),
                    item_data.get('expiry_date_gregorian'), # <--- ذخیره تاریخ انقضا میلادی
                    item_data.get('expiry_date_jalali'),   # <--- ذخیره تاریخ انقضا شمسی
                    item_data.get('batch_number'),         # <--- ذخیره شماره بچ
                    item_data.get('purchase_price_per_package', 0),
                    item_data.get('profit_percentage', 0), # این باید دقیق محاسبه شود
                    item_data.get('sale_price_per_package', 0), # این باید دقیق محاسبه شود
                    item_data.get('item_vat', 0),
                    item_data.get('item_discount_rial', 0),
                    item_data.get('main_warehouse_location', ""),
                    item_data.get('main_warehouse_min_stock', 0),
                    item_data.get('main_warehouse_max_stock', 0),
                    item_data.get('main_shelf_location', ""),
                    item_data.get('main_shelf_min_stock', 0),
                    item_data.get('main_shelf_max_stock', 0)
                ))
                
             # --- 4.3. به‌روزرسانی موجودی انبار اصلی (drugs.stock) ---
                # موجودی کلی در جدول drugs با هر خرید افزایش می‌یابد.
                # این مهم است که drugs.stock همیشه با مجموع موجودی بچ‌ها همگام باشد.
                total_units_added = item_data.get('package_count', 0) * item_data.get('quantity_in_package', 1)
                
                # ابتدا بررسی می‌کنیم که آیا دارویی با این generic_code در جدول drugs وجود دارد یا خیر
                cursor.execute("SELECT id FROM drugs WHERE generic_code = ?", (item_data.get('generic_code'),))
                drug_exists = cursor.fetchone()

                if drug_exists:
                    # اگر دارو وجود دارد، موجودی آن را به‌روزرسانی می‌کنیم.
                    cursor.execute("UPDATE drugs SET stock = stock + ? WHERE generic_code = ?",
                                   (total_units_added, item_data.get('generic_code')))
                    print(f"--- DEBUG: Updated stock for {item_data.get('generic_code')} by {total_units_added}. New total: stock + {total_units_added}")
                else:
                    # اگر دارو با این generic_code در جدول drugs وجود ندارد، یک پیام هشدار می‌دهیم.
                    # این حالت نباید رخ دهد اگر تمام داروها ابتدا از طریق AddDrugSimpleDialog یا TtakUpdateDialog ثبت شده باشند.
                    QMessageBox.warning(self, "خطای موجودی", f"داروی '{item_data.get('drug_name_snapshot')}' با کد ژنریک '{item_data.get('generic_code')}' در جدول اصلی داروها (drugs) یافت نشد. موجودی آن آپدیت نشد.")
                    print(f"--- WARNING: Drug {item_data.get('generic_code')} not found in 'drugs' table. Stock not updated. ---")

                # اگر apply_to_shelf_directly تیک خورده باشد، می‌توانید منطق مربوط به موجودی قفسه را هم اینجا اضافه کنید.
                # (در حال حاضر، فیلدهای مربوط به main_shelf_location/min/max در company_purchase_items ذخیره می‌شوند
                # اما منطق عملیاتی برای آپدیت موجودی قفسه در drugs.stock وجود ندارد و باید تعریف شود.)


            conn.commit() # نهایی کردن تراکنش
            QMessageBox.information(self, "ثبت موفق", f"سند خرید فاکتور شماره {invoice_number} با موفقیت ثبت شد.")
            self.accept() # بستن دیالوگ در صورت موفقیت

        except sqlite3.IntegrityError as ie:
            if conn: conn.rollback()
            if "UNIQUE constraint failed: company_purchases.invoice_number" in str(ie):
                 QMessageBox.critical(self, "خطای یکتایی", f"فاکتوری با شماره '{invoice_number}' قبلاً در سیستم ثبت شده است.")
                 self.invoice_num_edit.setFocus()
            else:
                 QMessageBox.critical(self, "خطای یکتایی دیتابیس", f"خطا در ثبت سند (احتمالا کد تکراری): {ie}")
        except sqlite3.Error as e:
            if conn: conn.rollback() # بازگرداندن تغییرات در صورت بروز خطا
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در هنگام ذخیره سند خرید: {e}")
        except Exception as ex:
            if conn: conn.rollback()
            QMessageBox.critical(self, "خطای ناشناخته", f"یک خطای پیش‌بینی نشده رخ داد: {ex}")
        finally:
            if conn:
                conn.close()