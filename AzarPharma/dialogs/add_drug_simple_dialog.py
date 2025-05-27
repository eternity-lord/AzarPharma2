# ui/dialogs/add_drug_simple_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QHBoxLayout, QMessageBox, QLabel, QFrame)
from PyQt6.QtGui import QIntValidator, QFont
from PyQt6.QtCore import Qt, QTimer

import sqlite3
import os

# تعریف DB_PATH و get_connection
try:
    from config import DB_PATH
    from database.db import get_connection
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')
    def get_connection(db_path_param):
        db_dir = os.path.dirname(db_path_param)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(db_path_param, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

class AddDrugSimpleDialog(QDialog):
    def __init__(self, parent=None, drug_data=None):
        super().__init__(parent)
        self.setWindowTitle("افزودن/ویرایش دارو")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self.drug_data_original = drug_data
        self.is_edit_mode = self.drug_data_original is not None
        
        # تایمر برای تشخیص ورودی از بارکد اسکنر
        self.barcode_timer = QTimer()
        self.barcode_timer.setSingleShot(True)
        self.barcode_timer.timeout.connect(self.process_barcode_input)
        self.barcode_buffer = ""
        
        self.setup_ui()
        
        if self.is_edit_mode and self.drug_data_original:
            self.load_existing_data()

    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        compact_font = QFont()
        compact_font.setPointSize(10)

        main_layout = QVBoxLayout(self)
        
        # عنوان
        title_label = QLabel("📦 افزودن دارو جدید" if not self.is_edit_mode else "✏️ ویرایش دارو")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title_label)

        # فرم
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setVerticalSpacing(8)
        form.setHorizontalSpacing(10)

        # فیلدهای اصلی
        self.generic_name_edit = QLineEdit()
        self.generic_name_edit.setFont(compact_font)
        self.generic_name_edit.setPlaceholderText("نام ژنریک دارو...")

        self.en_brand_name_edit = QLineEdit()
        self.en_brand_name_edit.setFont(compact_font)
        self.en_brand_name_edit.setPlaceholderText("نام تجاری...")

        self.form_edit = QLineEdit()
        self.form_edit.setFont(compact_font)
        self.form_edit.setPlaceholderText("قرص، کپسول، شربت...")

        self.dosage_edit = QLineEdit()
        self.dosage_edit.setFont(compact_font)
        self.dosage_edit.setPlaceholderText("500mg, 250ml...")

        self.generic_code_edit = QLineEdit()
        self.generic_code_edit.setFont(compact_font)
        self.generic_code_edit.setPlaceholderText("کد ژنریک...")

        self.price_per_unit_edit = QLineEdit()
        self.price_per_unit_edit.setFont(compact_font)
        self.price_per_unit_edit.setValidator(QIntValidator(0, 999999999))
        self.price_per_unit_edit.setPlaceholderText("قیمت به ریال...")

        self.min_stock_alert_level_edit = QLineEdit()
        self.min_stock_alert_level_edit.setFont(compact_font)
        self.min_stock_alert_level_edit.setValidator(QIntValidator(0, 99999))
        self.min_stock_alert_level_edit.setPlaceholderText("سطح هشدار...")

        # فیلد بارکد با قابلیت دریافت از اسکنر
        self.barcode_edit = QLineEdit()
        self.barcode_edit.setFont(compact_font)
        self.barcode_edit.setPlaceholderText("بارکد (از اسکنر یا دستی)...")
        # اتصال رویداد تغییر متن برای تشخیص ورودی از اسکنر
        self.barcode_edit.textChanged.connect(self.on_barcode_text_changed)
        
        # لیبل وضعیت بارکد اسکنر
        self.barcode_status_label = QLabel("🔍 آماده دریافت بارکد از اسکنر")
        self.barcode_status_label.setStyleSheet("color: #27ae60; font-size: 10px;")

        # دکمه تست بارکد اسکنر
        test_barcode_btn = QPushButton("🧪 تست اسکنر")
        test_barcode_btn.setMaximumWidth(100)
        test_barcode_btn.clicked.connect(self.test_barcode_scanner)
        test_barcode_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        # لایه‌اوت بارکد
        barcode_layout = QHBoxLayout()
        barcode_layout.addWidget(self.barcode_edit)
        barcode_layout.addWidget(test_barcode_btn)

        # اضافه کردن فیلدها به فرم
        form.addRow(self._create_label("نام ژنریک*:", compact_font), self.generic_name_edit)
        form.addRow(self._create_label("نام تجاری*:", compact_font), self.en_brand_name_edit)
        form.addRow(self._create_label("شکل دارو:", compact_font), self.form_edit)
        form.addRow(self._create_label("دوز:", compact_font), self.dosage_edit)
        form.addRow(self._create_label("کد ژنریک*:", compact_font), self.generic_code_edit)
        form.addRow(self._create_label("قیمت واحد*:", compact_font), self.price_per_unit_edit)
        form.addRow(self._create_label("سطح هشدار موجودی:", compact_font), self.min_stock_alert_level_edit)
        form.addRow(self._create_label("بارکد:", compact_font), barcode_layout)
        form.addRow("", self.barcode_status_label)

        main_layout.addLayout(form)

        # دکمه‌های عملیات
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 ذخیره")
        self.save_btn.setFont(compact_font)
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_drug)
        self.save_btn.setStyleSheet("""
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
        
        self.cancel_btn = QPushButton("❌ انصراف")
        self.cancel_btn.setFont(compact_font)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
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

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(buttons_layout)

    def _create_label(self, text, font):
        """ایجاد برچسب با فونت مشخص"""
        label = QLabel(text)
        label.setFont(font)
        label.setStyleSheet("font-weight: bold; color: #34495e;")
        return label

    def on_barcode_text_changed(self, text):
        """مدیریت تغییر متن بارکد برای تشخیص ورودی از اسکنر"""
        # اگر متن به سرعت تغییر کند (مشخصه ورودی از اسکنر)
        self.barcode_buffer = text
        self.barcode_timer.start(100)  # 100 میلی‌ثانیه تاخیر

    def process_barcode_input(self):
        """پردازش ورودی بارکد از اسکنر"""
        barcode = self.barcode_buffer.strip()
        if barcode:
            # تشخیص اینکه ورودی از اسکنر بوده (معمولاً با Enter ختم می‌شود)
            if len(barcode) > 5:  # بارکدهای معمولی حداقل 6 رقم دارند
                self.barcode_status_label.setText(f"✅ بارکد دریافت شد: {barcode}")
                self.barcode_status_label.setStyleSheet("color: #27ae60; font-size: 10px; font-weight: bold;")
                
                # جستجوی خودکار دارو با این بارکد
                self.search_drug_by_barcode(barcode)
            else:
                self.barcode_status_label.setText("⚠️ بارکد نامعتبر")
                self.barcode_status_label.setStyleSheet("color: #e74c3c; font-size: 10px;")

    def search_drug_by_barcode(self, barcode):
        """جستجوی دارو با بارکد"""
        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM drugs WHERE barcode = ?", (barcode,))
            drug = cursor.fetchone()
            
            if drug:
                # دارو پیدا شد، نمایش اطلاعات
                QMessageBox.information(
                    self, 
                    "دارو پیدا شد", 
                    f"این بارکد متعلق به داروی موجود است:"
                    f"نام: {drug[1]}"
                    f"کد ژنریک: {drug[3]}"
                    f"آیا می‌خواهید اطلاعات آن را ویرایش کنید؟"
                )
            else:
                # دارو جدید
                self.barcode_status_label.setText("🆕 بارکد جدید - آماده ثبت دارو")
                self.barcode_status_label.setStyleSheet("color: #f39c12; font-size: 10px; font-weight: bold;")
            
            conn.close()
            
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در جستجوی بارکد: {e}")

    def test_barcode_scanner(self):
        """تست عملکرد بارکد اسکنر"""
        QMessageBox.information(
            self, 
            "تست بارکد اسکنر", 
            "🔍 برای تست اسکنر:"
            "1. روی فیلد بارکد کلیک کنید"
            "2. بارکدی را اسکن کنید"
            "3. اسکنر باید خودکار بارکد را وارد کند"
            "✅ اگر اسکنر کار می‌کند، بارکد در فیلد ظاهر می‌شود"
        )
        self.barcode_edit.setFocus()

    def load_existing_data(self):
        """بارگذاری داده‌های موجود در حالت ویرایش"""
        data = self.drug_data_original
        self.generic_name_edit.setText(data.get("generic_name", ""))
        self.en_brand_name_edit.setText(data.get("en_brand_name", ""))
        self.form_edit.setText(data.get("form", ""))
        self.dosage_edit.setText(data.get("dosage", ""))
        self.generic_code_edit.setText(data.get("generic_code", ""))
        self.price_per_unit_edit.setText(str(data.get("price_per_unit", "0")))
        self.min_stock_alert_level_edit.setText(str(data.get("min_stock_alert_level", "0")))
        self.barcode_edit.setText(data.get("barcode", ""))
        
        if data.get("generic_code"):
            self.generic_code_edit.setReadOnly(True)

    def save_drug(self):
        """ذخیره کردن دارو"""
        gname = self.generic_name_edit.text().strip()
        enbrand = self.en_brand_name_edit.text().strip()
        drug_form = self.form_edit.text().strip()
        dosage = self.dosage_edit.text().strip()
        gcode = self.generic_code_edit.text().strip()
        barcode = self.barcode_edit.text().strip()
        
        try:
            ppu_str = self.price_per_unit_edit.text().strip()
            ppu = int(ppu_str) if ppu_str else 0
            
            min_stock_str = self.min_stock_alert_level_edit.text().strip()
            min_stock_alert = int(min_stock_str) if min_stock_str else 0

            if not (gname and gcode and enbrand):
                QMessageBox.warning(self, "خطا", "نام ژنریک، نام تجاری و کد ژنریک الزامی هستند.")
                return
            
            conn = None
            try:
                conn = get_connection(DB_PATH)
                cursor = conn.cursor()
                
                # بررسی وجود ستون barcode
                cursor.execute("PRAGMA table_info(drugs)")
                columns = [column[1] for column in cursor.fetchall()]
                has_barcode = 'barcode' in columns
                
                if not self.is_edit_mode:
                    # بررسی تکراری نبودن کد ژنریک
                    cursor.execute("SELECT id FROM drugs WHERE generic_code = ?", (gcode,))
                    if cursor.fetchone():
                        QMessageBox.warning(self, "خطا", "این کد ژنریک قبلاً ثبت شده است!")
                        return
                    
                    # بررسی تکراری نبودن بارکد
                    if has_barcode and barcode:
                        cursor.execute("SELECT id FROM drugs WHERE barcode = ? AND barcode != ''", (barcode,))
                        if cursor.fetchone():
                            QMessageBox.warning(self, "خطا", "این بارکد قبلاً ثبت شده است!")
                            return
                    
                    # درج دارو جدید
                    if has_barcode:
                        cursor.execute(
                            """INSERT INTO drugs (generic_name, en_brand_name, generic_code, form, dosage, 
                                               price_per_unit, stock, min_stock_alert_level, barcode) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (gname, enbrand, gcode, drug_form, dosage, ppu, 0, min_stock_alert, barcode)
                        )
                    else:
                        cursor.execute(
                            """INSERT INTO drugs (generic_name, en_brand_name, generic_code, form, dosage, 
                                               price_per_unit, stock, min_stock_alert_level) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (gname, enbrand, gcode, drug_form, dosage, ppu, 0, min_stock_alert)
                        )
                    
                    QMessageBox.information(self, "ثبت موفق", f"داروی '{gname}' با موفقیت اضافه شد.")
                else:
                    # آپدیت دارو
                    if has_barcode:
                        cursor.execute(
                            """UPDATE drugs SET generic_name=?, en_brand_name=?, form=?, dosage=?, 
                                               price_per_unit=?, min_stock_alert_level=?, barcode=? 
                               WHERE generic_code=?""",
                            (gname, enbrand, drug_form, dosage, ppu, min_stock_alert, barcode, gcode)
                        )
                    else:
                        cursor.execute(
                            """UPDATE drugs SET generic_name=?, en_brand_name=?, form=?, dosage=?, 
                                               price_per_unit=?, min_stock_alert_level=? 
                               WHERE generic_code=?""",
                            (gname, enbrand, drug_form, dosage, ppu, min_stock_alert, gcode)
                        )
                    
                    QMessageBox.information(self, "به‌روزرسانی موفق", f"اطلاعات داروی '{gname}' به‌روزرسانی شد.")
                
                conn.commit()
                self.accept()
            
            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ثبت: {e}")
            finally:
                if conn:
                    conn.close()

        except ValueError:
            QMessageBox.warning(self, "خطای ورودی", "لطفاً مقادیر عددی را درست وارد کنید.")
        except Exception as ex:
            QMessageBox.critical(self, "خطای ناشناخته", f"خطا: {ex}")