# dialogs/warehouse_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, 
    QLabel, QHeaderView, QMenu
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from database.db import get_connection
from dialogs.add_drug_simple_dialog import AddDrugSimpleDialog
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmacy.db')

class WarehouseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("لیست کامل انبار داروخانه")
        self.setMinimumSize(900, 600)
        layout = QVBoxLayout(self)

        btn_add = QPushButton("افزودن دارو")
        btn_add.clicked.connect(self.open_add_drug_dialog)
        hlayout = QHBoxLayout()
        hlayout.addWidget(btn_add)
        hlayout.addStretch(1)
        layout.addLayout(hlayout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "کد ژنریک", "نام ژنریک", "نام تجاری", "فرم", "دوز", "قیمت هر واحد", "موجودی"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.table)

        btn_close = QPushButton("بستن")
        btn_close.clicked.connect(self.close)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(btn_close)
        layout.addLayout(hbox)

        self.load_warehouse_data()

    def load_warehouse_data(self):
        self.table.setRowCount(0)
        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT generic_code, generic_name, en_brand_name, form, dosage, price_per_unit, stock FROM drugs")
            drugs = cursor.fetchall()
            for row_num, drug in enumerate(drugs):
                self.table.insertRow(row_num)
                for col, value in enumerate(drug):
                    self.table.setItem(row_num, col, QTableWidgetItem(str(value)))
            conn.close()
        except Exception as e:
            print(f"خطا در بارگذاری انبار: {e}")

    def open_add_drug_dialog(self):
        dialog = AddDrugSimpleDialog(self)
        if dialog.exec():
            self.load_warehouse_data()

    def open_context_menu(self, pos):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return
        row = indexes[0].row()
        m = QMenu(self)
        act_edit = QAction("ویرایش دارو", self)
        m.addAction(act_edit)
        act_edit.triggered.connect(lambda: self.edit_drug(row))
        m.exec(self.table.viewport().mapToGlobal(pos))

    def edit_drug(self, row):
        drug_data = {
            "generic_code": self.table.item(row, 0).text(),
            "generic_name": self.table.item(row, 1).text(),
            "en_brand_name": self.table.item(row, 2).text(),
            "form": self.table.item(row, 3).text(),
            "dosage": self.table.item(row, 4).text(),
            "price_per_unit": self.table.item(row, 5).text()
        }
        dialog = AddDrugSimpleDialog(self, drug_data=drug_data)
        if dialog.exec():
            self.load_warehouse_data()