import sqlite3
import os
import sys
from datetime import datetime, timedelta

# اضافه کردن مسیر پروژه
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    import config
    DB_PATH = config.DB_PATH
except ImportError:
    DB_PATH = os.path.join(parent_dir, 'pharmacy.db')

class DatabaseManager:
    """مدیریت یکپارچه دیتابیس داروخانه"""
    
    @staticmethod
    def get_connection():
        """دریافت اتصال به دیتابیس"""
        print(f"--- DatabaseManager: Connecting to {DB_PATH} ---")
        
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"--- DatabaseManager: Created directory {db_dir} ---")
        
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            print("--- DatabaseManager: Connection successful ---")
            return conn
        except sqlite3.Error as e:
            print(f"--- DatabaseManager ERROR: {e} ---")
            return None
    
    @staticmethod
    def execute_query(query, params=None):
        """اجرای کوئری با مدیریت خطا"""
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            if conn is None:
                raise sqlite3.Error("Failed to connect to database")
                
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
                
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"--- DatabaseManager ERROR in execute_query: {e} ---")
            raise e
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def init_database():
        """مقداردهی اولیه دیتابیس"""
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            if conn is None:
                print("--- DatabaseManager ERROR: init_database failed to get connection ---")
                return False
                
            cursor = conn.cursor()
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS drugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generic_name TEXT NOT NULL,
                en_brand_name TEXT NOT NULL,
                generic_code TEXT NOT NULL UNIQUE,
                form TEXT,
                dosage TEXT,
                price_per_unit INTEGER NOT NULL,
                stock INTEGER DEFAULT 0,
                min_stock_alert_level INTEGER DEFAULT 0,
                barcode TEXT DEFAULT '',
                qr_code TEXT DEFAULT '',
                drug_type TEXT DEFAULT 'PRESCRIPTION', -- <--- ستون جدید drug_type
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # جدول نسخه‌ها
            cursor.execute('''CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prescription_number TEXT,
                sale_type TEXT,
                date TEXT,
                total_price INTEGER,
                insurance_name TEXT,
                version_type TEXT,
                serial_number TEXT,
                patient_first_name TEXT,
                patient_last_name TEXT,
                patient_national_code TEXT,
                patient_phone_number TEXT,
                patient_birth_date TEXT,
                doctor_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
            )''')
            
           # جدول آیتم‌های نسخه
            cursor.execute('''CREATE TABLE IF NOT EXISTS prescription_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prescription_id INTEGER,
                drug_id INTEGER, -- <--- ستون جدید drug_id
                drug_name TEXT NOT NULL,
                dosage TEXT,
                form TEXT,
                generic_code TEXT,
                packaging TEXT,
                insurance INTEGER,
                unit_price INTEGER,
                quantity INTEGER,
                total_price INTEGER,
                usage_instructions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE,
                FOREIGN KEY (drug_id) REFERENCES drugs(id) ON DELETE SET NULL -- <--- Foreign Key جدید
            )''')
            
            # جدول دکترها
            cursor.execute('''CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                medical_council_id TEXT UNIQUE NOT NULL,
                phone_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # جدول خریدهای شرکت
            cursor.execute('''CREATE TABLE IF NOT EXISTS company_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_row_number TEXT UNIQUE,
                registration_date TEXT,
                document_type TEXT,
                supplier_name TEXT,
                description TEXT,
                apply_to_shelf_directly INTEGER,
                invoice_type TEXT,
                invoice_number TEXT UNIQUE,
                invoice_date TEXT,
                settlement_period_days INTEGER,
                settlement_date TEXT,
                total_items_purchase_price REAL,
                total_items_sale_price REAL,
                overall_document_discount REAL,
                document_product_discount REAL,
                document_tax_levies REAL,
                items_tax_levies REAL,
                shipping_cost REAL,
                payable_amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # جدول آیتم‌های خرید شرکت
            cursor.execute('''CREATE TABLE IF NOT EXISTS company_purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_document_id INTEGER,
                generic_code TEXT,
                brand_code TEXT,
                drug_name_snapshot TEXT,
                quantity_in_package INTEGER,
                package_count INTEGER,
                unit_count INTEGER,
                expiry_date_gregorian TEXT,
                expiry_date_jalali TEXT,
                purchase_price_per_package REAL,
                profit_percentage REAL,
                sale_price_per_package REAL,
                item_vat REAL,
                item_discount_rial REAL,
                batch_number TEXT,
                main_warehouse_location TEXT,
                main_warehouse_min_stock INTEGER,
                main_warehouse_max_stock INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_document_id) REFERENCES company_purchases(id) ON DELETE CASCADE
            )''')
            # جدول فروش آزاد (OTC)
            cursor.execute('''CREATE TABLE IF NOT EXISTS otc_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TEXT NOT NULL,
                sale_time TEXT,
                total_amount REAL NOT NULL,
                discount_amount REAL DEFAULT 0,
                final_amount REAL NOT NULL,
                payment_method TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            # جدول آیتم‌های فروش آزاد (OTC Sale Items)
            cursor.execute('''CREATE TABLE IF NOT EXISTS otc_sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                otc_sale_id INTEGER NOT NULL,
                drug_id INTEGER,
                generic_code TEXT,
                item_name_snapshot TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (otc_sale_id) REFERENCES otc_sales(id) ON DELETE CASCADE,
                FOREIGN KEY (drug_id) REFERENCES drugs(id) ON DELETE SET NULL
            )''')
            # جدول صندوق (Cash Registers)
            cursor.execute('''CREATE TABLE IF NOT EXISTS cash_registers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                total_amount INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            # جدول نسخه‌های ثبت شده در صندوق (Cash Prescriptions)
            cursor.execute('''CREATE TABLE IF NOT EXISTS cash_prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prescription_id INTEGER,
                date_added TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
            )''')
            
            # ایجاد ایندکس‌ها
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_drugs_generic_code ON drugs(generic_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_drugs_barcode ON drugs(barcode)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_drugs_qr_code ON drugs(qr_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prescriptions_date ON prescriptions(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prescription_items_prescription_id ON prescription_items(prescription_id)')
            
            conn.commit()
            print("✅ Database initialized successfully")
            return True
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"❌ Database initialization error: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def update_schema_for_barcode():
        """آپدیت schema برای barcode/QR - ادغام از update_schema_barcode.py"""
        print("🔄 شروع آپدیت schema برای barcode...")
        
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            if conn is None:
                print("❌ خطا در اتصال به دیتابیس")
                return False
                
            cursor = conn.cursor()
            
            # بررسی وجود جدول drugs
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drugs'")
            if not cursor.fetchone():
                print("❌ جدول drugs پیدا نشد!")
                return False
                
            # بررسی ستون‌های موجود
            cursor.execute("PRAGMA table_info(drugs)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"📋 ستون‌های موجود: {columns}")
            
            changes_made = False
            
            # اضافه کردن ستون barcode
            if 'barcode' not in columns:
                try:
                    cursor.execute("ALTER TABLE drugs ADD COLUMN barcode TEXT DEFAULT ''")
                    print("✅ ستون 'barcode' اضافه شد")
                    changes_made = True
                except Exception as e:
                    print(f"❌ خطا در اضافه کردن ستون barcode: {e}")
            else:
                print("ℹ️ ستون 'barcode' از قبل موجود است")
            
            # اضافه کردن ستون qr_code
            if 'qr_code' not in columns:
                try:
                    cursor.execute("ALTER TABLE drugs ADD COLUMN qr_code TEXT DEFAULT ''")
                    print("✅ ستون 'qr_code' اضافه شد")
                    changes_made = True
                except Exception as e:
                    print(f"❌ خطا در اضافه کردن ستون qr_code: {e}")
            else:
                print("ℹ️ ستون 'qr_code' از قبل موجود است")
            
            # ایجاد ایندکس‌ها
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_barcode ON drugs(barcode)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_qr_code ON drugs(qr_code)")
                if changes_made:
                    print("✅ ایندکس‌های barcode و qr_code ایجاد شد")
            except Exception as e:
                print(f"❌ خطا در ایجاد ایندکس: {e}")
            
            if changes_made:
                conn.commit()
                print("💾 تغییرات ذخیره شد")
            
            print("✅ آپدیت schema با موفقیت انجام شد!")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ خطا در آپدیت schema: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_near_expiry_items_count(days_threshold: int = 90) -> int:
        """دریافت تعداد اقلام نزدیک به انقضا"""
        try:
            today_date_str = datetime.now().date().strftime("%Y/%m/%d")
            future_date = datetime.now().date() + timedelta(days=days_threshold)
            future_date_str = future_date.strftime("%Y/%m/%d")
            
            query = """
                SELECT COUNT(DISTINCT generic_code) 
                FROM company_purchase_items
                WHERE expiry_date_gregorian >= ? AND expiry_date_gregorian <= ? 
                AND (package_count > 0 OR unit_count > 0)
            """
            
            result = DatabaseManager.execute_query(query, (today_date_str, future_date_str))
            return result[0][0] if result else 0
            
        except Exception as e:
            print(f"--- DatabaseManager ERROR in get_near_expiry_items_count: {e} ---")
            return 0
    
    # توابع آماری برای چارت‌ها
    @staticmethod
    def get_sales_data():
        """دریافت داده‌های فروش برای چارت‌ها"""
        query = '''
        SELECT 
            DATE(p.date) as sale_date,
            SUM(p.total_price) as daily_total,
            COUNT(*) as prescription_count
        FROM prescriptions p 
        WHERE p.date >= date('now', '-30 days')
        GROUP BY DATE(p.date)
        ORDER BY sale_date DESC
        '''
        return DatabaseManager.execute_query(query)
    
    @staticmethod
    def get_top_selling_drugs():
        """دریافت پرفروش‌ترین داروها"""
        query = '''
        SELECT 
            pi.drug_name,
            SUM(pi.quantity) as total_quantity,
            SUM(pi.total_price) as total_revenue
        FROM prescription_items pi
        JOIN prescriptions p ON pi.prescription_id = p.id
        WHERE p.date >= date('now', '-30 days')
        GROUP BY pi.drug_name
        ORDER BY total_quantity DESC
        LIMIT 10
        '''
        return DatabaseManager.execute_query(query)
    
    @staticmethod
    def get_low_stock_drugs():
        """دریافت داروهای کم موجود"""
        query = '''
        SELECT generic_name, stock, min_stock_alert_level
        FROM drugs 
        WHERE stock <= min_stock_alert_level AND min_stock_alert_level > 0
        ORDER BY (stock - min_stock_alert_level) ASC
        '''
        return DatabaseManager.execute_query(query)
    
    @staticmethod
    def get_monthly_trends():
        """دریافت روند ماهانه فروش"""
        query = '''
        SELECT 
            strftime('%Y-%m', p.date) as month,
            SUM(p.total_price) as monthly_total,
            COUNT(*) as prescription_count
        FROM prescriptions p 
        WHERE p.date >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', p.date)
        ORDER BY month DESC
        '''
        return DatabaseManager.execute_query(query)

# برای سازگاری با کدهای قدیمی
def get_connection(db_path: str = None):
    """تابع سازگاری با db.py قدیمی"""
    return DatabaseManager.get_connection()

def get_near_expiry_items_count(days_threshold: int = 90) -> int:
    """تابع سازگاری با db.py قدیمی"""
    return DatabaseManager.get_near_expiry_items_count(days_threshold)
