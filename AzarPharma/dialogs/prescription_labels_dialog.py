# dialogs/prescription_labels_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser, 
    QSizePolicy, QMessageBox # QMessageBox اضافه شد
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# --- ایمپورت‌های جدید برای قابلیت چاپ ---
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
# ------------------------------------

# تلاش برای ایمپورت نام داروخانه از فایل کانفیگ (اختیاری)
PHARMACY_NAME_DEFAULT = "داروخانه آذر فارما"
try:
    from config import COMPANY_NAME 
    PHARMACY_NAME = COMPANY_NAME if COMPANY_NAME else PHARMACY_NAME_DEFAULT
except ImportError:
    PHARMACY_NAME = PHARMACY_NAME_DEFAULT


class PrescriptionLabelsDialog(QDialog):
    def __init__(self, prescription_items, patient_name, doctor_name, prescription_date, 
                 pharmacy_name=PHARMACY_NAME, parent=None):
        super().__init__(parent)
        self.setWindowTitle("پیش‌نمایش و چاپ لیبل‌های داروی نسخه") # عنوان کمی تغییر کرد
        self.setMinimumSize(450, 500)

        self.prescription_items = prescription_items
        self.patient_name = patient_name
        self.doctor_name = doctor_name if doctor_name else "نامشخص"
        self.prescription_date = prescription_date
        self.pharmacy_name = pharmacy_name

        self._setup_ui()
        self._generate_labels()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        compact_font = QFont(); compact_font.setPointSize(8)

        self.text_browser = QTextBrowser()
        self.text_browser.setReadOnly(True)
        # فونت و جهت متن برای QTextBrowser (برای نمایش بهتر فارسی و انگلیسی کنار هم)
        # text_browser_font = QFont("Tahoma", 9)
        # self.text_browser.setFont(text_browser_font)
        # self.text_browser.setLayoutDirection(Qt.LayoutDirection.RightToLeft) # اگر محتوای HTML خودش جهت ندارد
        main_layout.addWidget(self.text_browser, 1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        self.print_button = QPushButton("چاپ لیبل‌ها (Ctrl+P)") 
        self.print_button.setFont(compact_font)
        self.print_button.setEnabled(True) # <--- دکمه چاپ فعال شد
        self.print_button.clicked.connect(self._handle_print) # <--- اتصال به متد چاپ
        self.print_button.setShortcut("Ctrl+P") # افزودن میانبر Ctrl+P
        buttons_layout.addWidget(self.print_button)

        self.close_button = QPushButton("بستن (Esc)")
        self.close_button.setFont(compact_font)
        self.close_button.clicked.connect(self.accept)
        self.close_button.setShortcut("Esc") # افزودن میانبر Esc
        buttons_layout.addWidget(self.close_button)
        
        main_layout.addLayout(buttons_layout)

    def _generate_labels(self):
        # این متد بدون تغییر از مرحله قبل باقی می‌ماند
        # (برای خوانایی، کد آن را دوباره اینجا تکرار نمی‌کنم، فرض بر این است که کد مرحله قبل را دارید)
        # فقط مطمئن شوید که HTML تولید شده برای چاپ مناسب است.
        all_labels_html = "<html><head><meta charset='UTF-8'></head>" # افزودن UTF-8 برای کاراکترهای فارسی
        all_labels_html += "<body style='font-family: Tahoma, Arial, sans-serif; font-size: 9pt; direction: rtl;'>" # تنظیم جهت راست به چپ برای کل بدنه

        for index, item in enumerate(self.prescription_items):
            if not item.get("generic_code"): 
                continue

            drug_name = item.get("en_brand_name") or item.get("generic_name", "نام دارو نامشخص")
            dosage_form = f"{item.get('dosage', '')} {item.get('form', '')}".strip()
            usage = item.get("usage_instructions", "طبق دستور پزشک")
            quantity = item.get("quantity", "-")

            label_html = f"""
            <div style='border: 1px solid #888; margin-bottom: 10px; padding: 8px; page-break-inside: avoid; width: 95%;'>
                <p style='text-align: center; font-weight: bold; font-size: 10pt; margin: 2px 0;'>{self.pharmacy_name}</p>
                <hr style='border: none; border-top: 1px dashed #bbb; margin: 4px 0;'>
                <table width='100%' style='font-size: 8.5pt;'>
                    <tr><td width='30%' style='text-align: right; padding-left: 5px;'><b>بیمار:</b></td><td>{self.patient_name}</td></tr>
                    <tr><td style='text-align: right; padding-left: 5px;'><b>نام دارو:</b></td><td>{drug_name}</td></tr>
                    <tr><td style='text-align: right; padding-left: 5px;'><b>شکل و دوز:</b></td><td>{dosage_form}</td></tr>
                    <tr><td style='text-align: right; padding-left: 5px; vertical-align:top;'><b>دستور مصرف:</b></td><td>{usage if usage else 'طبق دستور پزشک'}</td></tr>
                    <tr><td style='text-align: right; padding-left: 5px;'><b>تعداد:</b></td><td>{quantity} عدد</td></tr>
                </table>
                <p style='font-size: 7.5pt; text-align: left; margin-top: 5px;'>پزشک: {self.doctor_name} &nbsp;&nbsp; تاریخ: {self.prescription_date}</p>
            </div>
            """
            all_labels_html += label_html
            # اگر می‌خواهید هر لیبل در صفحه جدیدی چاپ شود (برای پرینترهای رولی یا A4 که هر لیبل جداست)
            all_labels_html += "<div style='page-break-after:always;'></div>"


        all_labels_html += "</body></html>"
        self.text_browser.setHtml(all_labels_html)

    def _handle_print(self):
        """محتوای QTextBrowser را به پرینتر ارسال می‌کند."""
        print("--- DEBUG: _handle_print called ---")
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        # می‌توانید تنظیمات پیش‌فرض پرینتر را اینجا تغییر دهید، مثلا:
        # printer.setPageSize(QPageSize(QPageSize.PageSizeId.A7)) # اگر لیبل‌های شما اندازه A7 دارند
        # printer.setOrientation(QPrinter.Orientation.Portrait)
        # printer.setOutputFormat(QPrinter.OutputFormat.NativeFormat) # یا PdfFormat برای ذخیره به عنوان PDF

        print_dialog = QPrintDialog(printer, self)
        print_dialog.setWindowTitle("انتخاب پرینتر و تنظیمات چاپ لیبل")

        if print_dialog.exec() == QDialog.DialogCode.Accepted:
            # اگر کاربر دکمه OK را در دیالوگ چاپ زد
            print("--- DEBUG: Print dialog accepted. Sending document to printer... ---")
            self.text_browser.document().print_(printer) # ارسال سند QTextBrowser به پرینتر
            QMessageBox.information(self, "چاپ لیبل", "لیبل(ها) به پرینتر ارسال شد.")
        else:
            print("--- DEBUG: Print dialog cancelled by user. ---")
            QMessageBox.information(self, "چاپ لیبل", "عملیات چاپ لغو شد.")