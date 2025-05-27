# database/db.py

import sqlite3
import os
from datetime import datetime, timedelta # برای توابع دیگر ممکن است لازم باشد

# --- تابع اتصال به دیتابیس ---
# این تابع باید در تمام بخش‌های برنامه که به دیتابیس متصل می‌شوند، استفاده شود.
def get_connection(db_path: str):
    print(f"--- DATABASE.DB: get_connection called for path: {db_path} ---") # برای دیباگ
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # <--- تنظیم حیاتی برای دسترسی به ستون‌ها با نام
        print("--- DATABASE.DB: Connection successful, row_factory set. ---") # برای دیباگ
    except sqlite3.Error as e:
        print(f"--- DATABASE.DB ERROR: Failed to connect or set pragma/row_factory for {db_path}: {e} ---")
        # در صورت بروز خطا در اتصال، می‌توان conn را None برگرداند یا خطا را raise کرد
        # اگر None برگردانده شود، کدی که از این تابع استفاده می‌کند باید آن را مدیریت کند.
        # raise e # یا اینکه خطا را به بالا منتقل کنیم
    return conn

# --- تابع مقداردهی اولیه دیتابیس ---
def init_db(db_path: str):
    print(f"--- DATABASE.DB: init_db called for path: {db_path} ---")
    conn = None # اطمینان از تعریف conn
    try:
        # اطمینان از وجود پوشه دیتابیس
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir): # بررسی اینکه db_dir خالی نباشد
            os.makedirs(db_dir, exist_ok=True)
            print(f"--- DATABASE.DB: Created directory {db_dir} ---")
        
        conn = get_connection(db_path) # <--- استفاده از تابع get_connection اصلاح شده
        if conn is None:
            print("--- DATABASE.DB ERROR: init_db failed to get a database connection. ---")
            return # اگر اتصال برقرار نشد، ادامه نده

        c = conn.cursor()

        # تعریف جداول (کد کامل از پاسخ‌های قبلی شما، فقط بخش drugs را برای نمونه می‌آورم)
        c.execute('''CREATE TABLE IF NOT EXISTS drugs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        generic_name TEXT NOT NULL,
                        en_brand_name TEXT NOT NULL,
                        generic_code TEXT NOT NULL UNIQUE,
                        form TEXT,
                        dosage TEXT,
                        price_per_unit INTEGER NOT NULL,
                        stock INTEGER DEFAULT 0,
                        min_stock_alert_level INTEGER DEFAULT 0
                    )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS prescriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, prescription_number TEXT, sale_type TEXT, date TEXT,
                        total_price INTEGER, insurance_name TEXT, version_type TEXT, serial_number TEXT,
                        patient_first_name TEXT, patient_last_name TEXT, patient_national_code TEXT,
                        patient_phone_number TEXT, patient_birth_date TEXT, doctor_id INTEGER, 
                        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL )''')

        c.execute('''CREATE TABLE IF NOT EXISTS prescription_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prescription_id INTEGER,
                        drug_name TEXT NOT NULL, -- نام دارو در لحظه فروش (snapshot)
                        dosage TEXT,
                        form TEXT,
                        generic_code TEXT,
                        packaging TEXT,
                        insurance INTEGER,
                        unit_price INTEGER,
                        quantity INTEGER,
                        total_price INTEGER,
                        usage_instructions TEXT, -- <--- ستون جدید برای دستور مصرف
                        FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
                        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS doctors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, last_name TEXT,
                        medical_council_id TEXT UNIQUE NOT NULL, phone_number TEXT )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS company_purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, document_row_number TEXT UNIQUE, registration_date TEXT, 
                        document_type TEXT, supplier_name TEXT, description TEXT, apply_to_shelf_directly INTEGER, 
                        invoice_type TEXT, invoice_number TEXT UNIQUE, invoice_date TEXT, settlement_period_days INTEGER, 
                        settlement_date TEXT, total_items_purchase_price REAL, total_items_sale_price REAL, 
                        overall_document_discount REAL, document_product_discount REAL, document_tax_levies REAL, 
                        items_tax_levies REAL, shipping_cost REAL, payable_amount REAL )''')

        c.execute('''CREATE TABLE IF NOT EXISTS company_purchase_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, purchase_document_id INTEGER, generic_code TEXT,
                        brand_code TEXT, drug_name_snapshot TEXT, quantity_in_package INTEGER, package_count INTEGER, 
                        unit_count INTEGER, expiry_date_gregorian TEXT, expiry_date_jalali TEXT, 
                        purchase_price_per_package REAL, profit_percentage REAL, sale_price_per_package REAL, 
                        item_vat REAL, item_discount_rial REAL, batch_number TEXT, main_warehouse_location TEXT,
                        main_warehouse_min_stock INTEGER, main_warehouse_max_stock INTEGER, main_shelf_location TEXT,
                        main_shelf_min_stock INTEGER, main_shelf_max_stock INTEGER,
                        FOREIGN KEY (purchase_document_id) REFERENCES company_purchases(id),
                        FOREIGN KEY (generic_code) REFERENCES drugs(generic_code) )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS suppliers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, contact_person TEXT, 
                        phone TEXT, address TEXT, description TEXT )''')

        c.execute('''CREATE TABLE IF NOT EXISTS cash_registers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT UNIQUE, total_amount INTEGER DEFAULT 0 )''')

        c.execute('''CREATE TABLE IF NOT EXISTS cash_prescriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, prescription_id INTEGER, date_added TEXT,
                        FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS otc_sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, sale_date TEXT NOT NULL, sale_time TEXT,
                        total_amount REAL NOT NULL, discount_amount REAL DEFAULT 0, final_amount REAL NOT NULL,
                        payment_method TEXT, description TEXT )''')

        c.execute('''CREATE TABLE IF NOT EXISTS otc_sale_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, otc_sale_id INTEGER NOT NULL, drug_id INTEGER,
                        generic_code TEXT, item_name_snapshot TEXT NOT NULL, quantity INTEGER NOT NULL,
                        unit_price REAL NOT NULL, total_price REAL NOT NULL,
                        FOREIGN KEY (otc_sale_id) REFERENCES otc_sales(id) ON DELETE CASCADE,
                        FOREIGN KEY (drug_id) REFERENCES drugs(id) ON DELETE SET NULL )''')

        conn.commit()
        print("--- DATABASE.DB: init_db finished successfully. ---")
    except sqlite3.Error as e:
        print(f"--- DATABASE.DB ERROR: Error in init_db for {db_path}: {e} ---")
        # import traceback # اگر می‌خواهید جزئیات کامل خطا را ببینید
        # print(traceback.format_exc())
    except Exception as ex:
        print(f"--- DATABASE.DB ERROR: Unexpected error in init_db: {ex} ---")
    finally:
        if conn:
            conn.close()
            print("--- DATABASE.DB: Connection closed in init_db. ---")

# --- سایر توابع مانند get_low_stock_items_count و get_near_expiry_items_count ---
# این توابع باید از get_connection(db_path) استفاده کنند تا row_factory اعمال شود
# یا اگر خودشان اتصال جداگانه ایجاد می‌کنند، باید row_factory را تنظیم کنند.
# مثال برای get_low_stock_items_count:
def get_low_stock_items_count(db_path: str) -> int:
    conn = None; count = 0
    try:
        conn = get_connection(db_path) # <--- استفاده از get_connection اصلاح شده
        if conn is None: return 0 # اگر اتصال ناموفق بود
        cursor = conn.cursor()
        # کوئری شما برای شمارش (اینجا نیاز به دسترسی با نام ستون نیست، چون فقط COUNT(*) است)
        cursor.execute("SELECT COUNT(id) FROM drugs WHERE stock <= min_stock_alert_level AND min_stock_alert_level > 0")
        result = cursor.fetchone() 
        if result: # result یک sqlite3.Row خواهد بود
            count = result[0] # دسترسی به اولین (و تنها) ستون با ایندکس
    except Exception as e: 
        print(f"--- DATABASE.DB ERROR in get_low_stock_items_count: {e} ---")
    finally:
        if conn: conn.close()
    return count

def get_near_expiry_items_count(db_path: str, days_threshold: int = 90) -> int:
    conn = None; count = 0
    try:
        conn = get_connection(db_path) # <--- استفاده از get_connection اصلاح شده
        if conn is None: return 0
        cursor = conn.cursor()
        today_date_str = datetime.now().date().strftime("%Y/%m/%d")
        future_date = datetime.now().date() + timedelta(days=days_threshold)
        future_date_str = future_date.strftime("%Y/%m/%d")
        # اینجا هم فقط COUNT(*) است، پس دسترسی با نام ستون نیاز نیست
        cursor.execute("""
            SELECT COUNT(DISTINCT generic_code) FROM company_purchase_items
            WHERE expiry_date_gregorian >= ? AND expiry_date_gregorian <= ? AND (package_count > 0 OR unit_count > 0)
        """, (today_date_str, future_date_str))
        result = cursor.fetchone()
        if result: # result یک sqlite3.Row خواهد بود
            count = result[0] # دسترسی با ایندکس
    except Exception as e: 
        print(f"--- DATABASE.DB ERROR in get_near_expiry_items_count: {e} ---")
    finally:
        if conn: conn.close()
    return count