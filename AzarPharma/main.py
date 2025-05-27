# main.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from database.db_manager import DatabaseManager # مطمئن شوید این ایمپورت درست است
from ui.login import LoginPage


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICON_DIR = os.path.join(BASE_DIR, "icons") # پوشه آیکون‌ها
    if not os.path.exists(ICON_DIR):
        os.makedirs(ICON_DIR)
        print("پوشه 'icons' ایجاد شد. آیکون‌ها را داخلش قرار دهید (مثل back.png و ...)")
    
    db_file_path = os.path.join(BASE_DIR, "pharmacy.db")
    print(f"--- DEBUG: Attempting to initialize DB at: {db_file_path} ---") 
    DatabaseManager.init_database() # مطمئن شوید این فراخوانی درست است

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # اعمال استایل شیت آذر:
    qss_path = os.path.join(BASE_DIR, 'resources', 'azarsheet.qss')
    if os.path.exists(qss_path):
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    else:
        print("⚠️ فایل azarsheet.qss پیدا نشد.")

    login_page = LoginPage()
    login_page.show()

    sys.exit(app.exec())
