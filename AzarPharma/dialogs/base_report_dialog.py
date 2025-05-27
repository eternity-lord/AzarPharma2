# ui/dialogs/base_report_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import traceback

class ReportWorker(QThread):
    """worker thread برای گزارش‌گیری بدون فریز UI"""
    data_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, query_func, *args):
        super().__init__()
        self.query_func = query_func
        self.args = args
    
    def run(self):
        try:
            data = self.query_func(*self.args)
            self.data_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class BaseReportDialog(QDialog):
    """کلاس پایه برای همه گزارشات"""
    
    def __init__(self, parent=None, title="گزارش", min_size=(800, 600)):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(*min_size)
        
        self.worker = None
        self._setup_base_ui()
    
    def _setup_base_ui(self):
        """تنظیمات UI پایه"""
        self.main_layout = QVBoxLayout(self)
        
        # فونت یکپارچه
        self.compact_font = QFont()
        self.compact_font.setPointSize(9)
        
        self.header_font = QFont()
        self.header_font.setPointSize(10)
        self.header_font.setBold(True)
        
        # استایل یکپارچه
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                font-family: 'B Nazanin', 'Tahoma';
            }
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTableWidget {
                alternate-background-color: #f8f8f8;
                gridline-color: #ddd;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
    
    def create_filter_frame(self):
        """ایجاد فریم فیلترها"""
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.Shape.StyledPanel)
        return filter_frame
    
    def create_table(self, headers):
        """ایجاد جدول گزارش"""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        
        # تنظیم عرض ستون‌ها
        header = table.horizontalHeader()
        for i in range(len(headers)):
            if i == 0:  # ستون اول معمولاً کوچکتر
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            elif i == len(headers) - 1:  # ستون آخر کشیده شود
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        
        return table
    
    def create_progress_bar(self):
        """نوار پیشرفت برای لودینگ"""
        progress = QProgressBar()
        progress.setRange(0, 0)  # حالت نامحدود
        progress.hide()
        return progress
    
    def show_loading(self, show=True):
        """نمایش حالت لودینگ"""
        if hasattr(self, 'progress_bar'):
            if show:
                self.progress_bar.show()
            else:
                self.progress_bar.hide()
    
    def populate_table(self, table, data, formatters=None):
        """پر کردن جدول با داده‌ها"""
        table.setRowCount(0)
        
        if not data:
            return
        
        table.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                # اعمال فرمت کننده در صورت وجود
                if formatters and col_idx in formatters:
                    value = formatters[col_idx](value)
                
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_idx, col_idx, item)
    
    def show_message(self, title, message, msg_type="info"):
        """نمایش پیام"""
        if msg_type == "error":
            QMessageBox.critical(self, title, message)
        elif msg_type == "warning":
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def export_to_csv(self, table, filename):
        """خروجی CSV"""
        try:
            import csv
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "ذخیره فایل", filename, "CSV Files (*.csv)"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    
                    # نوشتن هدرها
                    headers = []
                    for col in range(table.columnCount()):
                        headers.append(table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # نوشتن داده‌ها
                    for row in range(table.rowCount()):
                        row_data = []
                        for col in range(table.columnCount()):
                            item = table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                self.show_message("موفقیت", f"گزارش در {file_path} ذخیره شد")
                
        except Exception as e:
            self.show_message("خطا", f"خطا در ذخیره فایل: {e}", "error")
