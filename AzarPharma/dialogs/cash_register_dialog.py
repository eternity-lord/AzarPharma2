from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from database.db import get_connection
from persiantools.jdatetime import JalaliDate
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmacy.db')

class CashRegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("صندوق امروز")
        self.resize(900, 600)
        self.set_azar_style()
        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout()
        self.new_btn = QPushButton("صندوق جدید برای امروز")
        self.new_btn.clicked.connect(self.create_new_cash_register)
        hbox.addWidget(self.new_btn)
        hbox.addStretch(1)
        self.histories_btn = QPushButton("نمایش صندوق کل (F9)")
        self.histories_btn.clicked.connect(self.open_cash_histories)
        hbox.addWidget(self.histories_btn)
        vbox.addLayout(hbox)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["شماره نسخه", "جمع مبلغ", "تاریخ ثبت (شمسی/میلادی)", "وضعیت"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        vbox.addWidget(self.table)
        self.table.cellDoubleClicked.connect(self.prompt_save_to_cash)
        self.table.installEventFilter(self)

        self.refresh_btn = QPushButton("رفرش (F5)")
        self.refresh_btn.clicked.connect(self.load_cash_prescriptions)
        vbox.addWidget(self.refresh_btn)

        self.total_label = QLabel("جمع کل صندوق: ۰ ریال")
        vbox.addWidget(self.total_label)

        self.load_cash_prescriptions()

    def set_azar_style(self):
        qss_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'azarsheet.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def jalali_and_gregorian(self, date_str):
        parts = date_str.split('/')
        if len(parts) == 3:
            try:
                y, m, d = map(int, parts)
                g = JalaliDate(y, m, d).to_gregorian()
                return f"{date_str} / {g.strftime('%Y-%m-%d')}"
            except:
                pass
        return date_str

    def get_today(self):
        today = datetime.now()
        persian_date = JalaliDate(today)
        return f"{persian_date.year}/{persian_date.month:02d}/{persian_date.day:02d}"

    def create_new_cash_register(self):
        today = self.get_today()
        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
        # ذخیره مجموع فروش قبلی
            cursor.execute("SELECT id FROM cash_registers WHERE date = ?", (today,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                "SELECT SUM(p.total_price) FROM cash_prescriptions cp JOIN prescriptions p ON p.id = cp.prescription_id WHERE cp.date_added = ?", (today,))
                sales_sum = cursor.fetchone()[0] or 0
                cursor.execute("UPDATE cash_registers SET total_amount = ? WHERE date = ?", (sales_sum, today))
                conn.commit()
                QMessageBox.information(self, "ذخیره شد", f"مجموع فروش امروز ({sales_sum:,} ریال) در صندوق ثبت شد.")
        # سپس صندوق جدید امروز (اگر نبود بساز)
            else:
                cursor.execute("INSERT INTO cash_registers (date, total_amount) VALUES (?, ?)", (today, 0))
                conn.commit()
                QMessageBox.information(self, "جدید", "صندوق جدید امروز ساخته شد.")
            conn.close()
        # ***** جدول نسخه‌ها ریست میشه *****
            self.load_cash_prescriptions()  # فقط نسخه‌های جدید رو از این لحظه نمایش بده
        except Exception as e:
            QMessageBox.critical(self, "خطا", str(e))

    def load_cash_prescriptions(self):
        self.table.setRowCount(0)
        total = 0
        today = self.get_today()
        conn = get_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cash_registers WHERE date=?", (today,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            self.create_new_cash_register()
            return
        cursor.execute(
            "SELECT p.prescription_number, p.total_price, p.date, p.id FROM cash_prescriptions cp "
            "JOIN prescriptions p ON cp.prescription_id = p.id "
            "WHERE cp.date_added=?",
            (today,)
        )
        res = cursor.fetchall()
        for i, item in enumerate(res):
            self.table.insertRow(i)
            for j, val in enumerate(item[:3]):
                if j == 2:
                    self.table.setItem(i, j, QTableWidgetItem(self.jalali_and_gregorian(str(val))))
                else:
                    self.table.setItem(i, j, QTableWidgetItem(str(val)))
            status_item = QTableWidgetItem("در صندوق")
            self.table.setItem(i, 3, status_item)
            total += int(item[1])
        self.total_label.setText(f"جمع کل صندوق: {total:,} ریال")
        conn.close()

    def prompt_save_to_cash(self, row, col):
        try:
            pres_number = self.table.item(row, 0).text()
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM prescriptions WHERE prescription_number=?", (pres_number,))
            pr = cursor.fetchone()
            conn.close()
            if not pr:
                QMessageBox.warning(self, "خطا", "نسخه یافت نشد.")
                return
            prescription_id = pr[0]
            reply = QMessageBox.question(
                self, "اضافه به صندوق امروز؟",
                f"آیا نسخه {pres_number} را به صندوق امروز اضافه کنم؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.add_prescription_to_cash(prescription_id)
        except Exception as e:
            QMessageBox.critical(self, "خطا", str(e))

    def add_prescription_to_cash(self, prescription_id):
        today = self.get_today()
        try:
            conn = get_connection(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cash_prescriptions WHERE prescription_id=? AND date_added=?", (prescription_id, today))
            if cursor.fetchone():
                QMessageBox.warning(self, "خطا", "این نسخه قبلاً به صندوق امروز افزوده شده.")
                conn.close()
                return
            cursor.execute(
                "INSERT INTO cash_prescriptions (prescription_id, date_added) VALUES (?, ?)",
                (prescription_id, today)
            )
            conn.commit()
            conn.close()
            self.load_cash_prescriptions()
        except Exception as e:
            QMessageBox.critical(self, "خطا", str(e))

    def open_cash_histories(self):
        from dialogs.cash_histories_dialog import CashHistoriesDialog
        d = CashHistoriesDialog(self)
        d.exec()