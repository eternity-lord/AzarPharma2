# dialogs/suppliers_management_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QPushButton, QHBoxLayout, 
    QStyle, QTableWidgetItem, QMessageBox, QAbstractItemView, QLabel
)
from PyQt6.QtCore import Qt
import os
from PyQt6.QtGui import QAction
from dialogs.supplier_dialog import SupplierEditDialog
from database.db import get_connection

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmacy.db')

class SuppliersManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("توزیع کنندگان و طرف انبارها")
        self.setGeometry(200, 100, 800, 500)
        
        main_layout = QVBoxLayout(self)
        
        # جدول نمایش شرکت‌ها
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.suppliers_table.setColumnCount(5)
        self.suppliers_table.setHorizontalHeaderLabels(["شناسه", "نام", "آدرس", "تلفن", "موبایل"])
        
        self.suppliers_table.setColumnWidth(0, 60)
        self.suppliers_table.setColumnWidth(1, 200)
        self.suppliers_table.setColumnWidth(2, 250)
        self.suppliers_table.setColumnWidth(3, 120)
        self.suppliers_table.setColumnWidth(4, 120)
        
        main_layout.addWidget(self.suppliers_table)
        
        # دکمه‌های عملیات
        button_layout = QHBoxLayout()
        
        self.new_supplier_btn = QPushButton("جدید F1")
        self.new_supplier_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.new_supplier_btn.clicked.connect(self.add_new_supplier)
        
        self.edit_supplier_btn = QPushButton("ویرایش F5")
        self.edit_supplier_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.edit_supplier_btn.clicked.connect(self.edit_selected_supplier)
        
        self.delete_supplier_btn = QPushButton("حذف F8")
        self.delete_supplier_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.delete_supplier_btn.clicked.connect(self.delete_selected_supplier)
        
        self.export_excel_btn = QPushButton("فایل اکسل Alt+E")
        self.export_excel_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        # TODO: پیاده سازی خروجی اکسل در صورت نیاز
        
        self.cancel_btn = QPushButton("انصراف F4")
        self.cancel_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.new_supplier_btn)
        button_layout.addWidget(self.edit_supplier_btn)
        button_layout.addWidget(self.delete_supplier_btn)
        button_layout.addWidget(self.export_excel_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # میانبرهای کیبورد
        self.shortcut_f1 = QAction(self)
        self.shortcut_f1.setShortcut("F1")
        self.shortcut_f1.triggered.connect(self.add_new_supplier)
        self.addAction(self.shortcut_f1)
        
        self.shortcut_f5 = QAction(self)
        self.shortcut_f5.setShortcut("F5")
        self.shortcut_f5.triggered.connect(self.edit_selected_supplier)
        self.addAction(self.shortcut_f5)
        
        self.shortcut_f8 = QAction(self)
        self.shortcut_f8.setShortcut("F8")
        self.shortcut_f8.triggered.connect(self.delete_selected_supplier)
        self.addAction(self.shortcut_f8)
        
        self.shortcut_f4 = QAction(self)
        self.shortcut_f4.setShortcut("F4")
        self.shortcut_f4.triggered.connect(self.reject)
        self.addAction(self.shortcut_f4)
        
        # بارگذاری اولیه داده‌ها
        self.load_suppliers()
        
        # اتصال دابل کلیک در جدول به ویرایش
        self.suppliers_table.cellDoubleClicked.connect(lambda row, col: self.edit_selected_supplier())
        
    def load_suppliers(self):
        """بارگذاری شرکت‌های پخش از دیتابیس"""
        self.suppliers_table.clearContents()
        self.suppliers_table.setRowCount(0)
        
        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, address, phone, contact_person FROM suppliers ORDER BY name")
            
            for row_idx, row_data in enumerate(cursor.fetchall()):
                self.suppliers_table.insertRow(row_idx)
                for col_idx, cell_data in enumerate(row_data):
                    self.suppliers_table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data or "")))
            
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری شرکت‌های پخش: {str(e)}")
    
    def add_new_supplier(self):
        """اضافه کردن شرکت پخش جدید"""
        dialog = SupplierEditDialog(self)
        if dialog.exec():
            self.load_suppliers()
    
    def edit_selected_supplier(self):
        """ویرایش شرکت پخش انتخاب شده"""
        selected_rows = self.suppliers_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "انتخاب نشده", "لطفاً یک شرکت را برای ویرایش انتخاب کنید.")
            return
            
        supplier_id = int(self.suppliers_table.item(selected_rows[0].row(), 0).text())
        dialog = SupplierEditDialog(self, supplier_id)
        if dialog.exec():
            self.load_suppliers()
    
    def delete_selected_supplier(self):
        """حذف شرکت پخش انتخاب شده"""
        selected_rows = self.suppliers_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "انتخاب نشده", "لطفاً یک شرکت را برای حذف انتخاب کنید.")
            return
            
        supplier_id = int(self.suppliers_table.item(selected_rows[0].row(), 0).text())
        supplier_name = self.suppliers_table.item(selected_rows[0].row(), 1).text()
        
        reply = QMessageBox.question(self, "تأیید حذف", 
                                    f"آیا از حذف شرکت {supplier_name} اطمینان دارید؟",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = get_connection(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
                conn.commit()
                conn.close()
                self.load_suppliers()
                QMessageBox.information(self, "حذف موفق", f"شرکت {supplier_name} با موفقیت حذف شد.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف شرکت: {str(e)}")