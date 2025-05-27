import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
#from PyQt6.QtCharts import *
import sqlite3
from datetime import datetime, timedelta
import json
import os
from ui.components.interactive_charts import ChartsContainer

class KPICard(QFrame):
    """کارت KPI با انیمیشن و طراحی مدرن"""
    clicked = pyqtSignal()
    
    def __init__(self, title, value, icon, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        self.setup_ui()
        self.setup_animation()
        
        
    def setup_ui(self):
        self.setFixedSize(200, 120)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # استایل کارت
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.color}, stop:1 {self.color}dd);
                border-radius: 15px;
                border: 2px solid {self.color}44;
                margin: 5px;
            }}
            QFrame:hover {{
                border: 2px solid {self.color};
                transform: scale(1.05);
            }}
            QLabel {{
                color: white;
                background: transparent;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # ردیف بالا: آیکون و عنوان
        header_layout = QHBoxLayout()
        
        # آیکون
        icon_label = QLabel(self.icon)
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # عنوان
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # مقدار اصلی
        self.value_label = QLabel(self.value)
        self.value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.value_label)
        layout.addStretch()
        
    def setup_animation(self):
        """انیمیشن hover"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
        
    def update_value(self, new_value):
        """بروزرسانی مقدار با انیمیشن"""
        self.value_label.setText(str(new_value))
        
        # انیمیشن تغییر رنگ
        effect = QGraphicsOpacityEffect()
        self.value_label.setGraphicsEffect(effect)
        
        self.fade_animation = QPropertyAnimation(effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0.3)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

class QuickStatsWidget(QWidget):
    """ویجت آمار سریع"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()
        self.setup_auto_refresh()
        
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # عنوان
        title = QLabel("آمار سریع")
        title.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # کانتینر کارت‌ها
        cards_container = QWidget()
        cards_layout = QGridLayout(cards_container)
        cards_layout.setSpacing(15)
        
        # ایجاد کارت‌های KPI
        self.kpi_cards = {}
        
        kpi_data = [
            {"key": "sales_today", "title": "فروش امروز", "icon": "💰", "color": "#28a745"},
            {"key": "low_stock", "title": "موجودی کم", "icon": "⚠️", "color": "#dc3545"},
            {"key": "customers_today", "title": "مراجعین امروز", "icon": "👥", "color": "#007bff"},
            {"key": "profit_today", "title": "سود امروز", "icon": "📈", "color": "#6f42c1"},
            {"key": "near_expiry", "title": "نزدیک انقضا", "icon": "⏰", "color": "#fd7e14"},
            {"key": "total_drugs", "title": "کل داروها", "icon": "💊", "color": "#20c997"}
        ]
        
        row, col = 0, 0
        for kpi in kpi_data:
            card = KPICard(kpi["title"], "0", kpi["icon"], kpi["color"])
            card.clicked.connect(lambda k=kpi["key"]: self.on_kpi_clicked(k))
            
            self.kpi_cards[kpi["key"]] = card
            cards_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 3:  # 3 کارت در هر ردیف
                col = 0
                row += 1
                
        layout.addWidget(cards_container)
        
    def load_data(self):
        """بارگذاری داده‌ها از دیتابیس"""
        try:
            # مسیر دیتابیس
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "pharmacy.db")
            
            if not os.path.exists(db_path):
                print(f"Database not found at: {db_path}")
                return
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # فروش امروز (OTC + نسخه)
            today = datetime.now().strftime('%Y/%m/%d') # فرمت تاریخ در دیتابیس شما yyyy/MM/dd است
            
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM otc_sales 
                WHERE sale_date = ?
            """, (today,))
            otc_sales_today = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT COALESCE(SUM(total_price), 0) 
                FROM prescriptions 
                WHERE date = ?
            """, (today,))
            prescription_sales_today = cursor.fetchone()[0] or 0
            
            sales_today = otc_sales_today + prescription_sales_today
            self.kpi_cards["sales_today"].update_value(f"{sales_today:,.0f} ریال")
            
            # موجودی کم (بر اساس min_stock_alert_level)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM drugs 
                WHERE stock <= min_stock_alert_level AND min_stock_alert_level > 0
            """)
            low_stock = cursor.fetchone()[0]
            self.kpi_cards["low_stock"].update_value(f"{low_stock} قلم")
            
            # مراجعین امروز (فعلاً از تعداد نسخه‌های امروز استفاده می‌کنیم)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM prescriptions 
                WHERE date = ?
            """, (today,))
            customers_today = cursor.fetchone()[0]
            self.kpi_cards["customers_today"].update_value(f"{customers_today} نفر")
            
            # سود امروز (تخمینی 20% از فروش - این باید دقیق‌تر شود)
            profit_today = sales_today * 0.2
            self.kpi_cards["profit_today"].update_value(f"{profit_today:,.0f} ریال")
            
            # نزدیک انقضا (3 ماه آینده)
            future_date_dt = datetime.now().date() + timedelta(days=90)
            future_date_str = future_date_dt.strftime('%Y/%m/%d')
            cursor.execute("""
                SELECT COUNT(*) 
                FROM company_purchase_items -- <--- تغییر به company_purchase_items
                WHERE expiry_date_gregorian <= ? AND expiry_date_gregorian > ?
            """, (future_date_str, today))
            near_expiry = cursor.fetchone()[0]
            self.kpi_cards["near_expiry"].update_value(f"{near_expiry} قلم")
            # کل داروها
            cursor.execute("SELECT COUNT(*) FROM drugs")
            total_drugs = cursor.fetchone()[0]
            self.kpi_cards["total_drugs"].update_value(f"{total_drugs} قلم")
            
            conn.close()
            
        except Exception as e:
            print(f"Error loading KPI data: {e}")
            
    def setup_auto_refresh(self):
        """بروزرسانی خودکار هر 30 ثانیه"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_data)
        self.refresh_timer.start(30000)  # 30 ثانیه
        
    def on_kpi_clicked(self, kpi_key):
        """کلیک روی کارت KPI"""
        print(f"KPI clicked: {kpi_key}")
        # اینجا می‌تونی گزارش مربوطه رو باز کنی
        
class EnhancedDashboard(QWidget):
    """داشبورد پیشرفته اصلی"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Main Content
        main_content = QScrollArea()
        main_content.setWidgetResizable(True)
        main_content.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        charts_container = ChartsContainer()
        content_layout.addWidget(charts_container)
        
        # آمار سریع
        self.quick_stats = QuickStatsWidget()
        content_layout.addWidget(self.quick_stats)
        
        # فضای اضافی برای آینده (نمودارها و...)
        content_layout.addStretch()
        
        main_content.setWidget(content_widget)
        layout.addWidget(main_content)
        
    def create_header(self):
        """ایجاد هدر داشبورد"""
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-bottom: 2px solid #5a67d8;
            }
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 10, 30, 10)
        
        # عنوان
        title = QLabel("📊 داشبورد پیشرفته آذر فارما")
        title.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
        
        # تاریخ و زمان
        datetime_label = QLabel(datetime.now().strftime("%Y/%m/%d - %H:%M"))
        datetime_label.setFont(QFont("Tahoma", 10))
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(datetime_label)
        
        return header
        
    def refresh_data(self):
        """بروزرسانی کل داده‌ها"""
        self.quick_stats.load_data()
