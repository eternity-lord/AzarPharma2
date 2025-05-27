# dialogs/add_edit_doctor_dialog.py

import sqlite3
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QHBoxLayout, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

# به مسیر دهی DB_PATH توجه کنید. اگر از config.py استفاده می‌کنید، آن را import کنید.
# در غیر این صورت، مانند سایر دیالوگ‌ها مسیر را بسازید.
# در اینجا فرض بر ساخت مسیر مشابه سایر دیالوگ‌ها است.
try:
    from config import DB_PATH # تلاش برای ایمپورت از فایل کانفیگ مرکزی
except ImportError:
    # اگر فایل کانفیگ وجود نداشت یا ایمپورت نشد، مسیر را دستی بسازید
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')
    print(f"Warning: config.py not found or DB_PATH not in it. Using default DB_PATH: {DB_PATH}")


# بهتر است این تابع از database.db ایمپورت شود تا از تکرار کد جلوگیری شود.
# from database.db import get_connection
# اما برای اینکه این فایل به تنهایی قابل ارائه باشد، موقتا اینجا تعریف می‌کنیم.
def get_db_connection_local():
    """یک اتصال محلی به دیتابیس ایجاد می‌کند."""
    # اطمینان از وجود پوشه دیتابیس
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=10)


class AddEditDoctorDialog(QDialog):
    def __init__(self, parent=None, doctor_id: int = None):
        super().__init__(parent)
        self.doctor_id = doctor_id
        self.is_edit_mode = self.doctor_id is not None

        if self.is_edit_mode:
            self.setWindowTitle("ویرایش اطلاعات پزشک")
        else:
            self.setWindowTitle("افزودن پزشک جدید")
        
        self.setMinimumWidth(450) # کمی عرض بیشتر برای نمایش بهتر
        self._setup_ui()

        if self.is_edit_mode:
            self._load_doctor_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows) # برای نمایش بهتر در عرض کم
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight) # تراز کردن لیبل‌ها به راست

        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.medical_council_id_edit = QLineEdit()
        self.medical_council_id_edit.setPlaceholderText("الزامی")
        self.phone_number_edit = QLineEdit()
        self.phone_number_edit.setPlaceholderText("اختیاری")

        form_layout.addRow("نام:", self.first_name_edit)
        form_layout.addRow("نام خانوادگی:", self.last_name_edit)
        form_layout.addRow("شماره نظام پزشکی*:", self.medical_council_id_edit)
        form_layout.addRow("شماره تلفن:", self.phone_number_edit)
        
        if self.is_edit_mode:
            # در حالت ویرایش، معمولاً شماره نظام پزشکی (که شناسه یکتا است) تغییر داده نمی‌شود.
            self.medical_council_id_edit.setReadOnly(True)

        layout.addLayout(form_layout)

        # خط جداکننده
        line = QPushButton(self) # استفاده از دکمه به عنوان خط افقی برای سادگی
        line.setFixedHeight(1)
        line.setEnabled(False) # غیرفعال کردن دکمه
        layout.addWidget(line)

        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("ذخیره")
        self.save_button.setDefault(True) # دکمه پیش‌فرض با زدن Enter
        self.save_button.clicked.connect(self.save_doctor)
        
        self.cancel_button = QPushButton("انصراف")
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

    def _load_doctor_data(self):
        conn = None
        try:
            conn = get_db_connection_local()
            cursor = conn.cursor()
            cursor.execute("SELECT first_name, last_name, medical_council_id, phone_number FROM doctors WHERE id = ?", (self.doctor_id,))
            doctor_data = cursor.fetchone()
            
            if doctor_data:
                self.first_name_edit.setText(doctor_data[0] or "")
                self.last_name_edit.setText(doctor_data[1] or "")
                self.medical_council_id_edit.setText(doctor_data[2] or "")
                self.phone_number_edit.setText(doctor_data[3] or "")
            else:
                QMessageBox.warning(self, "خطا", "اطلاعات پزشک برای ویرایش یافت نشد.")
                # اگر پزشک یافت نشد، دیالوگ بسته شود یا دکمه ذخیره غیرفعال شود
                self.save_button.setEnabled(False) 
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در بارگذاری اطلاعات پزشک: {e}")
            self.save_button.setEnabled(False)
        finally:
            if conn:
                conn.close()

    def save_doctor(self):
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        medical_council_id = self.medical_council_id_edit.text().strip()
        # اگر شماره تلفن خالی است، None ذخیره شود
        phone_number = self.phone_number_edit.text().strip()
        if not phone_number:
            phone_number = None 

        if not first_name:
            QMessageBox.warning(self, "ورودی نامعتبر", "نام پزشک نمی‌تواند خالی باشد.")
            self.first_name_edit.setFocus()
            return
            
        if not last_name:
            QMessageBox.warning(self, "ورودی نامعتبر", "نام خانوادگی پزشک نمی‌تواند خالی باشد.")
            self.last_name_edit.setFocus()
            return

        if not medical_council_id:
            QMessageBox.warning(self, "ورودی نامعتبر", "شماره نظام پزشکی نمی‌تواند خالی باشد.")
            self.medical_council_id_edit.setFocus()
            return

        conn = None
        try:
            conn = get_db_connection_local()
            cursor = conn.cursor()

            if self.is_edit_mode:
                # چون شماره نظام پزشکی در حالت ویرایش ReadOnly است، نیازی به بررسی مجدد یکتایی آن نیست.
                cursor.execute("""
                    UPDATE doctors SET first_name = ?, last_name = ?, phone_number = ?
                    WHERE id = ?
                """, (first_name, last_name, phone_number, self.doctor_id))
                QMessageBox.information(self, "به‌روزرسانی موفق", "اطلاعات پزشک با موفقیت به‌روزرسانی شد.")
            else: # حالت افزودن پزشک جدید
                # بررسی یکتایی شماره نظام پزشکی قبل از افزودن
                cursor.execute("SELECT id FROM doctors WHERE medical_council_id = ?", (medical_council_id,))
                if cursor.fetchone():
                    QMessageBox.warning(self, "خطا در ثبت", "پزشکی با این شماره نظام پزشکی قبلاً ثبت شده است.")
                    self.medical_council_id_edit.selectAll()
                    self.medical_council_id_edit.setFocus()
                    return # از ادامه عملیات ذخیره جلوگیری شود
                
                cursor.execute("""
                    INSERT INTO doctors (first_name, last_name, medical_council_id, phone_number)
                    VALUES (?, ?, ?, ?)
                """, (first_name, last_name, medical_council_id, phone_number))
                QMessageBox.information(self, "ثبت موفق", "پزشک جدید با موفقیت در سیستم ثبت شد.")
            
            conn.commit()
            self.accept() # بستن دیالوگ در صورت موفقیت عملیات

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در هنگام ذخیره اطلاعات پزشک: {e}")
        finally:
            if conn:
                conn.close()