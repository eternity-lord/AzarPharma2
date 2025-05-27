# ui/dashboard.py (نسخه کامل و به‌روز شده نهایی)

import os
import traceback # برای نمایش کامل خطاها
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QPushButton, QFrame, QLabel, QSizePolicy, QApplication, QMessageBox
)
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QAction, QIcon, QFont, QKeySequence # <--- QKeySequence moved here
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime
from persiantools.jdatetime import JalaliDate


# --- ایمپورت دیالوگ‌ها ---
from dialogs.add_drug_company_dialog import AddDrugFromCompanyDialog
from dialogs.near_expiry_report_dialog import NearExpiryReportDialog
from dialogs.cash_register_dialog import CashRegisterDialog
from dialogs.cash_histories_dialog import CashHistoriesDialog
from dialogs.low_stock_report_dialog import LowStockReportDialog
from dialogs.warehouse_dialog import WarehouseDialog
from dialogs.ttak_update_dialog import TtakUpdateDialog
from dialogs.detailed_inventory_report_dialog import DetailedInventoryReportDialog
from dialogs.otc_sale_dialog import OTCSaleDialog
from dialogs.sales_report_dialog import SalesReportDialog 
from dialogs.drug_performance_report_dialog import DrugPerformanceReportDialog
from ui.components.modern_card import ModernCard
from ui.components.notification_system import NotificationManager, NotificationType
from ui.components.advanced_search import AdvancedSearchWidget, CompactSearchWidget
from ui.components.interactive_charts import ChartsContainer
from ui.components.advanced_reports import AdvancedReportsWidget
from dialogs.profit_loss_report_dialog import ProfitLossReportDialog
from ui.components.enhanced_dashboard import EnhancedDashboard, QuickStatsWidget

# --- ایمپورت از ماژول‌های پروژه ---
# این بخش برای خواندن تنظیمات و ارتباط با دیتابیس حیاتی است
# مطمئن شوید فایل‌های config.py و database/db.py در مسیر درست و بدون خطا هستند
try:
    from config import DB_PATH, APP_VERSION, APP_EMAIL
    from database.db import get_low_stock_items_count, get_near_expiry_items_count, get_connection
    print("--- Dashboard: Successfully imported from config and database.db (Full Version) ---")
except ImportError as import_error:
    print(f"!!! CRITICAL Dashboard Import ERROR: {import_error}. Application may not function correctly. !!!")
    print("!!! Please ensure config.py and database/db.py are accessible and correct. !!!")
    # مقادیر پیش‌فرض حیاتی در صورت عدم موفقیت شدید ایمپورت
    DB_PATH = "pharmacy.db" # یا None تا خطاها واضح‌تر شوند
    APP_VERSION = "Error"
    APP_EMAIL = "error@example.com"
    # تعریف توابع ساختگی برای جلوگیری از NameError در ادامه، اما با هشدار
    def get_low_stock_items_count(db_path): 
        print("Warning: Using dummy get_low_stock_items_count due to import error.")
        return -1 
    def get_near_expiry_items_count(db_path, days_threshold=90): 
        print("Warning: Using dummy get_near_expiry_items_count due to import error.")
        return -1


class MainDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        print("--- MainDashboard __init__ started (Full Version v2) ---") # v2 برای شناسایی این نسخه
        self.setWindowTitle("آذر فارما")
        self.showMaximized() 

        self.compact_font = QFont(); self.compact_font.setPointSize(8)
        self.combo_font = QFont(); self.combo_font.setPointSize(8)
        self.app_title_font = QFont(); self.app_title_font.setPointSize(10); self.app_title_font.setBold(True)
        self.glass_title_font = QFont(); self.glass_title_font.setPointSize(12); self.glass_title_font.setBold(True)
        self.glass_info_font = QFont(); self.glass_info_font.setPointSize(8)
        # --- Notification System ---
        self.notification_manager = NotificationManager(self)
        self.notification_manager.hide()  # شروع مخفی
        # --- Advanced Search ---
        self.search_widget = None  # برای نگهداری ویجت جستجو
        self.compact_search = CompactSearchWidget(self)
        self.compact_search.drug_selected.connect(self.on_drug_selected_from_search)
        try:
            self.charts_container = ChartsContainer(self)
            main_layout.addWidget(self.charts_container)
            print("Charts container added successfully")
        except Exception as e:
            print(f"Error adding charts container: {e}")
            # نمایش نمای کلاسیک در صورت خطا
            self.create_classic_view()
        try:
            if hasattr(self.compact_search, 'drug_selected'):
                self.compact_search.drug_selected.connect(self.on_drug_selected_from_search)
                print("✅ drug_selected signal connected successfully")
            else:
                print("⚠️ CompactSearchWidget doesn't have drug_selected signal")
        except Exception as e:
            print(f"❌ Error connecting drug_selected signal: {e}")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) 
        main_layout.setSpacing(0) 

        self.background_pixmap = QPixmap()
        self.background_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "back.png")
        self.set_background_image(self.background_image_path)

        top_bar = QFrame()
        top_bar.setObjectName("MainDashboardTopBar")
        top_bar.setFixedHeight(45) 
        top_bar.setStyleSheet("""
            #MainDashboardTopBar { 
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0f0f0, stop:1 #e0e0e0); 
                border-bottom: 1px solid #c0c0c0; 
            }
            QLabel { background-color: transparent; border: none; }
            QComboBox { margin: 3px; }
        """)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 2, 10, 2) 
        top_bar_layout.setSpacing(8)

        app_title = QLabel("آذر فارما")
        app_title.setFont(self.app_title_font)
        top_bar_layout.addWidget(app_title)
        top_bar_layout.addStretch(1)

        # اضافه کردن دکمه اسکن بارکد
        scan_btn = QPushButton("🔍 اسکن بارکد")
        scan_btn.clicked.connect(self.open_barcode_scanner)
        scan_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                        stop:0 #ff7675, stop:1 #d63031);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                        stop:0 #fd79a8, stop:1 #e84393);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                        stop:0 #b71c1c, stop:1 #c62828);
            }
        """)


        self.low_stock_alert_label = QLabel("")
        self.low_stock_alert_label.setFont(self.compact_font)
        self.low_stock_alert_label.setStyleSheet("color: red; font-weight: bold; padding: 3px 6px; border: 1px solid red; border-radius: 3px; margin-left: 3px;")
        self.low_stock_alert_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.low_stock_alert_label.mousePressEvent = self._open_low_stock_report_from_alert
        self.low_stock_alert_label.setVisible(False)
        top_bar_layout.addWidget(self.low_stock_alert_label)

        self.near_expiry_alert_label = QLabel("")
        self.near_expiry_alert_label.setFont(self.compact_font)
        self.near_expiry_alert_label.setStyleSheet("color: orange; font-weight: bold; padding: 3px 6px; border: 1px solid orange; border-radius: 3px; margin-left: 3px;")
        self.near_expiry_alert_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.near_expiry_alert_label.mousePressEvent = self._open_near_expiry_report_from_alert
        self.near_expiry_alert_label.setVisible(False)
        top_bar_layout.addWidget(self.near_expiry_alert_label)

        self.prescription_menu = QComboBox()
        self.prescription_menu.setFont(self.combo_font)
        self.prescription_menu.addItems(["نسخه جدید (F1)", "ثبت فروش آزاد (OTC)", "بارگذاری نسخه"])
        self.prescription_menu.insertItem(0, "فروش و نسخه‌ها") 
        self.prescription_menu.setCurrentIndex(0) 
        print("--- MainDashboard __init__: Connecting prescription_menu.activated to self.handle_prescription_menu ---")
        self.prescription_menu.activated.connect(self.handle_prescription_menu) 
        self.prescription_menu.setMinimumWidth(150) 
        top_bar_layout.addWidget(self.prescription_menu)

        self.warehouse_menu = QComboBox()
        self.warehouse_menu.setFont(self.combo_font)
        self.warehouse_menu.addItems(["نمایش کلی انبار (داروها)", "گزارش کامل موجودی (بچ‌ها)", "ورود دارو از شرکت", "آپدیت از تی‌تک"])
        self.warehouse_menu.insertItem(0, "مدیریت انبار")
        self.warehouse_menu.setCurrentIndex(0)
        self.warehouse_menu.activated.connect(self.handle_warehouse_menu)
        self.warehouse_menu.setMinimumWidth(170)
        top_bar_layout.addWidget(self.warehouse_menu)

        self.reports_menu = QComboBox()
        # self.reports_menu.setFont(self.combo_font) # اگر combo_font تعریف شده
        self.reports_menu.addItems([
                "صندوق امروز", 
                "صندوق کل", 
                "گزارش داروهای تاریخ نزدیک", 
                "گزارش کالاهای با موجودی کم",
                "گزارش فروش",
                "گزارش عملکرد داروها",
                "گزارش سود و زیان",
                "گزارش‌های تحلیلی پیشرفته" # 🔥 آیتم جدید اضافه شد
            ])
        self.reports_menu.insertItem(0, "گزارش‌ها و صندوق") 
        self.reports_menu.setCurrentIndex(0)
        self.reports_menu.activated.connect(self.handle_reports_menu)
        # self.reports_menu.setMinimumWidth(180) # اگر قبلا تنظیم کرده‌اید
        top_bar_layout.addWidget(self.reports_menu)
        # اضافه کردن جستجوی فشرده//
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.compact_search)

        # دکمه جستجوی پیشرفته
        advanced_search_btn = QPushButton("جستجوی پیشرفته")
        advanced_search_btn.clicked.connect(self.toggle_advanced_search)
        advanced_search_btn.setFixedHeight(35)
        top_bar_layout.addWidget(advanced_search_btn)
        # دکمه تغییر نمای داشبورد
        self.prescription_btn = QPushButton("📝 ثبت و مدیریت نسخه") # Note/Form
        self.warehouse_btn = QPushButton("📦 مدیریت انبار") # Box/Package
        self.reports_btn = QPushButton("📈 گزارشات و صندوق") # Chart/Growth
        self.settings_btn = QPushButton("⚙️ تنظیمات") # Gear/Cog
        self.about_btn = QPushButton("ℹ️ درباره ما") # Information
        view_toggle_btn = QPushButton("📊 نمای پیشرفته")  # تغییر از "کلاسیک" به "پیشرفته"
        view_toggle_btn.clicked.connect(self.toggle_dashboard_view)
        view_toggle_btn.setFixedHeight(35)
        top_bar_layout.addWidget(view_toggle_btn)


        main_layout.addWidget(top_bar)
        
        # --- Modern Dashboard Cards Container ---
        cards_container = QWidget()
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setContentsMargins(50, 30, 50, 30)
        cards_layout.setSpacing(20)

        # عنوان داشبورد
        dashboard_title = QLabel("داشبورد آذر فارما")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        dashboard_title.setFont(title_font)
        dashboard_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dashboard_title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        cards_layout.addWidget(dashboard_title)

        # ردیف اول کارت‌ها
        first_row_layout = QHBoxLayout()
        first_row_layout.setSpacing(20)
        first_row_layout.addStretch()

        # کارت فروش امروز
        self.sales_today_card = ModernCard(
            title="فروش امروز", 
            value="0 تومان", 
            subtitle="آمار فروش روزانه",
            color="#3498db"
        )
        self.sales_today_card.clicked.connect(self.open_daily_sales_report)
        first_row_layout.addWidget(self.sales_today_card)

        # کارت موجودی کم
        self.low_stock_card = ModernCard(
            title="موجودی کم", 
            value="0 قلم", 
            subtitle="نیاز به تأمین",
            color="#e74c3c"
        )
        self.low_stock_card.clicked.connect(self.open_low_stock_report)
        first_row_layout.addWidget(self.low_stock_card)

        # کارت تاریخ نزدیک
        self.near_expiry_card = ModernCard(
            title="تاریخ نزدیک", 
            value="0 قلم", 
            subtitle="3 ماه آینده",
            color="#f39c12"
        )
        self.near_expiry_card.clicked.connect(self.open_near_expiry_report)
        first_row_layout.addWidget(self.near_expiry_card)

        first_row_layout.addStretch()
        cards_layout.addLayout(first_row_layout)

        # ردیف دوم کارت‌ها
        second_row_layout = QHBoxLayout()
        second_row_layout.setSpacing(20)
        second_row_layout.addStretch()

        # کارت کل موجودی
        self.total_inventory_card = ModernCard(
            title="کل موجودی", 
            value="0 قلم", 
            subtitle="تمام داروها",
            color="#27ae60"
        )
        self.total_inventory_card.clicked.connect(self.open_warehouse_overview)
        second_row_layout.addWidget(self.total_inventory_card)

        # کارت صندوق
        self.cash_register_card = ModernCard(
            title="صندوق", 
            value="0 تومان", 
            subtitle="موجودی نقدی",
            color="#9b59b6"
        )
        self.cash_register_card.clicked.connect(self.open_cash_register)
        second_row_layout.addWidget(self.cash_register_card)

        # کارت نسخه‌های امروز
        self.prescriptions_today_card = ModernCard(
            title="نسخه‌های امروز", 
            value="0 نسخه", 
            subtitle="تعداد مراجعین",
            color="#34495e"
        )
        self.prescriptions_today_card.clicked.connect(self.open_prescriptions_report)
        second_row_layout.addWidget(self.prescriptions_today_card)

        second_row_layout.addStretch()
        cards_layout.addLayout(second_row_layout)

        cards_layout.addStretch()
        main_layout.addWidget(cards_container)


        self.shortcut_f1_new_prescription = QAction("نسخه جدید (F1)", self)
        self.shortcut_f1_new_prescription.setShortcut(QKeySequence("F1"))
        self.shortcut_f1_new_prescription.triggered.connect(self.open_new_prescription_window)
        self.addAction(self.shortcut_f1_new_prescription)
        
        # تایمر برای بررسی اعلان‌ها
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self._check_alerts)
        self.alert_timer.start(30000)  # هر 30 ثانیه
        QTimer.singleShot(500, self._check_alerts)  # بررسی اولیه

        print("--- MainDashboard __init__ finished (Full Version v2) ---")
    
        self.setup_enhanced_dashboard()
        
        # اضافه کردن داشبورد پیشرفته به layout اصلی
        if hasattr(self, 'enhanced_dashboard') and self.enhanced_dashboard:
            main_layout.addWidget(self.enhanced_dashboard)
            self.enhanced_dashboard.hide()  # شروع مخفی
        
        # ذخیره کردن cards_container برای استفاده بعدی
        self.cards_container = cards_container
        
        print("--- MainDashboard __init__ completed ---")

    def get_app_version(self):
        try: return APP_VERSION
        except NameError: print("Warning: APP_VERSION not found in config."); return "1.0.3"

    def get_support_email(self):
        try: return APP_EMAIL
        except NameError: print("Warning: APP_EMAIL not found in config."); return "support@example.com"

    def _check_alerts(self):
        """بررسی و نمایش اعلان‌های سیستم"""
        try:
            # بررسی موجودی کم
            low_stock_count = get_low_stock_items_count(DB_PATH)
            
            # بررسی تاریخ نزدیک (3 ماه = 90 روز)
            near_expiry_count = get_near_expiry_items_count(DB_PATH, 90)
            
            print(f"Alert Check: Low stock: {low_stock_count}, Near expiry: {near_expiry_count}")
            
            # نمایش اعلان موجودی کم
            if low_stock_count > 0:
                self.low_stock_alert_label.setText(f"موجودی کم: {low_stock_count} قلم")
                self.low_stock_alert_label.setVisible(True)
                
                # اعلان فقط اگر تعداد زیاد باشد
                if low_stock_count >= 10:
                    self.notification_manager.show_notification(
                        "هشدار موجودی",
                        f"{low_stock_count} قلم دارو موجودی کم دارند",
                        NotificationType.WARNING,
                        auto_hide=True,
                        duration=8000
                    )
            else:
                self.low_stock_alert_label.setVisible(False)
            
            # نمایش اعلان تاریخ نزدیک
            if near_expiry_count > 0:
                self.near_expiry_alert_label.setText(f"تاریخ نزدیک: {near_expiry_count} قلم")
                self.near_expiry_alert_label.setVisible(True)
                
                # اعلان فقط اگر تعداد زیاد باشد
                if near_expiry_count >= 5:
                    self.notification_manager.show_notification(
                        "هشدار تاریخ انقضا",
                        f"{near_expiry_count} قلم دارو تا 3 ماه آینده منقضی می‌شوند",
                        NotificationType.WARNING,
                        auto_hide=True,
                        duration=8000
                    )
            else:
                self.near_expiry_alert_label.setVisible(False)
                
            # بررسی سایر شرایط
            self._check_daily_conditions()
            
        except Exception as e:
            print(f"Error in _check_alerts: {e}")
            # نمایش اعلان خطا
            self.notification_manager.show_notification(
                "خطای سیستم",
                "خطا در بررسی اعلان‌ها",
                NotificationType.ERROR,
                auto_hide=True,
                duration=5000
            )

    def _check_daily_conditions(self):
        """بررسی شرایط روزانه"""
        try:
            current_hour = datetime.now().hour # <--- تغییر
            
            # اعلان شروع روز کاری
            if current_hour == 8:
                self.notification_manager.show_notification(
                    "شروع روز کاری",
                    "داروخانه آذر فارما - روز بخیر!",
                    NotificationType.INFO,
                    auto_hide=True,
                    duration=3000
                )
            
            # اعلان پایان روز کاری
            elif current_hour == 20:
                self.notification_manager.show_notification(
                    "پایان روز کاری",
                    "فراموش نکنید گزارش روزانه را بررسی کنید",
                    NotificationType.INFO,
                    auto_hide=True,
                    duration=5000
                )
                
        except Exception as e:
            print(f"Error in _check_daily_conditions: {e}")


    def _open_low_stock_report_from_alert(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print("--- DEBUG (Full): Opening LowStockReportDialog from alert ---")
            dialog = LowStockReportDialog(self); dialog.exec()
            QTimer.singleShot(200, self._check_alerts)

    def _open_near_expiry_report_from_alert(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print("--- DEBUG (Full): Opening NearExpiryReportDialog from alert ---")
            dialog = NearExpiryReportDialog(self); dialog.exec()
            QTimer.singleShot(200, self._check_alerts)

    def set_background_image(self, image_path):
        try:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                cw = self.centralWidget(); default_bg = "background-color: #E6F0FF;"
                if cw: cw.setStyleSheet(default_bg)
                else: self.setStyleSheet(f"QMainWindow {{{default_bg}}}")
            else:
                palette = self.palette(); 
                scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                brush = QBrush(scaled_pixmap)
                brush.setTransform(brush.transform().translate((self.width() - scaled_pixmap.width()) / 2, (self.height() - scaled_pixmap.height()) / 2))
                palette.setBrush(QPalette.ColorRole.Window, brush)
                self.setPalette(palette); self.setAutoFillBackground(True)
        except Exception as e: print(f"Error setting background image: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'background_image_path') and self.background_image_path:
            if self.centralWidget() and self.centralWidget().size().isValid():
                 QTimer.singleShot(0, lambda: self.set_background_image(self.background_image_path))
    
    def handle_prescription_menu(self, index: int):
        print(f"--- DEBUG (Full): handle_prescription_menu CALLED with index: {index} ---")
        if index == 0: 
            self.prescription_menu.setCurrentIndex(0) 
            return

        item_text = self.prescription_menu.itemText(index)
        print(f"--- DEBUG (Full): Selected item text in prescription_menu: '{item_text}' ---")
        dialog_to_open = None 
        if item_text == "نسخه جدید (F1)":
            print("--- DEBUG (Full): Opening new prescription window... ---")
            self.open_new_prescription_window() 
        elif item_text == "ثبت فروش آزاد (OTC)": 
            print("--- DEBUG (Full): Attempting to open OTCSaleDialog... ---")
            try:
                dialog_to_open = OTCSaleDialog(self) 
                print("--- DEBUG (Full): OTCSaleDialog instantiated. ---")
            except NameError as ne: # برای خطای ایمپورت احتمالی OTCSaleDialog
                 print(f"--- DEBUG ERROR (Full): OTCSaleDialog NameError: {ne}. Check imports. ---")
                 QMessageBox.critical(self, "خطای برنامه", f"کلاس OTCSaleDialog یافت نشد: {ne}\n{traceback.format_exc()}")
            except Exception as e:
                print(f"--- DEBUG ERROR (Full): Error instantiating OTCSaleDialog: {e} ---")
                QMessageBox.critical(self, "خطای ایجاد دیالوگ", f"خطا در ایجاد پنجره فروش OTC: {e}\n{traceback.format_exc()}")
        elif item_text == "بارگذاری نسخه": 
            print("--- DEBUG (Full): 'Load prescription' selected (not implemented). ---")
            QMessageBox.information(self, "اطلاع", "قابلیت 'بارگذاری نسخه' هنوز پیاده‌سازی نشده است.")
        else:
            print(f"--- DEBUG (Full): Unknown item_text in prescription_menu: '{item_text}' ---")
        
        if dialog_to_open:
            print(f"--- DEBUG (Full): Executing dialog: {type(dialog_to_open).__name__} ---")
            dialog_to_open.exec()
            print("--- DEBUG (Full): Dialog execution finished. ---")
        
        self.prescription_menu.setCurrentIndex(0)

    def handle_warehouse_menu(self, index: int):
        print(f"--- DEBUG (Full): handle_warehouse_menu called with index: {index} ---")
        if index == 0: self.warehouse_menu.setCurrentIndex(0); return
        item_text = self.warehouse_menu.itemText(index)
        print(f"--- DEBUG (Full): Selected item text in warehouse_menu: '{item_text}' ---")
        dialog = None
        try:
            if item_text == "ورود دارو از شرکت": dialog = AddDrugFromCompanyDialog(self)
            elif item_text == "نمایش کلی انبار (داروها)": dialog = WarehouseDialog(self) 
            elif item_text == "آپدیت از تی‌تک": dialog = TtakUpdateDialog(self) 
            elif item_text == "گزارش کامل موجودی (بچ‌ها)": dialog = DetailedInventoryReportDialog(self)
            else: print(f"--- DEBUG (Full): Unknown item_text in warehouse_menu: '{item_text}' ---")
            
            if dialog: 
                print(f"--- DEBUG (Full): Executing dialog: {type(dialog).__name__} ---"); 
                dialog.exec(); 
                print("--- DEBUG (Full): Dialog execution finished. ---")
        except Exception as e:
            print(f"--- DEBUG ERROR (Full) in handle_warehouse_menu for '{item_text}': {e} ---")
            QMessageBox.critical(self, "خطای اجرای دیالوگ", f"خطا در باز کردن '{item_text}': {e}\n{traceback.format_exc()}")
        self.warehouse_menu.setCurrentIndex(0)

    # ui/dashboard.py
# (داخل کلاس MainDashboard)

    # ui/dashboard.py
# (داخل کلاس MainDashboard)

    def handle_reports_menu(self, index: int):
        # print(f"--- DEBUG (Full): handle_reports_menu called with index: {index} ---")
        if index == 0: 
            self.reports_menu.setCurrentIndex(0)
            return

        item_text = self.reports_menu.itemText(index)
        # print(f"--- DEBUG (Full): Selected item text in reports_menu: '{item_text}' ---")
        dialog = None 
        try:
            if item_text == "صندوق امروز": 
                dialog = CashRegisterDialog(self)
            elif item_text == "صندوق کل": 
                dialog = CashHistoriesDialog(self)
            elif item_text == "گزارش داروهای تاریخ نزدیک": 
                dialog = NearExpiryReportDialog(self)
            elif item_text == "گزارش کالاهای با موجودی کم": 
                dialog = LowStockReportDialog(self)
            elif item_text == "گزارش فروش": 
                dialog = SalesReportDialog(self)
            elif item_text == "گزارش عملکرد داروها": 
                dialog = DrugPerformanceReportDialog(self)
            elif item_text == "گزارش سود و زیان":  # <--- اضافه کردن
                dialog = ProfitLossReportDialog(self)
            # 🔥 آیتم جدید اضافه کن:
            elif item_text == "گزارش‌های تحلیلی پیشرفته":
                self.open_advanced_reports()
                self.reports_menu.setCurrentIndex(0)
                return
           
                

            if dialog: 
                dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطای اجرای دیالوگ", f"خطا در باز کردن '{item_text}': {e}\n{traceback.format_exc()}")
        
        self.reports_menu.setCurrentIndex(0)


    def open_new_prescription_window(self):
        print("--- DEBUG (Full): open_new_prescription_window called ---")
        try:
            from pharmacyapp.pharmacy_window import PharmacyApp 
            if not hasattr(self, "_prescription_window_instance") or not self._prescription_window_instance.isVisible():
                self._prescription_window_instance = PharmacyApp(parent=None)
                self._prescription_window_instance.showMaximized()
            else:
                self._prescription_window_instance.activateWindow()
                self._prescription_window_instance.raise_()     
        except ImportError: 
            print("--- DEBUG ERROR (Full): PharmacyApp module not found ---")
            QMessageBox.critical(self, "خطا", "ماژول نسخه‌زنی یافت نشد.")
        except Exception as e: 
            print(f"--- DEBUG ERROR (Full): Error opening prescription window: {e} ---")
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن پنجره نسخه‌زنی: {e}\n{traceback.format_exc()}")

    def open_advanced_reports(self):
        """باز کردن پنجره گزارش‌های تحلیلی پیشرفته"""
        print("--- DEBUG (Full): open_advanced_reports called ---")
        try:
            if not hasattr(self, "_advanced_reports_window") or not self._advanced_reports_window.isVisible():
                from PyQt6.QtWidgets import QMainWindow
                
                self._advanced_reports_window = QMainWindow(self)
                self._advanced_reports_window.setWindowTitle("📊 گزارش‌های تحلیلی پیشرفته - آذر فارما")
                self._advanced_reports_window.setMinimumSize(1200, 800)
                
                advanced_widget = AdvancedReportsWidget()
                self._advanced_reports_window.setCentralWidget(advanced_widget)
                self._advanced_reports_window.showMaximized()
                print("✅ Advanced Reports window opened successfully")
            else:
                self._advanced_reports_window.activateWindow()
                self._advanced_reports_window.raise_()
        except Exception as e:
            print(f"❌ Error opening advanced reports: {e}")
            print(f"❌ Full traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن گزارش‌های پیشرفته:\n{e}")

    def open_daily_sales_report(self):
        """باز کردن گزارش فروش روزانه"""
        try:
            dialog = SalesReportDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن گزارش فروش:\n{str(e)}")

    def open_low_stock_report(self):
        """باز کردن گزارش موجودی کم"""
        try:
            dialog = LowStockReportDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن گزارش موجودی کم:\n{str(e)}")

    def open_near_expiry_report(self):
        """باز کردن گزارش تاریخ نزدیک"""
        try:
            dialog = NearExpiryReportDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن گزارش تاریخ نزدیک:\n{str(e)}")

    def open_warehouse_overview(self):
        """باز کردن نمایش کلی انبار"""
        try:
            dialog = WarehouseDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن انبار:\n{str(e)}")

    def open_cash_register(self):
        """باز کردن صندوق"""
        try:
            dialog = CashRegisterDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن صندوق:\n{str(e)}")

    def open_prescriptions_report(self):
        """باز کردن گزارش نسخه‌های امروز"""
        # فعلاً همان گزارش فروش
        self.open_daily_sales_report()

    def update_dashboard_data(self):
        """به‌روزرسانی داده‌های داشبورد"""
        try:
            # موجودی کم
            low_stock_count = get_low_stock_items_count(DB_PATH)
            self.low_stock_card.update_value(f"{low_stock_count} قلم")
            
            # تاریخ نزدیک
            near_expiry_count = get_near_expiry_items_count(DB_PATH, 90)
            self.near_expiry_card.update_value(f"{near_expiry_count} قلم")
            
            print(f"Dashboard updated: Low stock: {low_stock_count}, Near expiry: {near_expiry_count}")
            
        except Exception as e:
            print(f"Error updating dashboard data: {e}")
    
    def show_success_notification(self, title, message):
        """نمایش اعلان موفقیت"""
        self.notification_manager.show_notification(
            title, message, NotificationType.SUCCESS, True, 3000
        )

    def show_warning_notification(self, title, message):
        """نمایش اعلان هشدار"""
        self.notification_manager.show_notification(
            title, message, NotificationType.WARNING, True, 5000
        )

    def show_error_notification(self, title, message):
        """نمایش اعلان خطا"""
        self.notification_manager.show_notification(
            title, message, NotificationType.ERROR, True, 7000
        )

    def show_info_notification(self, title, message):
        """نمایش اعلان اطلاعاتی"""
        self.notification_manager.show_notification(
            title, message, NotificationType.INFO, True, 4000
        )

    def resizeEvent(self, event):
        """تنظیم مجدد موقعیت اعلان‌ها هنگام تغییر اندازه"""
        super().resizeEvent(event)
        if hasattr(self, 'notification_manager'):
            self.notification_manager.update_position()
    
    def toggle_advanced_search(self):
        """نمایش/مخفی کردن پنل جستجوی پیشرفته"""
        try:
            if self.search_widget is None:
                # ایجاد ویجت جستجوی پیشرفته
                self.search_widget = AdvancedSearchWidget(self)
                self.search_widget.drug_selected.connect(self.on_drug_selected_from_search)
                
                # اضافه کردن به layout اصلی
                main_layout = self.centralWidget().layout()
                # اضافه کردن بعد از top_bar (index 1)
                main_layout.insertWidget(1, self.search_widget)
                
                print("Advanced search widget created and shown")
            else:
                # تغییر حالت نمایش
                if self.search_widget.isVisible():
                    self.search_widget.hide()
                    print("Advanced search widget hidden")
                else:
                    self.search_widget.show()
                    self.search_widget.refresh_cache()  # به‌روزرسانی کش
                    print("Advanced search widget shown")
                    
        except Exception as e:
            print(f"Error in toggle_advanced_search: {e}")
            self.show_error_notification("خطای جستجو", f"خطا در باز کردن پنل جستجو: {e}")

    def on_drug_selected_from_search(self, drug_info):
        """مدیریت انتخاب دارو از جستجوی پیشرفته"""
        print(f"--- DEBUG (Full): Drug selected from search: {drug_info} ---")
        try:
            # اینجا می‌تونی عملیات مربوط به انتخاب دارو رو انجام بدی
            # مثلاً باز کردن پنجره ویرایش دارو یا نمایش جزئیات
            drug_name = drug_info.get('name', 'نامشخص')
            QMessageBox.information(self, "دارو انتخاب شد", f"دارو انتخاب شده: {drug_name}")
        except Exception as e:
            print(f"--- DEBUG ERROR (Full): Error in on_drug_selected_from_search: {e} ---")
            QMessageBox.critical(self, "خطا", f"خطا در پردازش انتخاب دارو: {e}")

    def open_advanced_reports(self):
        """باز کردن پنجره گزارش‌های تحلیلی پیشرفته"""
        print("--- DEBUG (Full): open_advanced_reports called ---")
        try:
            if not hasattr(self, "_advanced_reports_window") or not self._advanced_reports_window.isVisible():
                from PyQt6.QtWidgets import QMainWindow
                
                self._advanced_reports_window = QMainWindow(self)
                self._advanced_reports_window.setWindowTitle("📊 گزارش‌های تحلیلی پیشرفته - آذر فارما")
                self._advanced_reports_window.setMinimumSize(1200, 800)
                
                advanced_widget = AdvancedReportsWidget()
                self._advanced_reports_window.setCentralWidget(advanced_widget)
                self._advanced_reports_window.showMaximized()
                print("✅ Advanced Reports window opened successfully")
            else:
                self._advanced_reports_window.activateWindow()
                self._advanced_reports_window.raise_()
        except Exception as e:
            print(f"❌ Error opening advanced reports: {e}")
            print(f"❌ Full traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن گزارش‌های پیشرفته:\n{e}")


    def show_drug_operations_menu(self, drug_data):
        """نمایش منوی عملیات برای دارو انتخاب شده"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"عملیات برای: {drug_data['drug_name']}")
            dialog.setFixedSize(300, 200)
            
            layout = QVBoxLayout(dialog)
            
            # دکمه‌های مختلف عملیات
            btn_new_prescription = QPushButton("اضافه به نسخه جدید")
            btn_new_prescription.clicked.connect(lambda: self.add_to_new_prescription(drug_data, dialog))
            layout.addWidget(btn_new_prescription)
            
            btn_otc_sale = QPushButton("فروش آزاد (OTC)")
            btn_otc_sale.clicked.connect(lambda: self.add_to_otc_sale(drug_data, dialog))
            layout.addWidget(btn_otc_sale)
            
            btn_view_details = QPushButton("مشاهده جزئیات موجودی")
            btn_view_details.clicked.connect(lambda: self.view_drug_details(drug_data, dialog))
            layout.addWidget(btn_view_details)
            
            btn_cancel = QPushButton("انصراف")
            btn_cancel.clicked.connect(dialog.close)
            layout.addWidget(btn_cancel)
            
            dialog.exec()
            
        except Exception as e:
            print(f"Error in show_drug_operations_menu: {e}")

    def add_to_new_prescription(self, drug_data, dialog):
        """اضافه کردن دارو به نسخه جدید"""
        try:
            dialog.close()
            self.show_success_notification("انتقال به نسخه", f"دارو {drug_data['drug_name']} آماده اضافه شدن به نسخه")
            # اینجا باید نسخه جدید باز شود و دارو اضافه شود
            self.open_new_prescription_window()
        except Exception as e:
            print(f"Error in add_to_new_prescription: {e}")

    def add_to_otc_sale(self, drug_data, dialog):
        """اضافه کردن دارو به فروش آزاد"""
        try:
            dialog.close()
            self.show_success_notification("انتقال به OTC", f"دارو {drug_data['drug_name']} آماده اضافه شدن به فروش آزاد")
            # اینجا باید پنجره OTC باز شود
            from dialogs.otc_sale_dialog import OTCSaleDialog
            otc_dialog = OTCSaleDialog(self)
            otc_dialog.exec()
        except Exception as e:
            print(f"Error in add_to_otc_sale: {e}")

    def view_drug_details(self, drug_data, dialog):
        """مشاهده جزئیات دارو"""
        try:
            from dialogs.warehouse_dialog import WarehouseDialog
            dialog.close()
            warehouse_dialog = WarehouseDialog(self)
            warehouse_dialog.exec()
        except Exception as e:
            print(f"Error in view_drug_details: {e}")

    def toggle_dashboard_view(self):
        """تغییر بین نمای چارت و نمای کلاسیک"""
        try:
            sender = self.sender()
            
            if hasattr(self, 'charts_container') and self.charts_container.isVisible():
                # تغییر به نمای کلاسیک
                self.charts_container.hide()
                self.show_classic_view()
                sender.setText("📊 نمای چارت")
                self.show_info_notification("تغییر نما", "نمای کلاسیک فعال شد")
            else:
                # تغییر به نمای چارت
                if hasattr(self, 'glass_frame_container'):
                    self.glass_frame_container.hide()
                
                if not hasattr(self, 'charts_container'):
                    self.charts_container = ChartsContainer(self)
                    # اضافه کردن به layout اصلی
                    main_layout = self.centralWidget().layout()
                    main_layout.insertWidget(-1, self.charts_container)
                
                self.charts_container.show()
                sender.setText("📊 نمای کلاسیک")
                self.show_info_notification("تغییر نما", "نمای چارت فعال شد")
                
        except Exception as e:
            print(f"Error in toggle_dashboard_view: {e}")
            self.show_error_notification("خطای تغییر نما", f"خطا در تغییر نمای داشبورد: {e}")

    def show_classic_view(self):
        """نمایش نمای کلاسیک"""
        try:
            if not hasattr(self, 'glass_frame_container'):
                self.create_classic_view()
            
            self.glass_frame_container.show()
            
        except Exception as e:
            print(f"Error in show_classic_view: {e}")

    def create_classic_view(self):
        """ایجاد نمای کلاسیک"""
        try:
            # ایجاد glass_frame_container
            self.glass_frame_container = QWidget() 
            glass_frame_container_layout = QHBoxLayout(self.glass_frame_container)
            glass_frame_container_layout.setContentsMargins(0,0,0,0)
            glass_frame_container_layout.addStretch(1) 

            glass_frame = QFrame()
            glass_frame.setObjectName("GlassFrame")
            glass_frame.setFrameShape(QFrame.Shape.StyledPanel)
            glass_frame.setStyleSheet("""
                #GlassFrame { 
                    background-color: rgba(245, 245, 245, 0.85); 
                    border: 1px solid rgba(200, 200, 200, 0.7); 
                    border-radius: 10px; 
                    padding: 20px; 
                }
                #GlassFrame QLabel { 
                    background-color: transparent; 
                    border: none; 
                    color: #2c3e50; 
                }
            """)
            
            glass_frame.setMinimumSize(450, 220)
            glass_frame.setMaximumSize(550, 280)
            
            glass_layout = QVBoxLayout(glass_frame)
            glass_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            glass_layout.setContentsMargins(15, 15, 15, 15)
            glass_layout.setSpacing(8) 
            
            # محتوای glass frame
            glass_title = QLabel("نرم افزار داروخانه آذر فارما")
            glass_title.setFont(self.glass_title_font)
            glass_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            glass_layout.addWidget(glass_title)
            glass_layout.addSpacing(10)
            
            version_label = QLabel(f"نسخه برنامه: {self.get_app_version()}")
            version_label.setFont(self.glass_info_font)
            version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            glass_layout.addWidget(version_label)
            
            email_label = QLabel("پشتیبانی از طریق ایمیل:")
            email_label.setFont(self.glass_info_font)
            email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            glass_layout.addWidget(email_label)
            
            email_address_label = QLabel(self.get_support_email())
            email_address_label.setFont(self.glass_info_font)
            email_address_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            email_address_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            glass_layout.addWidget(email_address_label)
            
            glass_frame_container_layout.addWidget(glass_frame)
            glass_frame_container_layout.addStretch(1)
            
            # اضافه کردن به layout اصلی
            main_layout = self.centralWidget().layout()
            main_layout.insertWidget(-1, self.glass_frame_container)
            
        except Exception as e:
            print(f"Error creating classic view: {e}")

    def refresh_dashboard_data(self):
        """به‌روزرسانی داده‌های داشبورد"""
        try:
            if hasattr(self, 'charts_container') and self.charts_container.isVisible():
                self.charts_container.refresh_charts()
                self.show_success_notification("به‌روزرسانی", "داده‌های داشبورد به‌روزرسانی شد")
            
            # به‌روزرسانی alerts
            self._check_alerts()
            
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
            self.show_error_notification("خطای به‌روزرسانی", f"خطا در به‌روزرسانی داشبورد: {e}")

    def open_barcode_scanner(self):
        """باز کردن اسکن بارکد"""
        print("--- DEBUG: open_barcode_scanner called ---")
        try:
            from ui.components.barcode_scanner import BarcodeScannerDialog
            
            scanner_dialog = BarcodeScannerDialog(self)
            scanner_dialog.barcode_scanned.connect(self.on_barcode_scanned)
            scanner_dialog.exec()
            
        except Exception as e:
            print(f"❌ Error opening barcode scanner: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن اسکن بارکد:\n{e}")

    def on_barcode_scanned(self, barcode_type, data):
        """مدیریت نتیجه اسکن بارکد"""
        print(f"--- DEBUG: Barcode scanned - Type: {barcode_type}, Data: {data} ---")
        
        # نمایش notification
        self.show_success_notification("بارکد اسکن شد", f"نوع: {barcode_type}\nداده: {data}")
    def setup_enhanced_dashboard(self):
        """راه‌اندازی داشبورد پیشرفته"""
        self.enhanced_dashboard = EnhancedDashboard(self)
        self.is_enhanced_view = False  # شروع با نمای کلاسیک
        
    def toggle_dashboard_view(self):
        """تغییر بین نمای کلاسیک و پیشرفته"""
        if hasattr(self, 'enhanced_dashboard'):
            if self.is_enhanced_view:
                # برگشت به نمای کلاسیک
                self.enhanced_dashboard.hide()
                # نمایش کارت‌های کلاسیک
                self.show_classic_cards()
                self.is_enhanced_view = False
                # تغییر متن دکمه
                sender = self.sender()
                if sender:
                    sender.setText("📊 نمای پیشرفته")
            else:
                # رفتن به نمای پیشرفته
                self.hide_classic_cards()
                self.enhanced_dashboard.show()
                self.is_enhanced_view = True
                # تغییر متن دکمه
                sender = self.sender()
                if sender:
                    sender.setText("📊 نمای کلاسیک")
        else:
            print("Enhanced dashboard not initialized")

    def show_classic_cards(self):
        """نمایش کارت‌های کلاسیک"""
        # کارت‌های موجود رو نمایش بده
        if hasattr(self, 'cards_container'):
            self.cards_container.show()

    def hide_classic_cards(self):
        """مخفی کردن کارت‌های کلاسیک"""
        if hasattr(self, 'cards_container'):
            self.cards_container.hide()





