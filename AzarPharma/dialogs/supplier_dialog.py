# dialogs/supplier_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QHBoxLayout,
    QPushButton, QStyle, QMessageBox
)
from PyQt6.QtCore import Qt
import sqlite3
import os
from PyQt6.QtGui import QAction
# توصیه: DB_PATH را در بالا از یک کانفیگ یا مسیر ثابت پروژکت بیاور، این نمونه است:
from database.db import get_connection

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmacy.db')


class SupplierEditDialog(QDialog):
    def __init__(self, parent=None, supplier_id=None):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.setWindowTitle("افزودن/ویرایش طرف انبار")
        self.setFixedSize(500, 350)

        layout = QVBoxLayout(self)

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(15)
        form_layout.setVerticalSpacing(10)

        # نام شرکت
        form_layout.addWidget(QLabel("نام شرکت:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("نام شرکت پخش را وارد کنید")
        form_layout.addWidget(self.name_edit, 0, 1, 1, 3)

        # شخص رابط
        form_layout.addWidget(QLabel("شخص رابط:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.contact_person_edit = QLineEdit()
        self.contact_person_edit.setPlaceholderText("نام شخص رابط")
        form_layout.addWidget(self.contact_person_edit, 1, 1, 1, 3)

        # شماره تماس
        form_layout.addWidget(QLabel("شماره تماس:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("شماره تماس ثابت")
        form_layout.addWidget(self.phone_edit, 2, 1)

        # آدرس
        form_layout.addWidget(QLabel("آدرس:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("آدرس شرکت")
        form_layout.addWidget(self.address_edit, 3, 1, 1, 3)

        # توضیحات
        form_layout.addWidget(QLabel("توضیحات:"), 4, 0, Qt.AlignmentFlag.AlignRight)
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("توضیحات اضافی")
        form_layout.addWidget(self.description_edit, 4, 1, 1, 3)

        layout.addLayout(form_layout)
        layout.addStretch(1)

        # دکمه‌های تایید و انصراف
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("ثبت F2")
        self.save_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.save_button.clicked.connect(self.save_supplier)

        self.cancel_button = QPushButton("انصراف Esc")
        self.cancel_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch(1)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # میانبرهای کیبورد
        self.shortcut_f2 = QAction(self)
        self.shortcut_f2.setShortcut("F2")
        self.shortcut_f2.triggered.connect(self.save_supplier)
        self.addAction(self.shortcut_f2)

        self.shortcut_esc = QAction(self)
        self.shortcut_esc.setShortcut("Esc")
        self.shortcut_esc.triggered.connect(self.reject)
        self.addAction(self.shortcut_esc)

        # اگر در حالت ویرایش هستیم، داده‌ها را بارگذاری می‌کنیم
        if self.supplier_id:
            self.load_supplier_data()

    def load_supplier_data(self):
        """بارگذاری اطلاعات شرکت برای ویرایش"""
        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, contact_person, phone, address, description FROM suppliers WHERE id = ?", (self.supplier_id,))
            data = cursor.fetchone()
            conn.close()

            if data:
                self.name_edit.setText(data[0] or "")
                self.contact_person_edit.setText(data[1] or "")
                self.phone_edit.setText(data[2] or "")
                self.address_edit.setText(data[3] or "")
                self.description_edit.setText(data[4] or "")
            else:
                QMessageBox.warning(self, "خطا", "اطلاعات شرکت یافت نشد.")
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری اطلاعات شرکت: {str(e)}")
            self.reject()

    def save_supplier(self):
        """ذخیره اطلاعات شرکت"""
        name = self.name_edit.text().strip()
        contact_person = self.contact_person_edit.text().strip()
        phone = self.phone_edit.text().strip()
        address = self.address_edit.text().strip()
        description = self.description_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "خطا", "نام شرکت الزامی است.")
            self.name_edit.setFocus()
            return

        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()

            if self.supplier_id:  # ویرایش
                cursor.execute("""
                    UPDATE suppliers 
                    SET name = ?, contact_person = ?, phone = ?, address = ?, description = ? 
                    WHERE id = ?
                """, (name, contact_person, phone, address, description, self.supplier_id))
                message = "اطلاعات شرکت با موفقیت به‌روزرسانی شد."
            else:  # اضافه کردن جدید
                cursor.execute("""
                    INSERT INTO suppliers (name, contact_person, phone, address, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, contact_person, phone, address, description))
                message = "شرکت جدید با موفقیت ثبت شد."

            conn.commit()
            conn.close()
            QMessageBox.information(self, "ثبت موفق", message)
            self.accept()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطا", "شرکتی با این نام قبلاً ثبت شده است.")
            self.name_edit.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره اطلاعات شرکت: {str(e)}")