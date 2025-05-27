# fix_database_barcode.py

import sqlite3
import os

# پیدا کردن فایل دیتابیس
possible_paths = [
    'pharmacy.db',
    'database/pharmacy.db',
    os.path.join(os.path.dirname(__file__), 'pharmacy.db'),
    os.path.join(os.path.dirname(__file__), 'database', 'pharmacy.db')
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("❌ فایل دیتابیس پیدا نشد!")
    print("فایل‌های موجود:")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db'):
                print(f"  📄 {os.path.join(root, file)}")
    exit(1)

print(f"✅ دیتابیس پیدا شد: {db_path}")

# آپدیت دیتابیس
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # بررسی ستون‌های موجود
    cursor.execute("PRAGMA table_info(drugs)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"� ستون‌های موجود: {columns}")
    
    # اضافه کردن ستون barcode
    if 'barcode' not in columns:
        cursor.execute("ALTER TABLE drugs ADD COLUMN barcode TEXT DEFAULT ''")
        print("✅ ستون barcode اضافه شد")
    else:
        print("ℹ️ ستون barcode از قبل موجود است")
    
    # اضافه کردن ایندکس
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_barcode ON drugs(barcode)")
    
    conn.commit()
    conn.close()
    
    print("🎉 دیتابیس با موفقیت آپدیت شد!")
    
except Exception as e:
   print(f"❌ خطا: {e}")
