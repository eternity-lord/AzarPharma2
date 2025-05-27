# dialogs/add_drug_to_invoice_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QGridLayout, 
    QMessageBox, QDateEdit # QDateEdit اضافه شد
)
from PyQt6.QtCore import Qt, QDate # QDate اضافه شد
from PyQt6.QtGui import QIntValidator # QAction حذف شد چون استفاده نشده بود
from persiantools.jdatetime import JalaliDate # برای تبدیل تاریخ

class AddDrugToInvoiceDialog(QDialog):
    def __init__(self, parent=None, item_data=None, row_index_in_invoice=None):
        super().__init__(parent)
        self.setWindowTitle("اضافه کردن / ویرایش داروی فاکتور خرید")
        self.setMinimumWidth(750) # کمی افزایش عرض برای جای دادن فیلدهای جدید
        self.setMinimumHeight(550) # کمی افزایش ارتفاع
        
        self.item_data_original = item_data if item_data else {} 
        
        # فونت کوچک برای لیبل‌ها و فیلدها
        compact_font = self.font() # گرفتن فونت پیش‌فرض
        compact_font.setPointSize(8)

        layout = QVBoxLayout(self)
        
        # بخش جستجو (فعلاً غیرفعال)
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setFont(compact_font)
        self.search_input.setPlaceholderText("کد یا نام دارو برای جستجو...")
        search_button = QPushButton("جستجو")
        search_button.setFont(compact_font)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        # layout.addLayout(search_layout) # اگر جستجو فعال نیست، نمایش داده نشود

        # جدول اطلاعات دارو
        info_grid = QGridLayout()
        info_grid.setVerticalSpacing(8)
        info_grid.setHorizontalSpacing(10)

        # ردیف اول اطلاعات اصلی دارو
        lbl_drug_name = QLabel("نام دارو:")
        lbl_drug_name.setFont(compact_font)
        self.drug_name_edit = QLineEdit(self.item_data_original.get("drug_name_snapshot", self.item_data_original.get("drug_name", "")))
        self.drug_name_edit.setFont(compact_font)
        info_grid.addWidget(lbl_drug_name, 0, 0, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.drug_name_edit, 0, 1)
        
        lbl_generic_code = QLabel("کد ژنریک:")
        lbl_generic_code.setFont(compact_font)
        self.generic_code_edit = QLineEdit(self.item_data_original.get("generic_code", ""))
        self.generic_code_edit.setFont(compact_font)
        info_grid.addWidget(lbl_generic_code, 0, 2, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.generic_code_edit, 0, 3)

        # ردیف دوم اطلاعات تکمیلی دارو
        lbl_form = QLabel("شکل دارو:")
        lbl_form.setFont(compact_font)
        self.form_edit = QLineEdit(self.item_data_original.get("form", ""))
        self.form_edit.setFont(compact_font)
        info_grid.addWidget(lbl_form, 1, 0, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.form_edit, 1, 1)
        
        lbl_dosage = QLabel("دوز دارو:")
        lbl_dosage.setFont(compact_font)
        self.dosage_edit = QLineEdit(self.item_data_original.get("dosage", ""))
        self.dosage_edit.setFont(compact_font)
        info_grid.addWidget(lbl_dosage, 1, 2, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.dosage_edit, 1, 3)

        # ردیف سوم: تعداد
        lbl_package_count = QLabel("تعداد بسته:")
        lbl_package_count.setFont(compact_font)
        self.package_count_edit = QLineEdit(str(self.item_data_original.get("package_count", "1")))
        self.package_count_edit.setFont(compact_font)
        self.package_count_edit.setValidator(QIntValidator(1, 10000))
        info_grid.addWidget(lbl_package_count, 2, 0, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.package_count_edit, 2, 1)
        
        lbl_qty_per_package = QLabel("تعداد در بسته:")
        lbl_qty_per_package.setFont(compact_font)
        self.qty_per_package_edit = QLineEdit(str(self.item_data_original.get("quantity_in_package", "1")))
        self.qty_per_package_edit.setFont(compact_font)
        self.qty_per_package_edit.setValidator(QIntValidator(1, 1000))
        info_grid.addWidget(lbl_qty_per_package, 2, 2, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.qty_per_package_edit, 2, 3)

        # ردیف چهارم: قیمت و مالیات
        lbl_purchase_price = QLabel("قیمت خرید بسته:")
        lbl_purchase_price.setFont(compact_font)
        self.purchase_price_edit = QLineEdit(str(self.item_data_original.get("purchase_price_per_package", "0")))
        self.purchase_price_edit.setFont(compact_font)
        # افزودن Validator برای قیمت (عدد اعشاری یا صحیح)
        info_grid.addWidget(lbl_purchase_price, 3, 0, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.purchase_price_edit, 3, 1)
        
        lbl_vat = QLabel("مالیات (%):")
        lbl_vat.setFont(compact_font)
        self.vat_edit = QLineEdit(str(self.item_data_original.get("item_vat", "9"))) # پیش‌فرض 9 درصد
        self.vat_edit.setFont(compact_font)
        # افزودن Validator برای درصد مالیات
        info_grid.addWidget(lbl_vat, 3, 2, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.vat_edit, 3, 3)

        # --- ردیف پنجم: تاریخ انقضاء ---
        lbl_expiry_gregorian = QLabel("تاریخ انقضا (میلادی):")
        lbl_expiry_gregorian.setFont(compact_font)
        self.expiry_date_gregorian_edit = QDateEdit(QDate.currentDate().addYears(1)) # پیش‌فرض یک سال بعد
        self.expiry_date_gregorian_edit.setFont(compact_font)
        self.expiry_date_gregorian_edit.setCalendarPopup(True)
        self.expiry_date_gregorian_edit.setDisplayFormat("yyyy/MM/dd")
        info_grid.addWidget(lbl_expiry_gregorian, 4, 0, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.expiry_date_gregorian_edit, 4, 1)

        self.expiry_date_jalali_label = QLabel("") # برای نمایش تاریخ شمسی متناظر
        self.expiry_date_jalali_label.setFont(compact_font)
        info_grid.addWidget(self.expiry_date_jalali_label, 4, 2, 1, 2, Qt.AlignmentFlag.AlignLeft) # ادغام دو ستون برای نمایش

        # اتصال سیگنال برای به‌روزرسانی تاریخ شمسی با تغییر تاریخ میلادی
        self.expiry_date_gregorian_edit.dateChanged.connect(self._update_jalali_expiry_display)
        
        # ردیف ششم: شماره بچ
        lbl_batch_number = QLabel("شماره بچ (Batch No):")
        lbl_batch_number.setFont(compact_font)
        self.batch_number_edit = QLineEdit(self.item_data_original.get("batch_number", ""))
        self.batch_number_edit.setFont(compact_font)
        info_grid.addWidget(lbl_batch_number, 5,0, Qt.AlignmentFlag.AlignRight)
        info_grid.addWidget(self.batch_number_edit, 5,1, 1, 3) # ادغام ستون برای فیلد طولانی‌تر


        layout.addLayout(info_grid)
        layout.addStretch(1) # اضافه کردن فضای خالی در انتها برای فشار دادن ویجت‌ها به بالا
        
        # بارگذاری تاریخ انقضا اگر در حالت ویرایش هستیم
        if self.is_editing():
            gregorian_date_str = self.item_data_original.get("expiry_date_gregorian")
            if gregorian_date_str:
                try:
                    year, month, day = map(int, gregorian_date_str.split('/'))
                    self.expiry_date_gregorian_edit.setDate(QDate(year, month, day))
                except ValueError:
                    print(f"Invalid Gregorian expiry date format in item_data: {gregorian_date_str}")
        self._update_jalali_expiry_display() # به‌روزرسانی اولیه نمایش تاریخ شمسی


        # دکمه‌ها
        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("تأیید (F2)")
        self.confirm_button.setFont(compact_font)
        self.confirm_button.setDefault(True)
        self.confirm_button.clicked.connect(self.confirm_and_return)
        
        self.cancel_button = QPushButton("انصراف (Esc)")
        self.cancel_button.setFont(compact_font)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def is_editing(self):
        """بررسی می‌کند آیا دیالوگ در حالت ویرایش یک آیتم موجود است یا خیر."""
        # اگر generic_code از داده‌های اولیه وجود داشته باشد، یعنی در حال ویرایش هستیم
        # یا می‌توان یک فلگ جداگانه در item_data برای این منظور در نظر گرفت
        return bool(self.item_data_original.get("generic_code"))


    def _update_jalali_expiry_display(self):
        """تاریخ شمسی را بر اساس تاریخ میلادی انتخاب شده به‌روز می‌کند."""
        try:
            gregorian_date = self.expiry_date_gregorian_edit.date().toPyDate()
            jalali_equiv = JalaliDate.to_jalali(gregorian_date)
            self.expiry_date_jalali_label.setText(f"شمسی: {jalali_equiv.year}/{jalali_equiv.month:02d}/{jalali_equiv.day:02d}")
        except Exception as e:
            self.expiry_date_jalali_label.setText("خطا در تبدیل تاریخ")
            print(f"Error converting to Jalali: {e}")


    def confirm_and_return(self):
        # اعتبارسنجی فیلدها قبل از تایید
        if not self.generic_code_edit.text().strip():
            QMessageBox.warning(self, "خطای ورودی", "کد ژنریک نمی‌تواند خالی باشد.")
            self.generic_code_edit.setFocus()
            return
        if not self.drug_name_edit.text().strip():
            QMessageBox.warning(self, "خطای ورودی", "نام دارو نمی‌تواند خالی باشد.")
            self.drug_name_edit.setFocus()
            return
        # اعتبارسنجی‌های دیگر (مثلا برای اعداد) در متد get_data انجام می‌شود
        
        # اگر داده‌ها معتبر بودند، accept کن
        if self.get_data(): # get_data خودش در صورت خطا None برمی‌گرداند
            self.accept() 

    def get_data(self):
        try:
            package_count = int(self.package_count_edit.text() or "1")
            if package_count <= 0: raise ValueError("تعداد بسته باید مثبت باشد")
            qty_per_package = int(self.qty_per_package_edit.text() or "1")
            if qty_per_package <= 0: raise ValueError("تعداد در بسته باید مثبت باشد")
            
            purchase_price_str = self.purchase_price_edit.text().replace(',', '').strip() # حذف جداکننده هزارگان
            purchase_price = float(purchase_price_str or "0")
            if purchase_price < 0: raise ValueError("قیمت خرید نمی‌تواند منفی باشد")

            item_vat_str = self.vat_edit.text().strip()
            item_vat = float(item_vat_str or "0") # پیش‌فرض 0 اگر خالی بود، قبلا 9 بود
            if item_vat < 0: raise ValueError("مالیات نمی‌تواند منفی باشد")

            # گرفتن تاریخ انقضا
            expiry_date_gregorian_qdate = self.expiry_date_gregorian_edit.date()
            expiry_date_gregorian_str = expiry_date_gregorian_qdate.toString("yyyy/MM/dd")
            
            py_gregorian_date = expiry_date_gregorian_qdate.toPyDate()
            jalali_equiv = JalaliDate.to_jalali(py_gregorian_date)
            expiry_date_jalali_str = f"{jalali_equiv.year}/{jalali_equiv.month:02d}/{jalali_equiv.day:02d}"
            
            # فرض سود اولیه (این بخش نیاز به بازنگری و تعریف دقیق‌تر منطق سود دارد)
            # این درصد سود و قیمت فروش باید از تنظیمات یا ورودی کاربر بیاید.
            # فعلا یک محاسبه ساده انجام می‌دهیم.
            profit_margin_default = 0.20 # 20 درصد سود پیش‌فرض
            sale_price_calculated = purchase_price * (1 + profit_margin_default)


            return {
                # اطلاعات قبلی
                "drug_name_snapshot": self.drug_name_edit.text().strip(),
                "generic_code": self.generic_code_edit.text().strip(),
                "brand_code": self.generic_code_edit.text().strip(), # فعلا کد برند همان کد ژنریک
                "form": self.form_edit.text().strip(),
                "dosage": self.dosage_edit.text().strip(),
                "package_count": package_count,
                "quantity_in_package": qty_per_package,
                "unit_count": package_count * qty_per_package,
                "purchase_price_per_package": purchase_price,
                "item_vat": item_vat,
                "item_discount_rial": self.item_data_original.get("item_discount_rial", 0), # تخفیف فعلا ثابت
                
                # فیلدهای جدید
                "expiry_date_gregorian": expiry_date_gregorian_str,
                "expiry_date_jalali": expiry_date_jalali_str,
                "batch_number": self.batch_number_edit.text().strip(),
                
                # قیمت فروش و سود (نیاز به منطق دقیق‌تر برای محاسبه دارد)
                "sale_price_per_package": self.item_data_original.get("sale_price_per_package", sale_price_calculated),
                "profit_percentage": self.item_data_original.get("profit_percentage", profit_margin_default * 100),
                
                # فیلدهای مربوط به انبار (اگر در این دیالوگ تنظیم نمی‌شوند، مقادیر پیش‌فرض یا قبلی)
                "main_warehouse_location": self.item_data_original.get("main_warehouse_location", ""),
                "main_warehouse_min_stock": self.item_data_original.get("main_warehouse_min_stock", 0),
                "main_warehouse_max_stock": self.item_data_original.get("main_warehouse_max_stock", 0),
                "main_shelf_location": self.item_data_original.get("main_shelf_location", ""),
                "main_shelf_min_stock": self.item_data_original.get("main_shelf_min_stock", 0),
                "main_shelf_max_stock": self.item_data_original.get("main_shelf_max_stock", 0),

                # فیلدهای اضافی که در نسخه قبلی شما بود (برای سازگاری با ساختار داده قبلی)
                "drug_name": self.drug_name_edit.text().strip(), # تکراری با drug_name_snapshot
                "purchase_price": purchase_price, # تکراری با purchase_price_per_package
                "sale_price": self.item_data_original.get("sale_price_per_package", sale_price_calculated), # تکراری
            }
        except ValueError as ve: # برای خطاهای تبدیل نوع یا مقادیر نامعتبر
            QMessageBox.warning(self, "خطای ورودی", f"لطفاً مقادیر را به درستی وارد کنید:\n{ve}")
            return None
        except Exception as e: # برای سایر خطاهای پیش‌بینی نشده
            QMessageBox.critical(self, "خطای ناشناخته", f"یک خطای پیش‌بینی نشده رخ داد: {e}")
            return None