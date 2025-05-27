# dialogs/ttak_update_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QMenu, QMessageBox, QHeaderView, QLabel)
from PyQt6.QtCore import Qt
from database.db import get_connection
from utils.ttak_api import fetch_data_from_ttak_api
from PyQt6.QtGui import  QAction
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmacy.db')

class TtakUpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("جستجوی دارو در تی‌تک و افزودن به انبار")
        self.setMinimumSize(1100, 600)
        vbox = QVBoxLayout(self)

        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("نام ژنریک، نام تجاری یا کد دارو در تی‌تک ...")
        self.btn_search = QPushButton("جستجو در تی‌تک")
        self.btn_search.clicked.connect(self.search_ttak)
        search_box.addWidget(self.search_input)
        search_box.addWidget(self.btn_search)
        vbox.addLayout(search_box)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "کد ژنریک", "نام ژنریک", "نام تجاری", "فرم", "دوز", "قیمت هر واحد"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        vbox.addWidget(self.table)

        # منوی راست کلیک
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # دکمه آپدیت خودکار
        self.auto_update_btn = QPushButton("آپدیت خودکار داروهای انبار با تی‌تک")
        self.auto_update_btn.clicked.connect(self.auto_update_warehouse)
        vbox.addWidget(self.auto_update_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def search_ttak(self):
        term = self.search_input.text().strip()
        if not term:
            QMessageBox.warning(self, "خطا", "برای جستجو در تی‌تک، حداقل یک واژه وارد کنید.")
            return
        self.table.setRowCount(0)
        results = fetch_data_from_ttak_api(term)
        for i, d in enumerate(results):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(d.get("generic_code", "")))
            self.table.setItem(i, 1, QTableWidgetItem(d.get("generic_name", "")))
            self.table.setItem(i, 2, QTableWidgetItem(d.get("en_brand_name", "")))
            self.table.setItem(i, 3, QTableWidgetItem(d.get("form", "")))
            self.table.setItem(i, 4, QTableWidgetItem(str(d.get("dosage", ""))))
            self.table.setItem(i, 5, QTableWidgetItem(str(d.get("price_per_unit", ""))))

    def show_context_menu(self, pos):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return
        row = indexes[0].row()
        m = QMenu(self)
        act_add = QAction("افزودن/آپدیت به انبار", self)
        m.addAction(act_add)
        act_add.triggered.connect(lambda: self.add_or_update_drug(row))
        m.exec(self.table.viewport().mapToGlobal(pos))

    def add_or_update_drug(self, row):
        code = self.table.item(row, 0).text()
        generic_name = self.table.item(row, 1).text()
        en_brand_name = self.table.item(row, 2).text()
        form = self.table.item(row, 3).text()
        dosage = self.table.item(row, 4).text()
        price = self.table.item(row, 5).text()
        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM drugs WHERE generic_code=?", (code,))
            data = cursor.fetchone()
            if not data:
                cursor.execute(
                    """INSERT INTO drugs (generic_name, en_brand_name, generic_code, form, dosage, price_per_unit, stock)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (generic_name, en_brand_name, code, form, dosage, int(price), 0)
                )
                conn.commit()
                QMessageBox.information(self, "موفق", f"دارو '{generic_name}' به انبار اضافه شد.")
            else:
                cursor.execute("UPDATE drugs SET price_per_unit=? WHERE generic_code=?", (int(price), code))
                conn.commit()
                QMessageBox.information(self, "آپدیت موفق", f"قیمت داروی '{generic_name}' در انبار به‌روزرسانی شد.")
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در افزودن یا آپدیت دارو: {e}")

    def auto_update_warehouse(self):
        try:
        # خواندن لیست داروها از فایل
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'drug_list.txt')
            if not os.path.exists(path):
               QMessageBox.warning(self, "خطا", "فایل لیست داروها (drug_list.txt) پیدا نشد!")
               return
            with open(path, "r", encoding="utf-8") as f:
                drug_names = [line.strip() for line in f if line.strip()]
            if not drug_names:
                QMessageBox.warning(self, "خطا", "فایل لیست داروها خالی است.")
                return

            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            count = 0
            for name in drug_names:
                results = fetch_data_from_ttak_api(name)
                if results:
                    d = results[0]
                    cursor.execute("SELECT id FROM drugs WHERE generic_code=?", (d.get("generic_code", ""),))
                    if not cursor.fetchone():
                        cursor.execute(
                        "INSERT INTO drugs (generic_name, en_brand_name, generic_code, form, dosage, price_per_unit, stock) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            d.get("generic_name", ""),
                            d.get("en_brand_name", ""),
                            d.get("generic_code", ""),
                            d.get("form", ""),
                            d.get("dosage", ""),
                            int(d.get("price_per_unit", 0)),
                            0
                        )
                    )
                        count += 1
            conn.commit()
            conn.close()
            QMessageBox.information(self, "اتمام", f"{count} دارو به انبار اضافه شدند. (موارد پیدا نشده رد شدند)")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"{e}")