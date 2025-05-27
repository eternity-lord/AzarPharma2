from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHeaderView
)
from persiantools.jdatetime import JalaliDate
from database.db import get_connection
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pharmacy.db')

class CashHistoriesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("صندوق کل فروش")
        self.resize(850, 500)
        self.set_azar_style()
        vbox = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["تاریخ صندوق (شمسی/میلادی)", "جمع فروش (ریال)", "شماره"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        vbox.addWidget(self.table)

        self.refresh_btn = QPushButton("رفرش صندوق کل")
        self.refresh_btn.clicked.connect(self.load_cash_histories)
        vbox.addWidget(self.refresh_btn)

        self.total_label = QLabel("جمع کل کل صندوق‌ها: ۰ ریال")
        vbox.addWidget(self.total_label)

        self.load_cash_histories()

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

    def load_cash_histories(self):
        self.table.setRowCount(0)
        total = 0
        conn = get_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT date, total_amount, id FROM cash_registers ORDER BY date DESC")
        rows = cursor.fetchall()
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(self.jalali_and_gregorian(str(row[0]))))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row[1]:,}"))
            self.table.setItem(i, 2, QTableWidgetItem(str(row[2])))
            total += int(row[1])
        self.total_label.setText(f"جمع کل صندوق‌ها: {total:,} ریال")
        conn.close()