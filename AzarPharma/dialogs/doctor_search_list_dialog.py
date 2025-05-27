# dialogs/doctor_search_list_dialog.py

import sqlite3
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QMenu, QFrame # QMenu اضافه شد
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction # QAction اضافه شد

from .add_edit_doctor_dialog import AddEditDoctorDialog

try:
    from config import DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, 'pharmacy.db')
    # print(f"Warning: config.py not found or DB_PATH not in it. Using default DB_PATH in DoctorSearchListDialog: {DB_PATH}")

def get_db_connection_local():
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=10)


class DoctorSearchListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("جستجو و انتخاب پزشک")
        self.setMinimumSize(700, 500)
        self.selected_doctor_info = None

        self._setup_ui()
        self._load_doctors_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        search_group_box = QFrame()
        search_group_box.setFrameShape(QFrame.Shape.StyledPanel)
        search_layout = QHBoxLayout(search_group_box)

        self.name_search_edit = QLineEdit()
        self.name_search_edit.setPlaceholderText("جستجو بر اساس نام یا نام خانوادگی...")
        self.name_search_edit.textChanged.connect(self._filter_doctors)
        search_layout.addWidget(QLabel("نام:"))
        search_layout.addWidget(self.name_search_edit, 1)

        self.mc_id_search_edit = QLineEdit()
        self.mc_id_search_edit.setPlaceholderText("جستجو بر اساس شماره نظام پزشکی...")
        self.mc_id_search_edit.textChanged.connect(self._filter_doctors)
        search_layout.addWidget(QLabel("نظام پزشکی:"))
        search_layout.addWidget(self.mc_id_search_edit, 1)
        
        main_layout.addWidget(search_group_box)

        self.doctors_table = QTableWidget()
        self.doctors_table.setColumnCount(4)
        self.doctors_table.setHorizontalHeaderLabels(["شناسه", "نام و نام خانوادگی", "شماره نظام پزشکی", "شماره تلفن"])
        self.doctors_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.doctors_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.doctors_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.doctors_table.verticalHeader().setVisible(False)

        header = self.doctors_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        
        self.doctors_table.setColumnWidth(0, 60)
        self.doctors_table.setColumnWidth(2, 150)
        self.doctors_table.setColumnWidth(3, 130)

        self.doctors_table.doubleClicked.connect(self._select_doctor_and_accept)

        # --- تغییر جدید: فعال کردن و اتصال منوی راست کلیک ---
        self.doctors_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.doctors_table.customContextMenuRequested.connect(self._show_context_menu)
        # ----------------------------------------------------

        main_layout.addWidget(self.doctors_table, 1)

        buttons_layout = QHBoxLayout()
        self.add_doctor_button = QPushButton("افزودن پزشک جدید (F2)")
        self.add_doctor_button.clicked.connect(self._open_add_doctor_dialog)
        
        self.select_button = QPushButton("انتخاب پزشک (Enter)")
        self.select_button.setDefault(True)
        self.select_button.clicked.connect(self._select_doctor_and_accept)
        
        self.cancel_button = QPushButton("انصراف (Esc)")
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.add_doctor_button)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.select_button)
        buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(buttons_layout)

    def _load_doctors_data(self, name_filter=None, mc_id_filter=None):
        # این متد بدون تغییر باقی می‌ماند (همانند نسخه قبلی)
        self.doctors_table.setRowCount(0) 
        conn = None
        try:
            conn = get_db_connection_local()
            cursor = conn.cursor()
            
            query = "SELECT id, first_name, last_name, medical_council_id, phone_number FROM doctors"
            conditions = []
            params = []

            if name_filter:
                conditions.append("(LOWER(first_name) LIKE LOWER(?) OR LOWER(last_name) LIKE LOWER(?))") # جستجوی غیر حساس به حروف کوچک و بزرگ
                params.extend([f"%{name_filter}%", f"%{name_filter}%"])
            
            if mc_id_filter:
                conditions.append("medical_council_id LIKE ?")
                params.append(f"%{mc_id_filter}%")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY last_name, first_name"

            cursor.execute(query, params)
            doctors = cursor.fetchall()

            for row_num, doctor_data in enumerate(doctors):
                self.doctors_table.insertRow(row_num)
                # ذخیره ID در آیتم اول به عنوان داده (برای دسترسی آسان‌تر)
                id_item = QTableWidgetItem(str(doctor_data[0]))
                id_item.setData(Qt.ItemDataRole.UserRole, doctor_data[0]) # ID پزشک را به عنوان UserRole ذخیره می‌کنیم
                self.doctors_table.setItem(row_num, 0, id_item)
                
                full_name = f"{doctor_data[1] or ''} {doctor_data[2] or ''}".strip()
                self.doctors_table.setItem(row_num, 1, QTableWidgetItem(full_name))
                self.doctors_table.setItem(row_num, 2, QTableWidgetItem(doctor_data[3] or ""))
                self.doctors_table.setItem(row_num, 3, QTableWidgetItem(doctor_data[4] or ""))
        
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در بارگذاری لیست پزشکان: {e}")
        finally:
            if conn:
                conn.close()


    def _filter_doctors(self):
        name_query = self.name_search_edit.text().strip()
        mc_id_query = self.mc_id_search_edit.text().strip()
        self._load_doctors_data(name_filter=name_query, mc_id_filter=mc_id_query)

    def _open_add_doctor_dialog(self):
        dialog = AddEditDoctorDialog(self)
        if dialog.exec():
            self._filter_doctors() # به‌روزرسانی لیست با حفظ فیلترهای فعلی یا _load_doctors_data() برای بارگذاری مجدد همه

    def _select_doctor_and_accept(self):
        selected_rows = self.doctors_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "انتخاب نشده", "لطفاً یک پزشک را از لیست انتخاب کنید.")
            return
        
        selected_row_index = selected_rows[0].row()
        # استفاده از UserRole برای گرفتن ID به جای تبدیل از متن
        doctor_id_item = self.doctors_table.item(selected_row_index, 0)
        doctor_id = doctor_id_item.data(Qt.ItemDataRole.UserRole) if doctor_id_item else -1
        
        full_name = self.doctors_table.item(selected_row_index, 1).text()
        medical_council_id = self.doctors_table.item(selected_row_index, 2).text()
        
        self.selected_doctor_info = {
            "id": doctor_id,
            "full_name": full_name,
            "medical_council_id": medical_council_id
        }
        self.accept()

    def get_selected_doctor_data(self):
        return self.selected_doctor_info

    # --- متدهای جدید برای منوی راست کلیک و ویرایش ---
    def _show_context_menu(self, pos):
        """نمایش منوی راست کلیک روی جدول پزشکان."""
        selected_item = self.doctors_table.itemAt(pos)
        if not selected_item: # اگر روی فضای خالی کلیک شد
            return

        # انتخاب ردیفی که روی آن کلیک شده است
        self.doctors_table.selectRow(selected_item.row()) 

        menu = QMenu(self)
        edit_action = QAction("ویرایش پزشک", self)
        edit_action.triggered.connect(self._open_edit_doctor_dialog)
        menu.addAction(edit_action)
        
        # می‌توانید گزینه‌های دیگری مانند "حذف پزشک" را هم در آینده اضافه کنید
        # delete_action = QAction("حذف پزشک", self)
        # menu.addAction(delete_action)

        menu.exec(self.doctors_table.mapToGlobal(pos)) # نمایش منو در مختصات کلیک موس

    def _open_edit_doctor_dialog(self):
        """باز کردن دیالوگ ویرایش برای پزشک انتخاب شده."""
        selected_rows = self.doctors_table.selectionModel().selectedRows()
        if not selected_rows:
            # این حالت معمولا رخ نمی‌دهد چون منو فقط برای آیتم‌های انتخاب شده باز می‌شود
            return 

        selected_row_index = selected_rows[0].row()
        doctor_id_item = self.doctors_table.item(selected_row_index, 0)
        if not doctor_id_item: return # اطمینان از وجود آیتم شناسه

        doctor_id = doctor_id_item.data(Qt.ItemDataRole.UserRole)
        if doctor_id is None: return # اطمینان از معتبر بودن شناسه

        dialog = AddEditDoctorDialog(self, doctor_id=doctor_id)
        if dialog.exec(): # اگر ویرایش با موفقیت انجام شد
            self._filter_doctors() # به‌روزرسانی لیست با حفظ فیلترهای فعلی یا _load_doctors_data()
    # -------------------------------------------------