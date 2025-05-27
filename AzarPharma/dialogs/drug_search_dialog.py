# ui/dialogs/drug_search_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QLabel, QComboBox,
                             QAbstractItemView) # QAbstractItemView اضافه شد برای setSelectionBehavior
from PyQt6.QtCore import Qt, QTimer, pyqtSignal # pyqtSignal اضافه شد
from PyQt6.QtGui import QFont
import sqlite3
import os

try:
    from config import DB_PATH
    from database.db import get_connection
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')
    def get_connection(db_path_param):
        conn = sqlite3.connect(db_path_param, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row # اضافه کردن این خط برای دسترسی به ستون‌ها با نام
        return conn

class DrugSearchDialog(QDialog):
    # یک سیگنال برای ارسال اطلاعات داروی انتخاب شده، به جای استفاده از متد get_selected_drug
    # این باعث می‌شود که بتوانیم بلافاصله پس از انتخاب، اطلاعات را به پنجره اصلی بفرستیم
    drug_selected_signal = pyqtSignal(dict) #

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 جستجوی دارو")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        self._selected_drug_info = None # متغیری برای نگهداری اطلاعات داروی انتخاب شده

        # تایمر برای بارکد اسکنر
        self.barcode_timer = QTimer()
        self.barcode_timer.setSingleShot(True)
        self.barcode_timer.timeout.connect(self.process_barcode_search)
        self.barcode_buffer = ""

        self.setup_ui()
        self.load_all_drugs()

    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)

        # عنوان
        title_label = QLabel("🔍 جستجوی دارو")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)

        # بخش جستجو
        search_layout = QHBoxLayout()

        # نوع جستجو
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems([
            "نام ژنریک",
            "نام تجاری",
            "کد ژنریک",
            "بارکد",
            "همه موارد"
        ])
        self.search_type_combo.setMinimumWidth(120)
        search_layout.addWidget(QLabel("نوع جستجو:"))
        search_layout.addWidget(self.search_type_combo)

        # فیلد جستجو
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("متن جستجو یا اسکن بارکد...")
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        self.search_edit.returnPressed.connect(self.search_drugs) # با زدن Enter جستجو انجام شود
        search_layout.addWidget(self.search_edit)

        # دکمه جستجو
        search_btn = QPushButton("🔍 جستجو")
        search_btn.clicked.connect(self.search_drugs)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        search_layout.addWidget(search_btn)

        # دکمه ریست
        reset_btn = QPushButton("🔄 ریست")
        reset_btn.clicked.connect(self.reset_search)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        search_layout.addWidget(reset_btn)

        layout.addLayout(search_layout)

        # وضعیت جستجو
        self.status_label = QLabel("📋 نمایش همه داروها")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin: 5px;")
        layout.addWidget(self.status_label)

        # جدول نتایج
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        # تنظیم ستون‌ها
        headers = ["شناسه", "نام ژنریک", "نام تجاری", "کد ژنریک", "فرم", "دوز", "قیمت", "موجودی", "بارکد"]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)

        # تنظیم عرض ستون‌ها
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # شناسه
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # نام ژنریک
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # نام تجاری
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # کد ژنریک
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # فرم
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # دوز
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # قیمت
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # موجودی
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # بارکد

        # مخفی کردن ستون ID اگر لازم نیست مستقیماً نمایش داده شود
        self.results_table.setColumnHidden(0, True) # ستون ID را مخفی می‌کنیم

        self.results_table.doubleClicked.connect(self.on_table_double_clicked) # اتصال دابل کلیک
        layout.addWidget(self.results_table)

        # دکمه‌های پایین
        bottom_layout = QHBoxLayout()

        select_btn = QPushButton("✅ انتخاب")
        select_btn.clicked.connect(self.select_drug)
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)

        close_btn = QPushButton("❌ بستن")
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        bottom_layout.addStretch()
        bottom_layout.addWidget(select_btn)
        bottom_layout.addWidget(close_btn)
        layout.addLayout(bottom_layout)

    def on_search_text_changed(self, text):
        """مدیریت تغییر متن جستجو برای تشخیص بارکد اسکنر"""
        self.barcode_buffer = text
        self.barcode_timer.start(100)  # تاخیر 100 میلی‌ثانیه

    def process_barcode_search(self):
        """پردازش جستجوی بارکد از اسکنر"""
        search_text = self.barcode_buffer.strip()
        # بارکدهای معمولی حداقل 6 رقم دارند یا طول بیشتری دارند.
        # می‌توانید منطق دقیق‌تری برای تشخیص بارکد (مثلاً با regex) اضافه کنید.
        if search_text and len(search_text) >= 6:
            # احتمالاً بارکد است، تنظیم نوع جستجو روی بارکد
            self.search_type_combo.setCurrentText("بارکد")
            self.status_label.setText(f"🔍 جستجوی بارکد: {search_text}")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 11px; margin: 5px; font-weight: bold;")
            # جستجوی خودکار
            self.search_drugs()
        else:
            # اگر متن کوتاه است، احتمالا کاربر در حال تایپ دستی است، وضعیت را به حالت عادی برگردان
            if not search_text:
                 self.status_label.setText("📋 نمایش همه داروها")
                 self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin: 5px;")
                 self.load_all_drugs()
            else:
                 self.status_label.setText(f"تایپ دستی: {search_text}")
                 self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin: 5px;")


    def search_drugs(self):
        """جستجوی داروها"""
        search_text = self.search_edit.text().strip()
        search_type = self.search_type_combo.currentText()

        # اگر متن جستجو خالی بود، همه داروها را بارگذاری کن
        if not search_text:
            self.load_all_drugs()
            return

        conn = None
        try:
            conn = get_connection(DB_PATH) #
            cursor = conn.cursor()

            # بررسی وجود ستون barcode (این منطق قبلا در db_manager بود، اینجا برای اطمینان مجدد بررسی می‌شود)
            # و همچنین drug_id را از جدول drugs SELECT می‌کنیم
            cursor.execute("PRAGMA table_info(drugs)")
            columns_info = cursor.fetchall()
            column_names = [col_info[1] for col_info in columns_info]
            has_barcode = 'barcode' in column_names

            query_parts = []
            params = []

            # ساخت کوئری بر اساس نوع جستجو
            base_select_query = """
                SELECT id, generic_name, en_brand_name, generic_code, form, dosage, price_per_unit, stock, barcode
                FROM drugs
            """

            if search_type == "نام ژنریک":
                query_parts.append("generic_name LIKE ?")
                params.append(f"%{search_text}%")
            elif search_type == "نام تجاری":
                query_parts.append("en_brand_name LIKE ?")
                params.append(f"%{search_text}%")
            elif search_type == "کد ژنریک":
                query_parts.append("generic_code LIKE ?")
                params.append(f"%{search_text}%")
            elif search_type == "بارکد" and has_barcode:
                query_parts.append("barcode LIKE ?")
                params.append(f"%{search_text}%")
            elif search_type == "همه موارد":
                query_parts.append("generic_name LIKE ?")
                params.append(f"%{search_text}%")
                query_parts.append("en_brand_name LIKE ?")
                params.append(f"%{search_text}%")
                query_parts.append("generic_code LIKE ?")
                params.append(f"%{search_text}%")
                if has_barcode:
                    query_parts.append("barcode LIKE ?")
                    params.append(f"%{search_text}%")
            else: # اگر نوع جستجو بارکد انتخاب شد اما ستون barcode نبود
                if search_type == "بارکد":
                    QMessageBox.warning(self, "خطا", "ستون بارکد در دیتابیس یافت نشد. لطفا ابتدا دیتابیس را آپدیت کنید.")
                    return


            final_query = base_select_query
            if query_parts:
                final_query += " WHERE " + " OR ".join(query_parts)
            final_query += " ORDER BY generic_name"


            cursor.execute(final_query, params)
            results = cursor.fetchall()

            self.populate_table(results)

            result_count = len(results)
            self.status_label.setText(f"📊 {result_count} دارو پیدا شد")
            self.status_label.setStyleSheet("color: #2c3e50; font-size: 11px; margin: 5px;")

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در جستجو: {e}")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در جستجو: {e}")
        finally:
            if conn:
                conn.close()

    def load_all_drugs(self):
        """بارگذاری همه داروها"""
        conn = None
        try:
            conn = get_connection(DB_PATH) #
            cursor = conn.cursor()

            # بررسی وجود ستون barcode (این منطق قبلا در db_manager بود، اینجا برای اطمینان مجدد بررسی می‌شود)
            cursor.execute("PRAGMA table_info(drugs)")
            columns_info = cursor.fetchall()
            column_names = [col_info[1] for col_info in columns_info]
            has_barcode = 'barcode' in column_names

            # انتخاب همه ستون‌هایی که برای نمایش و مدل Drug نیاز داریم
            select_columns = "id, generic_name, en_brand_name, generic_code, form, dosage, price_per_unit, stock"
            if has_barcode:
                select_columns += ", barcode"
            else:
                select_columns += ", '' AS barcode" # یک ستون خالی برای بارکد اگر وجود ندارد

            query = f"SELECT {select_columns} FROM drugs ORDER BY generic_name"
            cursor.execute(query)
            drugs = cursor.fetchall()

            self.populate_table(drugs)

            self.status_label.setText(f"📋 نمایش همه داروها ({len(drugs)} دارو)")
            self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin: 5px;")

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در بارگذاری داروها: {e}")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری داروها: {e}")
        finally:
            if conn:
                conn.close()

    def populate_table(self, drugs):
        """پر کردن جدول با داده‌های داروها"""
        self.results_table.setRowCount(len(drugs))

        for row, drug_row_data in enumerate(drugs):
            # drug_row_data اینجا یک شیء sqlite3.Row است چون row_factory تنظیم شده است
            # دسترسی به مقادیر با نام ستون‌ها راحت‌تر و خواناتر است
            drug_info = {
                'id': drug_row_data['id'],
                'generic_name': drug_row_data['generic_name'],
                'en_brand_name': drug_row_data['en_brand_name'],
                'generic_code': drug_row_data['generic_code'],
                'form': drug_row_data['form'],
                'dosage': drug_row_data['dosage'],
                'price_per_unit': drug_row_data['price_per_unit'],
                'stock': drug_row_data['stock'],
                'barcode': drug_row_data['barcode'] if 'barcode' in drug_row_data.keys() else ''
            }
            # هر ردیف را به عنوان UserRole ذخیره می‌کنیم
            self.results_table.setItem(row, 0, QTableWidgetItem(str(drug_info['id'])))
            self.results_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, drug_info) # ذخیره کل دیکشنری

            self.results_table.setItem(row, 1, QTableWidgetItem(drug_info['generic_name'] or ""))
            self.results_table.setItem(row, 2, QTableWidgetItem(drug_info['en_brand_name'] or ""))
            self.results_table.setItem(row, 3, QTableWidgetItem(drug_info['generic_code'] or ""))
            self.results_table.setItem(row, 4, QTableWidgetItem(drug_info['form'] or ""))
            self.results_table.setItem(row, 5, QTableWidgetItem(drug_info['dosage'] or ""))
            self.results_table.setItem(row, 6, QTableWidgetItem(f"{drug_info['price_per_unit']:,}" if drug_info['price_per_unit'] is not None else "0"))
            self.results_table.setItem(row, 7, QTableWidgetItem(str(drug_info['stock'] or "0")))
            self.results_table.setItem(row, 8, QTableWidgetItem(drug_info['barcode'] or ""))

    def reset_search(self):
        """ریست کردن جستجو"""
        self.search_edit.clear()
        self.search_type_combo.setCurrentIndex(0)
        self.load_all_drugs()

    def on_table_double_clicked(self, index):
        """وقتی روی جدل دو بار کلیک می‌شود، دارو انتخاب و دیالوگ پذیرفته می‌شود."""
        row = index.row()
        selected_item_data = self.results_table.item(row, 0).data(Qt.ItemDataRole.UserRole) #
        if selected_item_data:
            self._selected_drug_info = selected_item_data
            self.drug_selected_signal.emit(self._selected_drug_info) # ارسال سیگنال
            self.accept() # بستن دیالوگ

    def select_drug(self):
        """انتخاب دارو با دکمه 'انتخاب'"""
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            selected_item_data = self.results_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole) #
            if selected_item_data:
                self._selected_drug_info = selected_item_data
                self.drug_selected_signal.emit(self._selected_drug_info) # ارسال سیگنال
                self.accept() # بستن دیالوگ
            else:
                QMessageBox.warning(self, "خطا", "اطلاعات دارو انتخاب شده نامعتبر است.")
        else:
            QMessageBox.warning(self, "خطا", "لطفاً ابتدا یک دارو انتخاب کنید.")

    def get_selected_drug(self):
        """
        این متد برای سازگاری با کدهای موجود نگهداری می‌شود،
        اما توصیه می‌شود از سیگنال drug_selected_signal استفاده کنید.
        """
        return self._selected_drug_info