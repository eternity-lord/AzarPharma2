# dialogs/otc_sale_dialog.py

import sqlite3
import os
from datetime import datetime
import traceback # برای نمایش جزئیات خطا

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog,
    QSizePolicy,QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont # QFont برای تنظیم فونت لازم است
from PyQt6.QtGui import QFont, QDoubleValidator, QIntValidator, QKeySequence, QShortcut 

# ایمپورت دیالوگ جستجوی دارو
# مطمئن شوید این دیالوگ 'id' دارو را هم برمی‌گرداند
from dialogs.drug_search_dialog import DrugSearchDialog 

# --- استراتژی ایمپورت برای DB_PATH و get_connection ---
# این بخش برای حل مشکل ایمپورت و NameError است
CENTRAL_IMPORT_SUCCESSFUL = False
DB_PATH_FALLBACK = None # برای استفاده در تابع fallback
try:
    from config import DB_PATH as CENTRAL_DB_PATH # نامگذاری مجزا برای جلوگیری از تداخل
    from database.db import get_connection as central_get_connection
    # print("OTC_SALE_DIALOG: Using central DB_PATH and get_connection.") # برای دیباگ
    CENTRAL_IMPORT_SUCCESSFUL = True
except ImportError:
    print("OTC_SALE_DIALOG: Central import of DB_PATH or get_connection failed. Using local fallback.")
    # تعریف مقادیر fallback فقط اگر ایمپورت مرکزی ناموفق بود
    BASE_DIR_OTC_LOCAL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH_FALLBACK = os.path.join(BASE_DIR_OTC_LOCAL, 'pharmacy.db')

    def get_connection_otc_fallback_local(): # نام کاملاً منحصر به فرد برای تابع fallback
        # print(f"OTC_SALE_DIALOG: Using local fallback DB connection: {DB_PATH_FALLBACK}")
        db_dir = os.path.dirname(DB_PATH_FALLBACK)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(DB_PATH_FALLBACK, timeout=10)
        conn.row_factory = sqlite3.Row 
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

# تعیین اینکه کدام DB_PATH و تابع اتصال استفاده شود
if CENTRAL_IMPORT_SUCCESSFUL:
    current_DB_PATH_for_otc = CENTRAL_DB_PATH
    get_current_otc_db_connection = lambda: central_get_connection(current_DB_PATH_for_otc)
else:
    current_DB_PATH_for_otc = DB_PATH_FALLBACK
    get_current_otc_db_connection = get_connection_otc_fallback_local
# ---------------------------------------------------------


class OTCSaleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ثبت فروش آزاد (OTC)")
        self.setMinimumSize(700, 550)
        self.sale_items_data = [] 
        self._setup_ui()
        self._update_grand_total()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        compact_font = QFont(); compact_font.setPointSize(8)
        header_font = QFont(); header_font.setPointSize(9); header_font.setBold(True)
        total_font = QFont(); total_font.setPointSize(10); total_font.setBold(True)


        
        add_item_layout = QHBoxLayout()
        self.add_item_button = QPushButton("افزودن کالا/دارو (F3)")
        self.add_item_button.setFont(compact_font)
        self.add_item_button.clicked.connect(self._open_drug_search_to_add_item)
        add_item_layout.addWidget(self.add_item_button)
        add_item_layout.addStretch(1)
        main_layout.addLayout(add_item_layout)

        self.sale_items_table = QTableWidget()
        self.sale_items_table.setColumnCount(6) 
        self.sale_items_table.setHorizontalHeaderLabels(["کد کالا", "نام کالا/دارو", "تعداد", "قیمت واحد", "جمع کل ردیف", "عملیات"])
        self.sale_items_table.setFont(compact_font)
        self.sale_items_table.horizontalHeader().setFont(compact_font)
        self.sale_items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sale_items_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        header = self.sale_items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive); header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)    
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive); header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive); header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)      
        self.sale_items_table.setColumnWidth(0, 100); self.sale_items_table.setColumnWidth(2, 70); self.sale_items_table.setColumnWidth(3, 100)
        self.sale_items_table.setColumnWidth(4, 110); self.sale_items_table.setColumnWidth(5, 60)
        self.sale_items_table.cellChanged.connect(self._on_table_cell_changed)
        main_layout.addWidget(self.sale_items_table, 1)

        summary_layout = QHBoxLayout()
        summary_layout.addStretch(1)
        lbl_grand_total = QLabel("جمع کل قابل پرداخت:")
        lbl_grand_total.setFont(header_font)
        summary_layout.addWidget(lbl_grand_total)
        self.grand_total_display_label = QLabel("۰ ریال")
        self.grand_total_display_label.setFont(total_font)
        self.grand_total_display_label.setStyleSheet("color: green; padding: 3px;")
        self.grand_total_display_label.setMinimumWidth(150)
        self.grand_total_display_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        summary_layout.addWidget(self.grand_total_display_label)
        main_layout.addLayout(summary_layout)

        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch(1)
        self.complete_sale_button = QPushButton("تکمیل فروش و پرداخت (F2)")
        self.complete_sale_button.setFont(compact_font)
        self.complete_sale_button.setDefault(True)
        self.complete_sale_button.clicked.connect(self._process_sale)
        self.cancel_button = QPushButton("انصراف (Esc)")
        self.cancel_button.setFont(compact_font)
        self.cancel_button.clicked.connect(self.reject)
        action_buttons_layout.addWidget(self.complete_sale_button)
        action_buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(action_buttons_layout)
        # ... (کد دکمه‌های complete_sale_button و cancel_button) ...
        action_buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(action_buttons_layout) # این خط باید بعد از افزودن میانبر باشد یا قبل از آن، فرقی نمی‌کند

        # --- افزودن میانبر F8 برای حذف ردیف ---
        self.delete_row_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F8), self)
        self.delete_row_shortcut.activated.connect(self._delete_selected_sale_item_shortcut)
        # ------------------------------------

    def _open_drug_search_to_add_item(self):
        # این دیالوگ باید DB_PATH را از current_DB_PATH_for_otc بگیرد اگر خودش از config ایمپورت نمی‌کند
        # برای سادگی، فرض می‌کنیم DrugSearchDialog خودش مدیریت DB_PATH را دارد.
        dialog = DrugSearchDialog(self) 
        if dialog.exec():
            drug_info = dialog.get_selected_drug() 
            if drug_info and drug_info.get("generic_code"): 
                quantity, ok = QInputDialog.getInt(self, "ورود تعداد", 
                                                   f"تعداد برای '{drug_info.get('en_brand_name', drug_info.get('generic_name', ''))}':", 
                                                   1, 1, 1000, 1)
                if ok and quantity > 0:
                    item = {
                        "drug_id": drug_info.get("id"), 
                        "generic_code": drug_info.get("generic_code"),
                        "name": drug_info.get("en_brand_name", drug_info.get("generic_name")),
                        "quantity": quantity,
                        "unit_price": float(drug_info.get("price", 0)),
                        "total_price": quantity * float(drug_info.get("price", 0))
                    }
                    existing_item_index = -1
                    for i, existing in enumerate(self.sale_items_data):
                        if existing.get("generic_code") == item["generic_code"]:
                            existing_item_index = i
                            break
                    if existing_item_index != -1:
                        reply = QMessageBox.question(self, "کالای تکراری",
                                                     f"کالای '{item['name']}' قبلاً به لیست اضافه شده است. آیا می‌خواهید تعداد آن را افزایش دهید؟",
                                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                                                     QMessageBox.StandardButton.Yes)
                        if reply == QMessageBox.StandardButton.Yes:
                            self.sale_items_data[existing_item_index]["quantity"] += quantity
                            self.sale_items_data[existing_item_index]["total_price"] = self.sale_items_data[existing_item_index]["quantity"] * self.sale_items_data[existing_item_index]["unit_price"]
                        elif reply == QMessageBox.StandardButton.Cancel: return
                    else: self.sale_items_data.append(item)
                    self._update_sale_items_table()
                    self._update_grand_total()
            elif drug_info:
                 QMessageBox.warning(self, "خطا", "کالای انتخاب شده کد ژنریک معتبر ندارد.")
                 
    def _delete_selected_sale_item_shortcut(self):
        """ردیف انتخاب شده در جدول اقلام فروش را با میانبر F8 حذف می‌کند."""
        selected_rows = self.sale_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "انتخاب نشده", "لطفاً یک ردیف را برای حذف انتخاب کنید.")
            return
        
        current_row = selected_rows[0].row()
        self._remove_item_from_table(current_row) # از متد موجود برای حذف استفاده می‌کنیم

    def _add_item_to_table(self, row_index, item_data):
        self.sale_items_table.blockSignals(True)
        self.sale_items_table.setItem(row_index, 0, QTableWidgetItem(item_data.get("generic_code", "")))
        self.sale_items_table.setItem(row_index, 1, QTableWidgetItem(item_data.get("name", "")))
        qty_item = QTableWidgetItem(str(item_data.get("quantity", 1)))
        self.sale_items_table.setItem(row_index, 2, qty_item)
        unit_price = item_data.get("unit_price", 0)
        self.sale_items_table.setItem(row_index, 3, QTableWidgetItem(f"{unit_price:,.0f}"))
        total_row_price = item_data.get("total_price", 0)
        self.sale_items_table.setItem(row_index, 4, QTableWidgetItem(f"{total_row_price:,.0f}"))
        delete_button = QPushButton("حذف")
        delete_button.setFont(QFont("Arial", 7)) 
        delete_button.setStyleSheet("padding: 2px;")
        delete_button.clicked.connect(lambda _, r=row_index: self._remove_item_from_table(r))
        self.sale_items_table.setCellWidget(row_index, 5, delete_button)
        self.sale_items_table.blockSignals(False)

    def _update_sale_items_table(self):
        self.sale_items_table.setRowCount(0) 
        for i, item_data in enumerate(self.sale_items_data):
            self.sale_items_table.insertRow(i)
            self._add_item_to_table(i, item_data)
        self._update_grand_total()

    def _remove_item_from_table(self, row_index):
        if 0 <= row_index < len(self.sale_items_data):
            reply = QMessageBox.question(self, "تایید حذف", 
                                         f"آیا از حذف '{self.sale_items_data[row_index].get('name', '')}' اطمینان دارید؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                del self.sale_items_data[row_index]
                self._update_sale_items_table()

    def _on_table_cell_changed(self, row, column):
        if column == 2: 
            if not (0 <= row < len(self.sale_items_data)): return # بررسی محدوده ردیف
            self.sale_items_table.blockSignals(True) 
            try:
                current_item = self.sale_items_table.item(row, 2)
                if not current_item: # اگر آیتم به هر دلیلی وجود ندارد
                    self.sale_items_table.blockSignals(False)
                    return

                new_quantity_str = current_item.text()
                new_quantity = int(new_quantity_str)

                if new_quantity <= 0: 
                    QMessageBox.warning(self, "تعداد نامعتبر", "تعداد باید حداقل ۱ باشد.")
                    current_item.setText(str(self.sale_items_data[row]["quantity"]))
                else:
                    self.sale_items_data[row]["quantity"] = new_quantity
                    self.sale_items_data[row]["total_price"] = new_quantity * self.sale_items_data[row]["unit_price"]
                    total_price_item = self.sale_items_table.item(row, 4)
                    if total_price_item: # بررسی وجود آیتم قیمت کل
                        total_price_item.setText(f"{self.sale_items_data[row]['total_price']:,.0f}")
                    else: # اگر آیتم قیمت کل وجود ندارد، آن را ایجاد کن
                         self.sale_items_table.setItem(row, 4, QTableWidgetItem(f"{self.sale_items_data[row]['total_price']:,.0f}"))
                    self._update_grand_total()
            except ValueError:
                QMessageBox.warning(self, "ورودی نامعتبر", "لطفاً برای تعداد یک عدد صحیح وارد کنید.")
                if 0 <= row < len(self.sale_items_data) and self.sale_items_table.item(row,2):
                     self.sale_items_table.item(row, 2).setText(str(self.sale_items_data[row]["quantity"]))
            except Exception as e:
                print(f"خطا در _on_table_cell_changed: {e}")
                if 0 <= row < len(self.sale_items_data) and self.sale_items_table.item(row,2): # اطمینان از وجود آیتم
                     self.sale_items_table.item(row, 2).setText(str(self.sale_items_data[row]["quantity"]))
            self.sale_items_table.blockSignals(False)

    def _update_grand_total(self):
        total = sum(item.get("total_price", 0) for item in self.sale_items_data)
        self.grand_total_display_label.setText(f"{total:,.0f} ریال")

    # dialogs/otc_sale_dialog.py
# (داخل کلاس OTCSaleDialog)

    def _process_sale(self):
        if not self.sale_items_data:
            QMessageBox.warning(self, "فاکتور خالی", "هیچ کالایی به فاکتور اضافه نشده است.")
            return

        sale_date_str = datetime.now().strftime("%Y/%m/%d")
        sale_time_str = datetime.now().strftime("%H:%M:%S")
        total_amount_val = sum(item.get("total_price", 0) for item in self.sale_items_data)
        discount_amount_val = 0 
        final_amount_val = total_amount_val - discount_amount_val
        payment_method_val = "نقدی" 
        description_val = "فروش آزاد OTC"

        conn = None
        try:
            conn = get_current_otc_db_connection() 
            cursor = conn.cursor()
            conn.execute("BEGIN TRANSACTION")

            can_fulfill_all_items = True
            fulfillment_plan = [] 

            for item_to_sell in self.sale_items_data:
                generic_code = item_to_sell.get("generic_code")
                quantity_needed = item_to_sell.get("quantity", 0)
                item_name_for_msg = item_to_sell.get('name', 'کالای نامشخص')
                current_item_drug_id = item_to_sell.get("drug_id")

                if not generic_code or quantity_needed <= 0:
                    QMessageBox.warning(self, "قلم نامعتبر", f"کالای '{item_name_for_msg}' دارای کد یا تعداد نامعتبر است.")
                    can_fulfill_all_items = False; break

                cursor.execute("""
                    SELECT id, unit_count, expiry_date_gregorian
                    FROM company_purchase_items
                    WHERE generic_code = ? AND unit_count > 0 
                    ORDER BY expiry_date_gregorian ASC
                """, (generic_code,))
                available_batches = cursor.fetchall()

                item_batches_to_use = []
                fulfilled_for_item = 0

                if available_batches: # اگر بچ‌های قابل فروش وجود دارد
                    for batch_row in available_batches:
                        batch_id = batch_row["id"]
                        batch_units = batch_row["unit_count"]
                        if fulfilled_for_item >= quantity_needed: break
                        units_from_this_batch = min(quantity_needed - fulfilled_for_item, batch_units)
                        if units_from_this_batch > 0:
                            item_batches_to_use.append({
                                "batch_id": batch_id, "units_taken": units_from_this_batch,
                                "new_unit_count": batch_units - units_from_this_batch
                            })
                            fulfilled_for_item += units_from_this_batch
                    
                    if fulfilled_for_item < quantity_needed:
                        # اگر بچ موجود بود ولی کافی نبود
                        QMessageBox.warning(self, "کمبود موجودی در بچ‌ها", 
                                            f"موجودی کالای '{item_name_for_msg}' از بچ‌های موجود ({fulfilled_for_item} عدد) "
                                            f"کمتر از تعداد درخواستی ({quantity_needed} عدد) است.\n"
                                            f" لطفاً ابتدا موجودی انبار (بچ‌ها) را اصلاح کنید یا از موجودی کلی (در صورت امکان) استفاده شود.")
                        # اینجا می‌توانید تصمیم بگیرید که آیا اجازه فروش از موجودی کلی drugs.stock را بدهید یا خیر
                        # فعلا برای جلوگیری از پیام خطای قبلی، اگر بچ کافی نبود، فروش را متوقف می‌کنیم.
                        # اگر میخواهید در این حالت هم از drugs.stock کم شود، باید منطق آن اضافه شود.
                        can_fulfill_all_items = False; break 
                    else: # از بچ‌ها تامین شد
                        fulfillment_plan.append({
                            "type": "batch_stock", "generic_code": generic_code,
                            "item_name": item_name_for_msg, "quantity_to_deduct": fulfilled_for_item,
                            "batches_used_details": item_batches_to_use
                        })
                elif current_item_drug_id : # اگر هیچ بچ قابل فروشی یافت نشد، اما drug_id داریم، از موجودی اصلی drugs کم کن
                    print(f"--- OTC Sale: No batches for {generic_code}. Attempting to use main stock (drug_id: {current_item_drug_id}) ---")
                    cursor.execute("SELECT stock FROM drugs WHERE id = ?", (current_item_drug_id,))
                    drug_stock_row = cursor.fetchone()
                    current_main_stock = drug_stock_row["stock"] if drug_stock_row else 0
                    
                    if current_main_stock >= quantity_needed:
                        fulfillment_plan.append({
                            "type": "main_stock", "drug_id": current_item_drug_id,
                            "generic_code": generic_code, "item_name": item_name_for_msg,
                            "quantity_to_deduct": quantity_needed
                        })
                        print(f"--- OTC Sale: Using {quantity_needed} from main_stock for {generic_code} ---")
                    else: # اگر موجودی اصلی هم کافی نبود
                        QMessageBox.warning(self, "کمبود موجودی کلی", 
                                            f"موجودی کالای '{item_name_for_msg}' در انبار کافی نیست (موجودی کلی: {current_main_stock}).")
                        can_fulfill_all_items = False; break
                else: # نه بچی یافت شد و نه drug_id برای بررسی موجودی اصلی
                    QMessageBox.warning(self, "موجودی نامشخص", 
                                        f"برای کالای '{item_name_for_msg}' نه بچ قابل فروشی یافت شد و نه امکان بررسی موجودی کلی وجود دارد.")
                    can_fulfill_all_items = False; break
            
            if not can_fulfill_all_items:
                if conn: conn.rollback()
                return

            # --- ادامه ذخیره‌سازی فروش و اقلام و آپدیت انبار (بدون تغییر نسبت به کد قبلی شما برای این بخش) ---
            cursor.execute("""
                INSERT INTO otc_sales (sale_date, sale_time, total_amount, discount_amount, final_amount, payment_method, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sale_date_str, sale_time_str, total_amount_val, discount_amount_val, final_amount_val, payment_method_val, description_val))
            otc_sale_id = cursor.lastrowid

            total_stock_change_for_drugs_table = {} 

            for item_idx, item_data_to_save in enumerate(self.sale_items_data):
                plan_for_this_item = fulfillment_plan[item_idx] 
                
                cursor.execute("""
                    INSERT INTO otc_sale_items (otc_sale_id, drug_id, generic_code, item_name_snapshot, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    otc_sale_id, item_data_to_save.get("drug_id"), item_data_to_save.get("generic_code"),
                    item_data_to_save.get("name"), item_data_to_save.get("quantity"),
                    item_data_to_save.get("unit_price"), item_data_to_save.get("total_price")
                ))

                generic_code = plan_for_this_item["generic_code"]
                quantity_deducted_for_item = plan_for_this_item["quantity_to_deduct"]

                if plan_for_this_item["type"] == "batch_stock":
                    for batch_detail in plan_for_this_item["batches_used_details"]:
                        cursor.execute("UPDATE company_purchase_items SET unit_count = ? WHERE id = ?",
                                       (batch_detail["new_unit_count"], batch_detail["batch_id"]))
                elif plan_for_this_item["type"] == "main_stock":
                     cursor.execute("UPDATE drugs SET stock = stock - ? WHERE id = ?", # کسر از drugs.stock
                                   (quantity_deducted_for_item, plan_for_this_item["drug_id"]))
                
                if generic_code not in total_stock_change_for_drugs_table:
                    total_stock_change_for_drugs_table[generic_code] = 0
                total_stock_change_for_drugs_table[generic_code] += quantity_deducted_for_item
            
            # آپدیت نهایی drugs.stock برای مواردی که از بچ کسر شده‌اند
            # یا اگر از ابتدا فقط از drugs.stock کم شده، این بخش آن را دوباره کم نکند.
            for g_code, total_deducted_units in total_stock_change_for_drugs_table.items():
                # این آپدیت باید فقط برای تغییرات بچ اعمال شود، چون تغییرات main_stock مستقیم اعمال شده
                # برای جلوگیری از کسر دوباره، باید بررسی کنیم که آیا این g_code قبلا از main_stock کم شده یا نه
                # یک راه ساده‌تر این است که drugs.stock همیشه مجموعی از بچ‌ها باشد و مستقیم آپدیت نشود،
                # یا اینکه این آپدیت نهایی را دقیق‌تر کنیم.
                # فعلا با فرض اینکه کسر از بچ باید در drugs.stock هم منعکس شود:
                item_was_main_stock_deducted = any(p["type"] == "main_stock" and p["generic_code"] == g_code for p in fulfillment_plan)
                if not item_was_main_stock_deducted: # فقط اگر کسر اولیه از main_stock نبوده، اینجا از drugs.stock کم کن
                     cursor.execute("UPDATE drugs SET stock = stock - ? WHERE generic_code = ?",
                                   (total_deducted_units, g_code))


            conn.commit()
            QMessageBox.information(self, "فروش موفق", "فروش آزاد با موفقیت ثبت و موجودی انبار به‌روز شد.")
            
            self.sale_items_data = []
            self._update_sale_items_table()
        except sqlite3.Error as e:
            if conn: conn.rollback()
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در پردازش فروش آزاد: {e}\n{traceback.format_exc()}")
        except Exception as ex:
            if conn: conn.rollback()
            QMessageBox.critical(self, "خطای برنامه", f"یک خطای پیش بینی نشده رخ داد: {ex}\n{traceback.format_exc()}")
        finally:
            if conn:
                conn.close()