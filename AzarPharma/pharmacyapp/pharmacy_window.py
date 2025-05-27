import os
import sqlite3
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QComboBox, QLineEdit, QPushButton, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QSpacerItem, QGridLayout,QFormLayout , QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtGui import QIcon
from dialogs.drug_search_dialog import DrugSearchDialog
from dialogs.doctor_search_list_dialog import DoctorSearchListDialog
from PyQt6.QtGui import QIntValidator, QKeySequence, QAction
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer
from datetime import datetime
from persiantools.jdatetime import JalaliDate
from dialogs.prescription_labels_dialog import PrescriptionLabelsDialog
from database.db import get_connection
import traceback
from dialogs.otc_receipt_dialog import OTCReceiptDialog

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmacy.db')

class PharmacyApp(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ثبت و مدیریت نسخه")
        self.showMaximized()
        self.main_dashboard_parent = parent

        self.prescription_ids = []
        self.selected_drugs = []
        self.current_prescription_index = -1
        self.init_variables()
        self.set_initial_prescription_number()
        self.load_prescription_ids()
        self.patient_fields_order = []
           # --- متغیرهای جدید برای نگهداری اطلاعات پزشک انتخاب شده ---
        self.selected_doctor_id = None
        self.selected_doctor_full_name = ""
        self.selected_doctor_medical_council_id = ""
        # ---------------------------------------------------------
        # لیبل جدید برای نمایش شماره نظام پزشک در قاب کوچک اطلاعات پزشک
        self.doctor_selected_mc_id_display_label = QLabel("-")
        if not hasattr(self, 'doctor_selected_mc_id_display_label'):
             self.doctor_selected_mc_id_display_label = QLabel("-")
        self.create_widgets()
        self.update_main_table()
        self.install_shortcuts()
        self._update_print_labels_button_state()

    def init_variables(self):
        self.sale_type = "نسخه آزاد"
        self.insurance_name = "تأمین اجتماعی"
        self.version_type = "عادی"
        self.patient_first_name = ""
        
        # --- مقداردهی اولیه مشخصات بیمار ---
        self.patient_first_name = ""
        self.patient_last_name = ""
        self.patient_national_code = ""
        self.patient_phone_number = ""
        self.patient_birth_date = ""
        
        # ... (بقیه متغیرهای بیمار) ...
        self.selected_doctor_id = None
        self.selected_doctor_full_name = ""
        self.selected_doctor_medical_council_id = ""

        self.selected_drugs = [{
            "drug_id": None, # برای سازگاری با منطق ذخیره و کسر انبار
            "generic_name": "", "en_brand_name": "", "generic_code": "",
            "form": "", "dosage": "", "price": 0, "quantity": 1, "total_price": 0,
            "usage_instructions": ""
        }]
        self.prescription_number = ""
        self.current_prescription_index = -1
    def install_shortcuts(self):
        # ذخیره نسخه (F2)
        self.save_shortcut = QAction(self)
        self.save_shortcut.setShortcut(QKeySequence(Qt.Key.Key_F2))
        self.save_shortcut.triggered.connect(self.save_prescription)
        self.addAction(self.save_shortcut)
        # --- میانبر جدید برای حذف ردیف دارو ---
        self.delete_item_shortcut = QAction("حذف ردیف دارو", self)
        self.delete_item_shortcut.setShortcut(QKeySequence(Qt.Key.Key_F8))
        self.delete_item_shortcut.triggered.connect(self._delete_selected_prescription_item)
        self.addAction(self.delete_item_shortcut)
        # ------------------------------------

        self.prev_shortcut = QAction(self)
        self.prev_shortcut.setShortcut(QKeySequence(Qt.Key.Key_F11))
        self.prev_shortcut.triggered.connect(self.load_prev_prescription)
        self.addAction(self.prev_shortcut)

        self.next_shortcut = QAction(self)
        self.next_shortcut.setShortcut(QKeySequence(Qt.Key.Key_F12))
        self.next_shortcut.triggered.connect(self.load_next_prescription)
        self.addAction(self.next_shortcut)

        self.new_shortcut = QAction(self)
        self.new_shortcut.setShortcut(QKeySequence(Qt.Key.Key_F1))
        self.new_shortcut.triggered.connect(self.new_prescription)
        self.addAction(self.new_shortcut)

        self.new_window_shortcut = QAction(self)
        self.new_window_shortcut.setShortcut(QKeySequence(Qt.Key.Key_F3))
        self.new_window_shortcut.triggered.connect(self.open_new_pharmacy_window)
        self.addAction(self.new_window_shortcut)

    def closeEvent(self, event):
        if self.main_dashboard_parent:
            self.main_dashboard_parent.showMaximized()
        super().closeEvent(event)

    def get_db_connection(self):
        return get_connection(DB_PATH)

    def set_initial_prescription_number(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM prescriptions")
        max_id = cursor.fetchone()[0]
        self.prescription_number = "1" if max_id is None else str(max_id + 1)
        conn.close()

    def load_prescription_ids(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM prescriptions ORDER BY id")
        self.prescription_ids = [row[0] for row in cursor.fetchall()]
        self.current_prescription_index = len(self.prescription_ids) - 1 if self.prescription_ids else -1
        conn.close()

    def _delete_selected_prescription_item(self):
        """ردیف انتخاب شده در جدول داروهای نسخه را حذف می‌کند."""
        if not self.main_table.hasFocus() and not self.main_table.selectedItems():
            return

        selected_rows = self.main_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "انتخاب نشده", "لطفاً یک ردیف دارو را برای حذف از جدول انتخاب کنید.")
            return

        current_row_index = selected_rows[0].row()

        if 0 <= current_row_index < len(self.selected_drugs):
            item_to_delete = self.selected_drugs[current_row_index]
            
            if item_to_delete.get("generic_code"):
                reply = QMessageBox.question(self, "تایید حذف",
                                             f"آیا از حذف داروی '{item_to_delete.get('generic_name', 'انتخاب شده')}' از نسخه اطمینان دارید؟",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    del self.selected_drugs[current_row_index]
                    
                    if not self.selected_drugs:
                        self.selected_drugs.append({
                            "generic_name": "", "en_brand_name": "", "generic_code": "",
                            "form": "", "dosage": "", "price": 0, "quantity": 1, "total_price": 0
                        })
                    elif self.selected_drugs[-1].get("generic_code"):
                         self.selected_drugs.append({
                            "generic_name": "", "en_brand_name": "", "generic_code": "",
                            "form": "", "dosage": "", "price": 0, "quantity": 1, "total_price": 0
                        })
                        
                    self.update_main_table()
                    self.update_totals()
                    self._update_print_labels_button_state()
            else:
                QMessageBox.information(self, "عملیات نامعتبر", "این ردیف یک داروی ثبت شده نیست و قابل حذف نمی‌باشد.")
        else:
            QMessageBox.warning(self, "خطا", "ردیف انتخاب شده برای حذف نامعتبر است.")
            
    
    def _update_print_labels_button_state(self):
        """وضعیت دکمه چاپ لیبل‌ها را بر اساس وجود آیتم‌های دارویی در نسخه فعلی تنظیم می‌کند."""
        has_items = any(drug.get("generic_code") for drug in self.selected_drugs)
        is_valid_prescription_context = bool(self.prescription_number)

        if hasattr(self, 'print_labels_button'):
             self.print_labels_button.setEnabled(has_items)
        has_saved_prescription = bool(self.prescription_number and self.prescription_number.strip())
        self.print_receipt_button.setEnabled(has_saved_prescription)


    def _show_or_print_prescription_labels(self):
        """اطلاعات لازم را جمع‌آوری کرده و دیالوگ پیش‌نمایش لیبل‌ها را نمایش می‌دهد."""
        print("--- DEBUG: _show_or_print_prescription_labels called ---")
        items_for_labeling = [d for d in self.selected_drugs if d.get("generic_code")]

        if not items_for_labeling:
            QMessageBox.information(self, "لیبل دارو", "هیچ دارویی برای چاپ لیبل در نسخه فعلی وجود ندارد.")
            return

        patient_fname = self.patient_first_name_entry.text().strip()
        patient_lname = self.patient_last_name_entry.text().strip()
        patient_name = f"{patient_fname} {patient_lname}".strip()
        if not patient_name:
            patient_name = "بیمار محترم"

        doctor_name_to_print = self.selected_doctor_full_name if self.selected_doctor_id else "پزشک نامشخص"
        
        dialog = PrescriptionLabelsDialog(
            prescription_items=items_for_labeling,
            patient_name=patient_name,
            doctor_name=doctor_name_to_print,
            prescription_date=self.today_date_label.text(),
            parent=self
        )
        dialog.exec()



    def create_widgets(self):
        print("--- Running UPDATED create_widgets method (with early label definitions) ---")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6) 

        # تعریف فونت‌های مورد استفاده
        compact_font = QFont()
        compact_font.setPointSize(8) 
        
        small_button_font = QFont()
        small_button_font.setPointSize(8)

        # *** مهم: تعریف لیبل‌های جمع کل در ابتدای متد ***
        self.grand_total_label = QLabel("جمع کل: ۰ ریال")
        self.version_free_label = QLabel("جمع با ویزیت نسخه آزاد: ۰ ریال")
        self.grand_total_label.setFont(compact_font)
        self.version_free_label.setFont(compact_font)
        # *************************************************

        _afix_right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        _afix_left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        patient_field_max_width = 130 
        doctor_mc_id_field_max_width = 100 

        # --- لایه افقی برای نگهداری دو پنل اصلی در بالای صفحه ---
        top_panels_container_layout = QHBoxLayout()
        top_panels_container_layout.setSpacing(10)
        top_panels_container_layout.setContentsMargins(0,0,0,0)

        # --- پنل اطلاعات اصلی نسخه، بیمار و بیمه (سمت راست در RTL) ---
        main_prescription_info_RIGHT_panel = QFrame()
        main_prescription_info_RIGHT_panel.setObjectName("MainPrescriptionInfoRightPanel")
        main_prescription_info_RIGHT_panel.setMaximumWidth(580)
        main_prescription_info_RIGHT_panel_layout = QVBoxLayout(main_prescription_info_RIGHT_panel)
        main_prescription_info_RIGHT_panel_layout.setContentsMargins(2, 2, 2, 2)
        main_prescription_info_RIGHT_panel_layout.setSpacing(3)

        # بخش اطلاعات کلی نسخه
        rx_details_frame = QFrame()
        rx_details_layout = QGridLayout(rx_details_frame)
        rx_details_layout.setContentsMargins(0, 0, 0, 0)
        rx_details_layout.setHorizontalSpacing(4)
        rx_details_layout.setVerticalSpacing(2)

        lbl_presc_no = QLabel("شماره نسخه:")
        lbl_presc_no.setFont(compact_font)
        rx_details_layout.addWidget(lbl_presc_no, 0, 0, _afix_right)
        self.prescription_label = QLabel(self.prescription_number)
        self.prescription_label.setFont(compact_font)
        rx_details_layout.addWidget(self.prescription_label, 0, 1, _afix_left)

        lbl_date = QLabel("تاریخ:")
        lbl_date.setFont(compact_font)
        rx_details_layout.addWidget(lbl_date, 0, 2, _afix_right)
        self.today_date_label = QLabel(self.get_persian_date())
        self.today_date_label.setFont(compact_font)
        rx_details_layout.addWidget(self.today_date_label, 0, 3, _afix_left)

        lbl_sale_type = QLabel("نوع فروش:")
        lbl_sale_type.setFont(compact_font)
        rx_details_layout.addWidget(lbl_sale_type, 0, 4, _afix_right)
        self.sale_combobox = QComboBox()
        self.sale_combobox.setFont(compact_font)
        self.sale_combobox.addItems(["نسخه آزاد", "بیمه", "فروش دستی"])
        self.sale_combobox.setCurrentText(self.sale_type)
        self.sale_combobox.currentTextChanged.connect(self.update_sale_type)
        rx_details_layout.addWidget(self.sale_combobox, 0, 5)
        rx_details_layout.setColumnStretch(6, 1)
        main_prescription_info_RIGHT_panel_layout.addWidget(rx_details_frame)

        patient_insurance_details_frame = QFrame()
        patient_insurance_details_v_layout = QVBoxLayout(patient_insurance_details_frame)
        patient_insurance_details_v_layout.setContentsMargins(0,0,0,0)
        patient_insurance_details_v_layout.setSpacing(3)

        patient_details_frame = QFrame()
        patient_details_layout = QGridLayout(patient_details_frame)
        patient_details_layout.setContentsMargins(0,0,0,0)
        patient_details_layout.setHorizontalSpacing(4)
        patient_details_layout.setVerticalSpacing(2)
        
        patient_current_row = 0
        lbl_fname = QLabel("نام:"); lbl_fname.setFont(compact_font)
        patient_details_layout.addWidget(lbl_fname, patient_current_row, 0, _afix_right)
        self.patient_first_name_entry = QLineEdit(self.patient_first_name)
        self.patient_first_name_entry.setFont(compact_font)
        self.patient_first_name_entry.setMaximumWidth(patient_field_max_width)
        patient_details_layout.addWidget(self.patient_first_name_entry, patient_current_row, 1)
        
        lbl_lname = QLabel("نام خانوادگی:"); lbl_lname.setFont(compact_font)
        patient_details_layout.addWidget(lbl_lname, patient_current_row, 2, _afix_right)
        self.patient_last_name_entry = QLineEdit(self.patient_last_name)
        self.patient_last_name_entry.setFont(compact_font)
        self.patient_last_name_entry.setMaximumWidth(patient_field_max_width)
        patient_details_layout.addWidget(self.patient_last_name_entry, patient_current_row, 3)
        patient_details_layout.setColumnStretch(4,1)
        
        patient_current_row += 1
        lbl_nat_code = QLabel("کد ملی:"); lbl_nat_code.setFont(compact_font)
        patient_details_layout.addWidget(lbl_nat_code, patient_current_row, 0, _afix_right)
        self.patient_national_code_entry = QLineEdit(self.patient_national_code)
        self.patient_national_code_entry.setFont(compact_font)
        self.patient_national_code_entry.setValidator(QIntValidator())
        self.patient_national_code_entry.setMaximumWidth(patient_field_max_width)
        patient_details_layout.addWidget(self.patient_national_code_entry, patient_current_row, 1)

        lbl_phone = QLabel("شماره تماس:"); lbl_phone.setFont(compact_font)
        patient_details_layout.addWidget(lbl_phone, patient_current_row, 2, _afix_right)
        self.patient_phone_number_entry = QLineEdit(self.patient_phone_number)
        self.patient_phone_number_entry.setFont(compact_font)
        self.patient_phone_number_entry.setMaximumWidth(patient_field_max_width)
        patient_details_layout.addWidget(self.patient_phone_number_entry, patient_current_row, 3)

        patient_current_row += 1
        lbl_bdate = QLabel("تاریخ تولد:"); lbl_bdate.setFont(compact_font)
        patient_details_layout.addWidget(lbl_bdate, patient_current_row, 0, _afix_right)
        self.patient_birth_date_entry = QLineEdit(self.patient_birth_date)
        self.patient_birth_date_entry.setFont(compact_font)
        self.patient_birth_date_entry.setPlaceholderText("YYYY/MM/DD")
        self.patient_birth_date_entry.setMaximumWidth(patient_field_max_width)
        patient_details_layout.addWidget(self.patient_birth_date_entry, patient_current_row, 1)
        patient_insurance_details_v_layout.addWidget(patient_details_frame)

        insurance_details_frame = QFrame()
        insurance_details_layout = QGridLayout(insurance_details_frame)
        insurance_details_layout.setContentsMargins(0,3,0,0)
        insurance_details_layout.setHorizontalSpacing(4)
        insurance_details_layout.setVerticalSpacing(2)
        lbl_ins_name = QLabel("نام بیمه:"); lbl_ins_name.setFont(compact_font)
        insurance_details_layout.addWidget(lbl_ins_name, 0, 0, _afix_right)
        self.insurance_combo = QComboBox()
        self.insurance_combo.setFont(compact_font)
        new_insurance_items = ["تأمین اجتماعی", "سلامت", "نیروهای مسلح", "بیمه ایران", "بیمه آسیا", "بیمه البرز", "بیمه دانا", "بیمه پاسارگاد", "بیمه کارآفرین", "بیمه سینا", "بیمه ملت", "بیمه دی"]
        self.insurance_combo.addItems(new_insurance_items)
        self.insurance_combo.setCurrentText(self.insurance_name)
        insurance_details_layout.addWidget(self.insurance_combo, 0, 1)

        lbl_ver_type = QLabel("نوع نسخه:"); lbl_ver_type.setFont(compact_font)
        insurance_details_layout.addWidget(lbl_ver_type, 0, 2, _afix_right)
        self.version_combo = QComboBox()
        self.version_combo.setFont(compact_font)
        self.version_combo.addItems(["عادی", "جانباز"])
        self.version_combo.setCurrentText(self.version_type)
        insurance_details_layout.addWidget(self.version_combo, 0, 3)
        insurance_details_layout.setColumnStretch(4,1)
        patient_insurance_details_v_layout.addWidget(insurance_details_frame)
        patient_insurance_details_v_layout.addStretch(1)

        # ایجاد یک QWidget برای نگهداری patient_insurance_details_v_layout
        # این ویجت نقش یک کانتینر برای لایه را ایفا می‌کند.
        patient_insurance_details_container = QWidget()
        patient_insurance_details_container.setLayout(patient_insurance_details_v_layout)
        
        main_prescription_info_RIGHT_panel_layout.addWidget(patient_insurance_details_container)
        main_prescription_info_RIGHT_panel_layout.addStretch(1)

        # --- پنل اطلاعات پزشک (سمت چپ در RTL) ---
        doctor_info_LEFT_panel = QFrame()
        doctor_info_LEFT_panel.setObjectName("DoctorInfoLeftPanel")
        doctor_info_LEFT_panel.setMaximumWidth(320)
        doctor_info_LEFT_panel_layout = QVBoxLayout(doctor_info_LEFT_panel)
        doctor_info_LEFT_panel_layout.setContentsMargins(5, 2, 5, 2)
        doctor_info_LEFT_panel_layout.setSpacing(5)

        doctor_search_controls_frame = QFrame()
        doctor_search_controls_layout = QGridLayout(doctor_search_controls_frame)
        doctor_search_controls_layout.setContentsMargins(0,0,0,0)
        doctor_search_controls_layout.setHorizontalSpacing(3)
        doctor_search_controls_layout.setVerticalSpacing(3)

        lbl_doc_mcid = QLabel("نظام پزشکی:")
        lbl_doc_mcid.setFont(compact_font)
        doctor_search_controls_layout.addWidget(lbl_doc_mcid, 0, 0, _afix_right)
        
        self.doctor_mc_id_edit = QLineEdit()
        self.doctor_mc_id_edit.setFont(compact_font)
        self.doctor_mc_id_edit.setPlaceholderText("کد و Enter")
        self.doctor_mc_id_edit.setMaximumWidth(doctor_mc_id_field_max_width)
        self.doctor_mc_id_edit.returnPressed.connect(self._search_doctor_by_mc_id)
        doctor_search_controls_layout.addWidget(self.doctor_mc_id_edit, 0, 1)

        self.doctor_check_id_button = QPushButton("بررسی")
        self.doctor_check_id_button.setFont(small_button_font)
        self.doctor_check_id_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.doctor_check_id_button.setMinimumWidth(45)
        self.doctor_check_id_button.clicked.connect(self._search_doctor_by_mc_id)
        doctor_search_controls_layout.addWidget(self.doctor_check_id_button, 0, 2)
        
        self.doctor_search_dialog_button = QPushButton("لیست پزشکان")
        self.doctor_search_dialog_button.setFont(small_button_font)
        self.doctor_search_dialog_button.clicked.connect(self._open_doctor_search_dialog)
        doctor_search_controls_layout.addWidget(self.doctor_search_dialog_button, 1, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)

        doctor_search_controls_layout.setColumnStretch(1, 0)
        doctor_search_controls_layout.setColumnMinimumWidth(1, doctor_mc_id_field_max_width + 5)
        
        doctor_info_LEFT_panel_layout.addWidget(doctor_search_controls_frame)

        self.doctor_display_info_frame = QFrame()
        self.doctor_display_info_frame.setObjectName("DoctorDisplayFrame")
        self.doctor_display_info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.doctor_display_info_frame.setStyleSheet(
            "#DoctorDisplayFrame { background-color: #f0f0f0; border: 1px solid #dcdcdc; border-radius: 3px; padding: 3px; margin-top: 4px; }"
        )
        self.doctor_display_info_frame.setMinimumHeight(45)
        
        doctor_display_layout = QFormLayout(self.doctor_display_info_frame)
        doctor_display_layout.setContentsMargins(5,2,5,2)
        doctor_display_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        doctor_display_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        doctor_display_layout.setHorizontalSpacing(4)
        doctor_display_layout.setVerticalSpacing(1)

        self.doctor_name_label = QLabel("-")
        self.doctor_name_label.setFont(compact_font)
        self.doctor_name_label.setStyleSheet("font-weight: bold; color: #333;")
        
        if not hasattr(self, 'doctor_selected_mc_id_display_label'):
            self.doctor_selected_mc_id_display_label = QLabel("-")
        self.doctor_selected_mc_id_display_label.setFont(compact_font)
        self.doctor_selected_mc_id_display_label.setStyleSheet("color: #555;")

        lbl_doc_name_disp = QLabel("نام پزشک:")
        lbl_doc_name_disp.setFont(compact_font)
        doctor_display_layout.addRow(lbl_doc_name_disp, self.doctor_name_label)
        
        lbl_doc_mcid_disp = QLabel("نظام پزشکی:")
        lbl_doc_mcid_disp.setFont(compact_font)
        doctor_display_layout.addRow(lbl_doc_mcid_disp, self.doctor_selected_mc_id_display_label)
        
        doctor_info_LEFT_panel_layout.addWidget(self.doctor_display_info_frame)
        doctor_info_LEFT_panel_layout.addStretch(1)

        top_panels_container_layout.addWidget(main_prescription_info_RIGHT_panel)
        top_panels_container_layout.addStretch(1)
        top_panels_container_layout.addWidget(doctor_info_LEFT_panel)
        
        main_layout.addLayout(top_panels_container_layout)
        main_layout.addStretch(1)

        self.main_table = QTableWidget()
        self.patient_fields_order = [
            self.patient_first_name_entry, self.patient_last_name_entry,
            self.patient_national_code_entry, self.patient_phone_number_entry,
            self.patient_birth_date_entry, self.main_table
        ]
        for field in self.patient_fields_order[:-1]:
            if isinstance(field, QLineEdit):
                field.returnPressed.connect(self._handle_enter_navigation)
        
        self.update_sale_type(self.sale_type)
        self._update_doctor_display()

        self.main_table.setColumnCount(10)
        self.main_table.setHorizontalHeaderLabels([
            "ردیف", "نام ژنریک", "نام تجاری", "کد ژنریک",
            "شکل", "دوز", "دستور مصرف",
            "قیمت واحد", "تعداد", "قیمت کل"
        ])
        header = self.main_table.horizontalHeader()
        header.setFont(compact_font)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)

        self.main_table.setColumnWidth(0, 40)
        self.main_table.setColumnWidth(3, 100)
        self.main_table.setColumnWidth(4, 80)
        self.main_table.setColumnWidth(5, 80)
        self.main_table.setColumnWidth(7, 90)
        self.main_table.setColumnWidth(8, 60)
        self.main_table.setFont(compact_font)
        header.setFont(compact_font)
        self.main_table.setStyleSheet("QTableWidget { alternate-background-color: #f8f8f8; } QHeaderView::section { background-color: #e8e8e8; padding: 3px; }")
        self.main_table.setAlternatingRowColors(True)
        self.main_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.main_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.main_table.setEditTriggers(QTableWidget.EditTrigger.SelectedClicked | QTableWidget.EditTrigger.EditKeyPressed | QTableWidget.EditTrigger.DoubleClicked)
        self.main_table.cellClicked.connect(lambda row, col: self.main_table.selectRow(row)); self.main_table.cellDoubleClicked.connect(self.on_row_double_clicked)
        self.main_table.installEventFilter(self)
        main_layout.addWidget(self.main_table, 10)
        
        hbox_bottom = QHBoxLayout()
        self.prev_btn = QPushButton("نسخه قبلی (F11)")
        self.next_btn = QPushButton("نسخه بعدی (F12)")
        self.save_btn = QPushButton("ذخیره نسخه (F2)")
        self.new_btn = QPushButton("نسخه جدید (F1)")
        self.new_window_btn = QPushButton("ثبت نسخه جدید در پنجره دیگر (F3)")

        self.print_labels_button = QPushButton("چاپ لیبل‌ها (F6)")
        self.print_labels_button.setFont(compact_font if 'compact_font' in locals() else QFont())
        self.print_labels_button.clicked.connect(self._show_or_print_prescription_labels)
        self.print_labels_button.setEnabled(False)
        self.print_receipt_button = QPushButton("چاپ رسید")
        self.print_receipt_button.setStyleSheet("""
            QPushButton {
                background-color: #FF6B35;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E55A2B;
            }
            QPushButton:pressed {
                background-color: #CC4A1F;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.print_receipt_button.clicked.connect(self.open_print_receipt_dialog)
        self.print_receipt_button.setEnabled(False)
        
        for btn in [self.prev_btn, self.next_btn, self.save_btn, self.new_btn, self.new_window_btn, self.print_labels_button]:
            if hasattr(self, 'compact_font'): btn.setFont(self.compact_font)


        self.prev_btn.clicked.connect(self.load_prev_prescription)
        self.next_btn.clicked.connect(self.load_next_prescription)
        self.save_btn.clicked.connect(self.save_prescription)
        self.new_btn.clicked.connect(self.new_prescription)
        self.new_window_btn.clicked.connect(self.open_new_pharmacy_window)

        hbox_bottom.addWidget(self.prev_btn)
        hbox_bottom.addWidget(self.next_btn)
        hbox_bottom.addWidget(self.print_labels_button)
        hbox_bottom.addWidget(self.save_btn)
        hbox_bottom.addWidget(self.new_btn)
        hbox_bottom.addWidget(self.new_window_btn)
        hbox_bottom.addStretch(1)
        
        total_labels_layout = QVBoxLayout()
        total_labels_layout.addWidget(self.grand_total_label, alignment=Qt.AlignmentFlag.AlignRight)
        total_labels_layout.addWidget(self.version_free_label, alignment=Qt.AlignmentFlag.AlignRight)
        hbox_bottom.addLayout(total_labels_layout)
        main_layout.addLayout(hbox_bottom)

    def _handle_enter_navigation(self):
        sender = self.sender()
        try:
            current_index = self.patient_fields_order.index(sender)
            next_index = current_index + 1
            if next_index < len(self.patient_fields_order):
                next_widget = self.patient_fields_order[next_index]
                next_widget.setFocus()
                if isinstance(next_widget, QLineEdit):
                    next_widget.selectAll()
                elif isinstance(next_widget, QTableWidget):
                    if next_widget.rowCount() > 0:
                        first_empty_row_index = -1
                        for r_idx in range(next_widget.rowCount()):
                            item_gcode = next_widget.item(r_idx, 3)
                            if not item_gcode or not item_gcode.text():
                                first_empty_row_index = r_idx
                                break
                        
                        if first_empty_row_index != -1:
                            next_widget.setCurrentCell(first_empty_row_index, 1)
                        else:
                            next_widget.setCurrentCell(next_widget.rowCount() -1, 1)
            # اگر در آخرین فیلد بیمار (تاریخ تولد) بودیم و Enter زدیم، فوکوس به جدول منتقل شده
            # و منطق بالا برای جدول اجرا شده است.
        except ValueError:
            pass
        except AttributeError:
            pass

    def on_row_double_clicked(self, row, col):
        print(f"--- DEBUG: on_row_double_clicked - Row: {row}, Col: {col} ---")
        search_trigger_columns = [1, 2, 3]

        if col in search_trigger_columns:
            print(f"--- DEBUG: Double-click on a search trigger column ({col}). Opening drug search for row {row}. ---")
            self.open_drug_search_for_row(row)
        else:
            # برای سایر ستون‌ها (مانند تعداد یا دستور مصرف که قابل ویرایش هستند)،
            # رفتار پیش‌فرض دابل کلیک Qt (یعنی شروع ویرایش سلول) باید انجام شود
            # و ما اینجا کاری انجام نمی‌دهیم تا آن رفتار پیش‌فرض مختل نشود.
            pass


    def eventFilter(self, obj, event):
        if obj == self.main_table:
            if event.type() == event.Type.KeyPress:
                key = event.key()
                row, col = self.main_table.currentRow(), self.main_table.currentColumn()
                if key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                    if col == 7: # اگر در ستون قیمت واحد بود (ایندکس 7)
                        # ممکن است بخواهید ویرایش را روی تعداد (ستون 8) شروع کنید
                        self.main_table.setCurrentCell(row, 8)
                        self.main_table.editItem(self.main_table.item(row, 8))
                    elif col == 8: # اگر در ستون تعداد بود
                        # اگر آخرین ردیف نبود، به ردیف بعدی برو
                        if row < self.main_table.rowCount() - 1:
                            self.main_table.setCurrentCell(row + 1, 1) # به ستون نام ژنریک در ردیف بعدی
                            self.open_drug_search_for_row(row + 1) # باز کردن دیالوگ جستجو برای ردیف بعدی
                        else:
                            # اگر آخرین ردیف بود، یک ردیف جدید اضافه کن و فوکوس کن
                            if self.selected_drugs[-1].get("generic_code"): # اگر آخرین ردیف فعلی پر شده
                                self.selected_drugs.append({
                                    "drug_id": None, "generic_name": "", "en_brand_name": "", "generic_code": "",
                                    "form": "", "dosage": "", "price": 0, "quantity": 1, "total_price": 0,
                                    "usage_instructions": ""
                                })
                                self.update_main_table()
                                self.main_table.setCurrentCell(row + 1, 1)
                                self.open_drug_search_for_row(row + 1)
                            else: # اگر آخرین ردیف خالی بود، همانجا بمان و دیالوگ را باز کن
                                self.open_drug_search_for_row(row)
                    else: # برای سایر ستون‌ها، دیالوگ جستجو را باز کن
                        self.open_drug_search_for_row(row)
                    return True
                elif key in [Qt.Key.Key_Up, Qt.Key.Key_Down]:
                    next_row = row + (1 if key == Qt.Key.Key_Down else -1)
                    next_row = min(max(next_row, 0), self.main_table.rowCount()-1)
                    self.main_table.setCurrentCell(next_row, col)
                    self.main_table.selectRow(next_row)
                    return True
        return super().eventFilter(obj, event)


    def update_main_table(self):
        self.main_table.blockSignals(True)
        self.main_table.setRowCount(0)
        for i, drug_data in enumerate(self.selected_drugs):
            self.main_table.insertRow(i)
            item_values = [
                str(i + 1),
                drug_data.get("generic_name", ""), drug_data.get("en_brand_name", ""),
                drug_data.get("generic_code", ""), drug_data.get("form", ""),
                drug_data.get("dosage", ""), drug_data.get("usage_instructions", ""),
                f"{drug_data.get('price', 0):,.0f}", str(drug_data.get("quantity", 1)),
                f"{drug_data.get('total_price', 0):,.0f}"
            ]
            for col, val_text in enumerate(item_values):
                item = QTableWidgetItem(val_text)
                if drug_data.get("generic_code") and (col == 8 or col == 6):
                    item.setFlags(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                else:
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.main_table.setItem(i, col, item)
        
        self.main_table.blockSignals(False)

        try:
            self.main_table.cellChanged.disconnect(self.handle_table_cell_changed)
        except TypeError:
            pass
        self.main_table.cellChanged.connect(self.handle_table_cell_changed)
        
        self.update_totals()
        
    def handle_table_cell_changed(self, row, col):
        print(f"--- DEBUG: handle_table_cell_changed - Row: {row}, Col: {col} ---")
        
        if getattr(self, "_ignore_cell_change", False) or not (0 <= row < len(self.selected_drugs)):
            if getattr(self, "_ignore_cell_change", False): print("--- DEBUG: Ignoring cell change due to flag ---")
            else: print(f"--- DEBUG: Ignoring cell change due to invalid row index {row} for selected_drugs length {len(self.selected_drugs)} ---")
            return
        
        self._ignore_cell_change = True
        
        current_drug_data = self.selected_drugs[row]
        item_widget = self.main_table.item(row, col)
        new_text = item_widget.text().strip() if item_widget else ""
        print(f"--- DEBUG: Cell ({row},{col}) new_text: '{new_text}' ---")

        try:
            if col == 8:
                print(f"--- DEBUG: Quantity cell changed for drug: {current_drug_data.get('generic_name')} ---")
                try:
                    qty = int(new_text)
                    if qty < 0:
                        print("--- DEBUG: Quantity less than 0, setting to 0 ---")
                        qty = 0
                    
                    current_drug_data["quantity"] = qty
                    drug_price = current_drug_data.get("price", 0)
                    current_drug_data["total_price"] = qty * drug_price
                    print(f"--- DEBUG: New Quantity: {qty}, Price: {drug_price}, New Total Price for item: {current_drug_data['total_price']} ---")
                    
                    total_price_item_widget = self.main_table.item(row, 9)
                    if not total_price_item_widget:
                        total_price_item_widget = QTableWidgetItem()
                        self.main_table.setItem(row, 9, total_price_item_widget)
                    
                    total_price_item_widget.setText(f"{current_drug_data['total_price']:,.0f}")
                    print(f"--- DEBUG: Updated total price cell ({row},9) to: {total_price_item_widget.text()} ---")
                    
                    self.update_totals()

                    if current_drug_data.get("generic_code") and \
                       qty > 0 and \
                       row == len(self.selected_drugs) - 1 and \
                       self.selected_drugs[-1].get("generic_code"):
                        print("--- DEBUG: Adding new empty template row to selected_drugs ---")
                        self.selected_drugs.append({
                            "drug_id": None, "generic_name": "", "en_brand_name": "", "generic_code": "",
                            "form": "", "dosage": "", "price": 0, "quantity": 1, "total_price": 0,
                            "usage_instructions": ""
                        })
                        self.update_main_table()
                        self.main_table.setCurrentCell(row + 1, 1)
                        print("--- DEBUG: New template row added and focus moved. ---")

                except ValueError:
                    print(f"--- DEBUG ERROR: ValueError converting quantity '{new_text}' to int. Reverting. ---")
                    original_qty = current_drug_data.get("quantity", 1)
                    if item_widget: item_widget.setText(str(original_qty))
            
            elif col == 6:
                print(f"--- DEBUG: Usage instruction cell changed for drug: {current_drug_data.get('generic_name')} to '{new_text}' ---")
                current_drug_data["usage_instructions"] = new_text

        except Exception as e:
            print(f"--- DEBUG ERROR in handle_table_cell_changed (row:{row}, col:{col}): {e}\n{traceback.format_exc()} ---")
        finally:
            self._ignore_cell_change = False
            print(f"--- DEBUG: handle_table_cell_changed finished for ({row},{col}) ---")

    def open_drug_search_for_row(self, row_index_to_update):
        # ذخیره ایندکس ردیفی که قرار است به‌روز شود
        self._current_row_for_drug_selection = row_index_to_update

        # جلوگیری از باز شدن چند دیالوگ جستجو
        if getattr(self, '_search_dialog_open', False): return
        self._search_dialog_open = True
        
        dialog = DrugSearchDialog(self)
        # اتصال به سیگنال drug_selected_signal به جای فراخوانی get_selected_drug()
        dialog.drug_selected_signal.connect(self._handle_drug_selection)
        dialog.exec()
        
        self._search_dialog_open = False # پس از بسته شدن دیالوگ، فلگ را ریست می‌کنیم

    def _handle_drug_selection(self, drug_info):
        """
        این متد پس از انتخاب دارو از DrugSearchDialog توسط سیگنال فراخوانی می‌شود.
        drug_info شامل دیکشنری کامل اطلاعات داروی انتخاب شده است.
        """
        row_to_update = self._current_row_for_drug_selection # استفاده از ایندکس ذخیره شده
        print(f"--- DEBUG (_handle_drug_selection): Drug selected for row {row_to_update}: {drug_info.get('generic_name')} ---")

        if drug_info:
            # اطمینان از اینکه لیست selected_drugs به اندازه کافی بزرگ است
            while row_to_update >= len(self.selected_drugs):
                self.selected_drugs.append({
                    "drug_id": None, "generic_name": "", "en_brand_name": "", "generic_code": "",
                    "form": "", "dosage": "", "price": 0, "quantity": 1, "total_price": 0,
                    "usage_instructions": ""
                })

            self.selected_drugs[row_to_update] = {
               "drug_id": drug_info.get("id"),
               "generic_name": drug_info.get("generic_name", ""),
               "en_brand_name": drug_info.get("en_brand_name", ""),
               "generic_code": drug_info.get("generic_code", ""),
               "form": drug_info.get("form", ""),
               "dosage": drug_info.get("dosage", ""),
               "price": drug_info.get("price_per_unit", 0), # از price_per_unit استفاده شود
               "quantity": 1, # مقدار پیش‌فرض ۱ برای تعداد
               "total_price": drug_info.get("price_per_unit", 0) * 1, # محاسبه قیمت کل
               "usage_instructions": "" # دستور مصرف پیش‌فرض خالی
            }
            
            # اگر این ردیف، آخرین ردیف در selected_drugs بود و پر شد، یک ردیف خالی جدید اضافه کن
            if row_to_update == len(self.selected_drugs) - 1 and drug_info.get("generic_code"):
                self.selected_drugs.append({
                    "drug_id": None, "generic_name": "", "en_brand_name": "", "generic_code": "",
                    "form": "", "dosage": "", "price": 0, "quantity": 1, "total_price": 0,
                    "usage_instructions": ""
                })
            
            self.update_main_table() # جدول را با اطلاعات جدید به‌روز کن
            self._update_print_labels_button_state()
            
            # --- انتقال فوکوس به سلول "تعداد" (ایندکس 8) و شروع ویرایش ---
            print(f"--- DEBUG (_handle_drug_selection): Attempting to focus and edit cell ({row_to_update}, 8) for Quantity ---")
            
            QApplication.processEvents() # اطمینان از به‌روزرسانی UI
            
            target_item = self.main_table.item(row_to_update, 8) # ستون تعداد (ایندکس 8)
            if target_item:
                if target_item.flags() & Qt.ItemFlag.ItemIsEditable:
                    self.main_table.setCurrentCell(row_to_update, 8)
                    self.main_table.editItem(target_item)
                    print(f"--- DEBUG (_handle_drug_selection): Successfully initiated editing for cell ({row_to_update}, 8) ---")
                else:
                    print(f"--- DEBUG WARNING (_handle_drug_selection): Item at ({row_to_update}, 8) is NOT editable. Flags: {target_item.flags()} ---")
                    self.main_table.setCurrentCell(row_to_update, 8)
            else:
                print(f"--- DEBUG ERROR (_handle_drug_selection): Item at ({row_to_update}, 8) is None. Cannot set focus. ---")
            # -------------------------------------------------
        # اگر drug_info خالی بود (یعنی کاربر چیزی انتخاب نکرد و دیالوگ بسته شد)
        # هیچ کاری انجام نمی‌دهیم و پیام خطایی نمایش نمی‌دهیم.


    def update_totals(self):
        total = sum(d["total_price"] for d in self.selected_drugs if d.get("generic_code"))
        self.grand_total_label.setText(f"جمع کل: {total:,} ریال")
        if self.sale_type == "نسخه آزاد":
            grand_plus_visit = total + 330000
            self.version_free_label.setText(f"جمع با ویزیت نسخه آزاد: {grand_plus_visit:,} ریال")
        else:
            self.version_free_label.setText("")

    def get_persian_date(self):
        today = datetime.now()
        persian_date = JalaliDate(today)
        return f"{persian_date.year}/{persian_date.month:02d}/{persian_date.day:02d}"

    def update_sale_type(self, sale_type):
        self.sale_type = sale_type
        enable_insurance = (sale_type == "بیمه")
        self.insurance_combo.setEnabled(enable_insurance)
        self.version_combo.setEnabled(enable_insurance)
        self.patient_national_code_entry.setEnabled(True)
        self.patient_first_name_entry.setEnabled(True)
        self.patient_last_name_entry.setEnabled(True)
        self.patient_phone_number_entry.setEnabled(True)
        self.patient_birth_date_entry.setEnabled(True)
        if not enable_insurance:
            for w in [self.patient_national_code_entry, self.patient_first_name_entry, self.patient_last_name_entry,
                      self.patient_phone_number_entry, self.patient_birth_date_entry]:
                w.setEnabled(True)
        self.update_totals()

    def save_prescription(self):
        drugs_to_save_in_prescription = [
            d for d in self.selected_drugs if d.get("generic_code") and d.get("quantity", 0) > 0
        ]
        if not drugs_to_save_in_prescription:
            QMessageBox.warning(self, "خطا", "حداقل یک دارو با تعداد مثبت باید در نسخه وارد شود.")
            return
        total_prescription_price = sum(d["total_price"] for d in drugs_to_save_in_prescription)

        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            conn.execute("BEGIN TRANSACTION")

            cursor.execute(
                """INSERT INTO prescriptions (prescription_number, sale_type, date, total_price,
                       insurance_name, version_type, serial_number, patient_first_name, patient_last_name,
                       patient_national_code, patient_phone_number, patient_birth_date, doctor_id
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ( self.prescription_number, self.sale_type, self.get_persian_date(), total_prescription_price,
                  self.insurance_combo.currentText() if self.sale_type == "بیمه" else "",
                  self.version_combo.currentText() if self.sale_type == "بیمه" else "", "",
                  self.patient_first_name_entry.text(), self.patient_last_name_entry.text(),
                  self.patient_national_code_entry.text(), self.patient_phone_number_entry.text(),
                  self.patient_birth_date_entry.text(), self.selected_doctor_id ))
            prescription_id = cursor.lastrowid

            for drug_item in drugs_to_save_in_prescription:
                cursor.execute(
                    """INSERT INTO prescription_items (
                           prescription_id, drug_id, drug_name, dosage, form, generic_code, -- <--- drug_id اضافه شد
                           packaging, insurance, unit_price, quantity, total_price,
                           usage_instructions
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        prescription_id,
                        drug_item.get("drug_id"), # <--- مقدار drug_id
                        drug_item.get("en_brand_name", drug_item.get("generic_name")),
                        drug_item.get("dosage"),
                        drug_item.get("form"),
                        drug_item.get("generic_code"),
                        "بسته",
                        1 if self.sale_type == "بیمه" else 0,
                        drug_item.get("price"),
                        drug_item.get("quantity"),
                        drug_item.get("total_price"),
                        drug_item.get("usage_instructions", "")
                    )
                )
                generic_code = drug_item["generic_code"]
                quantity_to_deduct = drug_item["quantity"]
                drug_id_for_main_stock = drug_item.get("drug_id")

                quantity_remaining_to_deduct = quantity_to_deduct
                if generic_code:
                    cursor.execute("""
                        SELECT id, unit_count FROM company_purchase_items
                        WHERE generic_code = ? ORDER BY expiry_date_gregorian ASC LIMIT 1
                    """, (generic_code,))
                    first_available_batch = cursor.fetchone()
                    if first_available_batch:
                        batch_id_to_update = first_available_batch["id"]
                        current_batch_stock = first_available_batch["unit_count"]
                        new_batch_stock = (current_batch_stock if current_batch_stock is not None else 0) - quantity_to_deduct
                        cursor.execute("UPDATE company_purchase_items SET unit_count = ? WHERE id = ?", (new_batch_stock, batch_id_to_update))
                if drug_id_for_main_stock:
                    cursor.execute("UPDATE drugs SET stock = stock - ? WHERE id = ?", (quantity_to_deduct, drug_id_for_main_stock))
                elif generic_code:
                    cursor.execute("UPDATE drugs SET stock = stock - ? WHERE generic_code = ?", (quantity_to_deduct, generic_code))


            conn.commit()
            self.add_this_prescription_to_cash(prescription_id)
            QMessageBox.information(self, "ثبت موفق", "نسخه با موفقیت ثبت شد...")
            self.load_prescription_ids()
            self._update_print_labels_button_state()
            self.new_prescription()

        except sqlite3.Error as e:
            if conn: conn.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره نسخه: {e}\n{traceback.format_exc()}")
        except Exception as ex:
            if conn: conn.rollback()
            QMessageBox.critical(self, "خطای برنامه", f"یک خطای پیش بینی نشده در ذخیره نسخه رخ داد: {ex}\n{traceback.format_exc()}")
        finally:
            if conn:
                conn.close()
    def new_prescription(self):
        self.init_variables()
        self.set_initial_prescription_number()
        self.prescription_label.setText(self.prescription_number)
        self.today_date_label.setText(self.get_persian_date())
        
        self.patient_first_name_entry.setText(self.patient_first_name)
        self.patient_last_name_entry.setText(self.patient_last_name)
        self.patient_national_code_entry.setText(self.patient_national_code)
        self.patient_phone_number_entry.setText(self.patient_phone_number)
        self.patient_birth_date_entry.setText(self.patient_birth_date)

        self.sale_combobox.setCurrentText(self.sale_type)
        self.insurance_combo.setCurrentText(self.insurance_name)
        self.version_combo.setCurrentText(self.version_type)
        
        self._clear_doctor_info()
        self.update_main_table()
        self.update_totals()

        self.doctor_mc_id_edit.setFocus()
        self.print_receipt_button.setEnabled(False)
        self._update_print_labels_button_state()


    def open_new_pharmacy_window(self):
        w = PharmacyApp(parent=None)
        w.showMaximized()

    def load_prev_prescription(self):
        if not self.prescription_ids or self.current_prescription_index <= 0:
            QMessageBox.information(self, "پیام", "نسخه قبلی دیگری نیست.")
            return
        self.current_prescription_index -= 1
        self.load_prescription_by_index(self.current_prescription_index)

    def load_next_prescription(self):
        if not self.prescription_ids or self.current_prescription_index >= len(self.prescription_ids) - 1:
            QMessageBox.information(self, "پیام", "نسخه بعدی دیگری نیست.")
            return
        self.current_prescription_index += 1
        self.load_prescription_by_index(self.current_prescription_index)

    def add_this_prescription_to_cash(self, prescription_id):
        from dialogs.cash_register_dialog import CashRegisterDialog
        cd = CashRegisterDialog(self)
        cd.add_prescription_to_cash(prescription_id)

    def show_cash_register(self):
        from dialogs.cash_register_dialog import CashRegisterDialog
        dialog = CashRegisterDialog(self)
        dialog.exec()

    def show_total_cash(self):
        from dialogs.cash_histories_dialog import CashHistoriesDialog
        dialog = CashHistoriesDialog(self)
        dialog.exec()
    
    def _update_doctor_display(self):
            """متد برای به‌روزرسانی نمایش اطلاعات پزشک در UI."""
            if self.selected_doctor_id:
                self.doctor_mc_id_edit.setText(self.selected_doctor_medical_council_id or "")
                self.doctor_name_label.setText(self.selected_doctor_full_name or "-")
                self.doctor_selected_mc_id_display_label.setText(self.selected_doctor_medical_council_id or "-")
            else:
                self.doctor_name_label.setText("-")
                self.doctor_selected_mc_id_display_label.setText("-")

    def _clear_doctor_info(self):
        """پاک کردن اطلاعات پزشک انتخاب شده و UI مربوطه."""
        self.selected_doctor_id = None
        self.selected_doctor_full_name = ""
        self.selected_doctor_medical_council_id = ""
        self.doctor_mc_id_edit.clear()
        self.doctor_name_label.setText("-")
        self.doctor_selected_mc_id_display_label.setText("-")


    def _search_doctor_by_mc_id(self):
        """جستجوی پزشک بر اساس شماره نظام پزشکی وارد شده."""
        mc_id = self.doctor_mc_id_edit.text().strip()
        if not mc_id:
            self._clear_doctor_info()
            return

        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, first_name, last_name, medical_council_id FROM doctors WHERE medical_council_id = ?", (mc_id,))
            doctor_data = cursor.fetchone()

            if doctor_data:
                self.selected_doctor_id = doctor_data[0]
                self.selected_doctor_full_name = f"{doctor_data[1] or ''} {doctor_data[2] or ''}".strip()
                self.selected_doctor_medical_council_id = doctor_data[3]
                self._update_doctor_display()
                if self.patient_fields_order and self.patient_fields_order[0]:
                    self.patient_fields_order[0].setFocus()
            else:
                self._clear_doctor_info()
                QMessageBox.information(self, "پزشک یافت نشد", f"پزشکی با شماره نظام پزشکی '{mc_id}' یافت نشد. می‌توانید از لیست جستجو کنید یا پزشک جدید اضافه نمایید.")
        except sqlite3.Error as e:
            self._clear_doctor_info()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در جستجوی پزشک: {e}")
        finally:
            if conn:
                conn.close()

    def _open_doctor_search_dialog(self):
        """باز کردن دیالوگ جستجو و انتخاب پزشک از لیست."""
        dialog = DoctorSearchListDialog(self)
        if dialog.exec():
            selected_info = dialog.get_selected_doctor_data()
            if selected_info:
                self.selected_doctor_id = selected_info.get("id")
                self.selected_doctor_full_name = selected_info.get("full_name")
                self.selected_doctor_medical_council_id = selected_info.get("medical_council_id")
                self._update_doctor_display()
                if self.patient_fields_order and self.patient_fields_order[0]:
                     self.patient_fields_order[0].setFocus()
            else:
                self._clear_doctor_info()

    def load_prescription_by_index(self, idx):
        prescription_id_to_load = self.prescription_ids[idx]
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, prescription_number, sale_type, date, total_price,
                          insurance_name, version_type, serial_number,
                          patient_first_name, patient_last_name, patient_national_code,
                          patient_phone_number, patient_birth_date, doctor_id
                   FROM prescriptions WHERE id = ?""",
                (prescription_id_to_load,)
            )
            prescription_data = cursor.fetchone()
            if not prescription_data: return

            (pid, pnum, sale, date, tprice, ins_name, vtype, serial,
             pfname, plname, nc, phone, bdate, loaded_doctor_id) = prescription_data
            
            self.prescription_number = str(pnum); self.prescription_label.setText(self.prescription_number)
            self.sale_combobox.setCurrentText(sale or "نسخه آزاد"); self.today_date_label.setText(date or self.get_persian_date())
            self.insurance_combo.setCurrentText(ins_name or "تأمین اجتماعی"); self.version_combo.setCurrentText(vtype or "عادی")
            self.patient_first_name_entry.setText(pfname or ""); self.patient_last_name_entry.setText(plname or "")
            self.patient_national_code_entry.setText(nc or ""); self.patient_phone_number_entry.setText(phone or "")
            self.patient_birth_date_entry.setText(bdate or "")
            if loaded_doctor_id:
                cursor.execute("SELECT first_name, last_name, medical_council_id FROM doctors WHERE id = ?", (loaded_doctor_id,))
                doctor_details = cursor.fetchone()
                if doctor_details:
                    self.selected_doctor_id = loaded_doctor_id
                    self.selected_doctor_full_name = f"{doctor_details[0] or ''} {doctor_details[1] or ''}".strip()
                    self.selected_doctor_medical_council_id = doctor_details[2] or ""
                else: self._clear_doctor_info()
            else: self._clear_doctor_info()
            self._update_doctor_display()


            cursor.execute(
                """SELECT drug_id, drug_name, dosage, form, generic_code, unit_price, quantity, total_price, usage_instructions
                   FROM prescription_items WHERE prescription_id = ?""",
                (pid,)
            )
            self.selected_drugs = []
            for item_data_row in cursor.fetchall():
                self.selected_drugs.append({
                    "drug_id": item_data_row["drug_id"], # <--- خواندن drug_id
                    "generic_name": item_data_row["drug_name"], # یا اگر نام ژنریک جدا دارید
                    "en_brand_name": item_data_row["drug_name"],
                    "generic_code": item_data_row["generic_code"],
                    "form": item_data_row["form"],
                    "dosage": item_data_row["dosage"],
                    "price": item_data_row["unit_price"],
                    "quantity": item_data_row["quantity"],
                    "total_price": item_data_row["total_price"],
                    "usage_instructions": item_data_row["usage_instructions"] or "" # <--- خواندن دستور مصرف
                })
            
            if not self.selected_drugs:
                self.selected_drugs = [{
                    "drug_id": None, "generic_name": "", "en_brand_name": "", "generic_code": "",
                    "form": "", "dosage": "", "price": 0, "quantity": 1, "total_price": 0,
                    "usage_instructions": ""
                }]
            elif self.selected_drugs[-1].get("generic_code"):
                self.selected_drugs.append({
                    "drug_id": None, "generic_name": "", "en_brand_name": "", "generic_code": "",
                    "form": "", "dosage": "", "price": 0, "quantity": 1, "total_price": 0,
                    "usage_instructions": ""
                })

            self.update_main_table()
            self.update_totals()
            self.current_prescription_index = idx
            self._update_print_labels_button_state()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در بارگذاری نسخه: {str(e)}")
        except Exception as ex:
             QMessageBox.critical(self, "خطای برنامه", f"یک خطای پیش بینی نشده در بارگذاری نسخه رخ داد: {str(ex)}")
        finally:
            if conn:
                conn.close()

    def open_print_receipt_dialog(self):
        """باز کردن دیالوگ چاپ رسید OTC"""
        try:
            if not self.prescription_number:
                QMessageBox.warning(self, "خطا", "ابتدا نسخه را ذخیره کنید.")
                return
                
            # جمع‌آوری اطلاعات نسخه برای رسید
            receipt_data = {
                'prescription_number': self.prescription_number,
                'patient_name': f"{self.patient_first_name_entry.text()} {self.patient_last_name_entry.text()}".strip(),
                'patient_national_code': self.patient_national_code_entry.text(),
                'patient_phone': self.patient_phone_number_entry.text(),
                'doctor_name': self.selected_doctor_full_name,
                'doctor_medical_council_id': self.selected_doctor_medical_council_id,
                'sale_type': self.sale_type,
                'insurance_name': self.insurance_name,
                'drugs': []
            }
            
            # افزودن داروها به رسید
            total_amount = 0
            for drug in self.selected_drugs:
                if drug.get('generic_code'):
                    drug_info = {
                        'name': drug.get('generic_name', ''),
                        'brand': drug.get('en_brand_name', ''),
                        'form': drug.get('form', ''),
                        'dosage': drug.get('dosage', ''),
                        'quantity': drug.get('quantity', 1),
                        'price': drug.get('price', 0),
                        'total': drug.get('total_price', 0)
                    }
                    receipt_data['drugs'].append(drug_info)
                    total_amount += drug.get('total_price', 0)
            
            receipt_data['total_amount'] = total_amount
            
            # باز کردن دیالوگ رسید
            dialog = OTCReceiptDialog(receipt_data, self)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن دیالوگ رسید:\n{str(e)}")
            print(f"Error in open_print_receipt_dialog: {e}")
            traceback.print_exc()