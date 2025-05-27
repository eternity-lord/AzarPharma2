
import sqlite3
import os
import sys

# اضافه کردن مسیر پروژه
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    import config
    DB_PATH = config.DB_PATH
except ImportError:
    DB_PATH = os.path.join(current_dir, 'pharmacy.db')

def update_database_schema():
    """آپدیت دیتابیس برای اضافه کردن ستون‌های بارکد"""
    print("🔄 شروع آپدیت دیتابیس...")
    
    try:
        # اطمینان از وجود فایل دیتابیس
        if not os.path.exists(DB_PATH):
            print(f"❌ فایل دیتابیس پیدا نشد: {DB_PATH}")
            return False
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"✅ اتصال به دیتابیس: {DB_PATH}")
        
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
        
        # ایجاد ایندکس برای جستجوی سریع‌تر
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_barcode ON drugs(barcode)")
            if changes_made:
                print("✅ ایندکس barcode ایجاد شد")
        except Exception as e:
            print(f"❌ خطا در ایجاد ایندکس: {e}")
        
        if changes_made:
            conn.commit()
            print("💾 تغییرات ذخیره شد")
        
        # بررسی نهایی
        cursor.execute("PRAGMA table_info(drugs)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 ستون‌های نهایی: {final_columns}")
        
        conn.close()
        print("✅ دیتابیس با موفقیت آپدیت شد!")
        return True
        
    except Exception as e:
        print(f"❌ خطا در آپدیت دیتابیس: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🗄️ آپدیت Schema دیتابیس برای بارکد")
    print("=" * 50)
    
    success = update_database_schema()
    
    print("=" * 50)
    if success:
        print("🎉 عملیات با موفقیت انجام شد!")
    else:
        print("💥 عملیات با خطا مواجه شد!")
    print("=" * 50)