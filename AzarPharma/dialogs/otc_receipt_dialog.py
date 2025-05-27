# dialogs/otc_receipt_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser, 
    QSizePolicy, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog # برای چاپ

# تلاش برای ایمپورت اطلاعات داروخانه از فایل کانفیگ
PHARMACY_NAME_DEFAULT = "داروخانه آذر فارما"
PHARMACY_ADDRESS_DEFAULT = "آدرس داروخانه شما"
PHARMACY_PHONE_DEFAULT = "تلفن داروخانه شما"

try:
    from config import COMPANY_NAME, PHARMACY_ADDRESS, PHARMACY_PHONE
    PHARMACY_NAME = COMPANY_NAME if COMPANY_NAME else PHARMACY_NAME_DEFAULT
    # فرض می‌کنیم این متغیرها را به config.py اضافه خواهید کرد
    PHARMACY_ADDRESS = PHARMACY_ADDRESS if PHARMACY_ADDRESS else PHARMACY_ADDRESS_DEFAULT
    PHARMACY_PHONE = PHARMACY_PHONE if PHARMACY_PHONE else PHARMACY_PHONE_DEFAULT
except ImportError:
    PHARMACY_NAME = PHARMACY_NAME_DEFAULT
    PHARMACY_ADDRESS = PHARMACY_ADDRESS_DEFAULT
    PHARMACY_PHONE = PHARMACY_PHONE_DEFAULT
except NameError: # اگر متغیرها در config.py تعریف نشده باشند
    PHARMACY_ADDRESS = PHARMACY_ADDRESS_DEFAULT
    PHARMACY_PHONE = PHARMACY_PHONE_DEFAULT
    # PHARMACY_NAME ممکن است از قبل به درستی از COMPANY_NAME خوانده شده باشد


class OTCReceiptDialog(QDialog):
    def __init__(self, sale_details, sale_items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"رسید فروش OTC - شماره: {sale_details.get('id', 'N/A')}")
        self.setMinimumSize(400, 500) # اندازه مناسب برای پیش‌نمایش رسید

        self.sale_details = sale_details
        self.sale_items = sale_items # لیستی از دیکشنری‌ها برای اقلام

        self._setup_ui()
        self._generate_receipt_html()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        # فونت‌ها را می‌توان بر اساس نیاز تنظیم کرد
        # compact_font = QFont(); compact_font.setPointSize(8) 
        default_font = QApplication.font() # استفاده از فونت پیش‌فرض برنامه
        default_font.setPointSize(9)


        self.text_browser = QTextBrowser()
        self.text_browser.setReadOnly(True)
        # self.text_browser.setFont(default_font) # فونت برای محتوای رسید
        main_layout.addWidget(self.text_browser, 1)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        self.print_button = QPushButton("چاپ رسید (Ctrl+P)") 
        self.print_button.setFont(default_font)
        self.print_button.clicked.connect(self._handle_print)
        self.print_button.setShortcut("Ctrl+P")
        buttons_layout.addWidget(self.print_button)

        self.close_button = QPushButton("بستن (Esc)")
        self.close_button.setFont(default_font)
        self.close_button.clicked.connect(self.accept)
        self.close_button.setShortcut("Esc")
        buttons_layout.addWidget(self.close_button)
        
        main_layout.addLayout(buttons_layout)

    def _generate_receipt_html(self):
        # استایل CSS برای ظاهر بهتر رسید (می‌تواند در یک فایل جداگانه هم باشد)
        # اندازه‌ها و فونت‌ها برای چاپ روی کاغذهای حرارتی کوچک تنظیم شده‌اند
        html_style = """
        <style>
            body { 
                font-family: 'Tahoma', 'Arial', sans-serif; 
                font-size: 8pt; 
                direction: rtl; 
                margin: 0; padding: 5px; 
                width: 280px; /* عرض تقریبی برای کاغذ حرارتی رول ۸ سانتی */
            }
            .header { text-align: center; margin-bottom: 8px; }
            .header h3 { margin: 2px 0; font-size: 10pt; }
            .header p { margin: 1px 0; font-size: 7pt; }
            .info { margin-bottom: 8px; font-size: 7.5pt; border-top: 1px dashed #777; border-bottom: 1px dashed #777; padding: 3px 0;}
            .info p { margin: 2px 0; }
            table.items { width: 100%; border-collapse: collapse; font-size: 7.5pt; }
            table.items th { text-align: right; border-bottom: 1px solid #333; padding: 2px; font-weight:bold; }
            table.items td { padding: 2px; vertical-align: top; }
            .total-row td { border-top: 1px dashed #777; font-weight: bold; padding-top: 3px;}
            .footer { text-align: center; font-size: 7pt; margin-top: 10px; }
        </style>
        """

        receipt_html = f"<html><head><meta charset='UTF-8'>{html_style}</head><body>"
        
        # --- بخش سربرگ ---
        receipt_html += "<div class='header'>"
        receipt_html += f"<h3>{PHARMACY_NAME}</h3>"
        if PHARMACY_ADDRESS and PHARMACY_ADDRESS != PHARMACY_ADDRESS_DEFAULT : receipt_html += f"<p>{PHARMACY_ADDRESS}</p>"
        if PHARMACY_PHONE and PHARMACY_PHONE != PHARMACY_PHONE_DEFAULT : receipt_html += f"<p>تلفن: {PHARMACY_PHONE}</p>"
        receipt_html += "</div>"

        # --- اطلاعات فروش ---
        receipt_html += "<div class='info'>"
        receipt_html += f"<p>شماره فاکتور: {self.sale_details.get('id', 'N/A')}</p>"
        sale_date_formatted = self.sale_details.get('sale_date', '')
        # اگر نیاز به تبدیل تاریخ به شمسی دارید، اینجا انجام دهید
        receipt_html += f"<p>تاریخ: {sale_date_formatted} &nbsp;&nbsp; زمان: {self.sale_details.get('sale_time', '')}</p>"
        receipt_html += "</div>"

        # --- جدول اقلام ---
        receipt_html += "<table class='items'>"
        receipt_html += "<thead><tr><th>شرح کالا</th><th>تعداد</th><th>فی</th><th>جمع</th></tr></thead>"
        receipt_html += "<tbody>"
        sub_total = 0
        for item in self.sale_items:
            item_name = item.get('item_name_snapshot', item.get('name', 'کالا'))
            quantity = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0)
            total_item_price = item.get('total_price', quantity * unit_price) # محاسبه مجدد برای اطمینان
            sub_total += total_item_price
            receipt_html += f"""
            <tr>
                <td>{item_name}</td>
                <td style='text-align:center;'>{quantity}</td>
                <td style='text-align:left;'>{unit_price:,.0f}</td>
                <td style='text-align:left;'>{total_item_price:,.0f}</td>
            </tr>
            """
        receipt_html += "</tbody>"
        
        # --- بخش جمع کل و پرداخت ---
        receipt_html += "<tfoot>"
        # اگر تخفیف دارید
        discount = self.sale_details.get('discount_amount', 0)
        if discount > 0:
            receipt_html += f"<tr class='total-row'><td colspan='3' style='text-align:right;'>جمع کل اقلام:</td><td style='text-align:left;'>{sub_total:,.0f}</td></tr>"
            receipt_html += f"<tr><td colspan='3' style='text-align:right;'>تخفیف:</td><td style='text-align:left;'>{discount:,.0f}</td></tr>"
        
        final_amount = self.sale_details.get('final_amount', sub_total - discount)
        receipt_html += f"<tr class='total-row'><td colspan='3' style='text-align:right;'>مبلغ قابل پرداخت:</td><td style='text-align:left;'>{final_amount:,.0f}</td></tr>"
        
        payment_method = self.sale_details.get('payment_method', 'نقدی')
        receipt_html += f"<tr><td colspan='3' style='text-align:right;'>روش پرداخت:</td><td style='text-align:left;'>{payment_method}</td></tr>"
        receipt_html += "</tfoot></table>"

        # --- پاورقی ---
        receipt_html += "<div class='footer'><p>از خرید شما متشکریم!</p></div>"
        receipt_html += "</body></html>"
        
        self.text_browser.setHtml(receipt_html)

    def _handle_print(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        # برای پرینترهای حرارتی، تنظیمات خاصی ممکن است لازم باشد
        # printer.setPageSize(QPrinter.PageSize.Custom) # اگر اندازه کاغذ سفارشی است
        # printer.setPaperSize(QSizeF(72, 200), QPrinter.Unit.Millimeter) # مثال: عرض ۷۲ میلیمتر، طول ۲۰۰ میلیمتر
        # printer.setFullPage(True)
        # printer.setPageMargins(QMarginsF(2,2,2,2), QPageLayout.Unit.Millimeter)


        print_dialog = QPrintDialog(printer, self)
        print_dialog.setWindowTitle("چاپ رسید فروش OTC")
        if print_dialog.exec() == QDialog.DialogCode.Accepted:
            self.text_browser.document().print_(printer)
            QMessageBox.information(self, "چاپ رسید", "رسید به پرینتر ارسال شد.")
        else:
            QMessageBox.information(self, "چاپ رسید", "عملیات چاپ لغو شد.")