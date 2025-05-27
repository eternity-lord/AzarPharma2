# config.py

import os

# مسیر پیش‌فرض دیتابیس
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = "pharmacy.db"
DB_PATH = os.path.join(PROJECT_ROOT, DATABASE_NAME)

# تنظیمات نسخه و توسعه
APP_EMAIL = "mohammadirdarkweb@gmail.com"
APP_VERSION = "1.0"
COMPANY_NAME = "AzarPharma"
PHARMACY_ADDRESS = "آدرس کامل داروخانه شما"
PHARMACY_PHONE = "شماره تلفن داروخانه"