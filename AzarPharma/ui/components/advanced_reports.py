# ui/components/advanced_reports.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QTableWidget, QTableWidgetItem, QLabel, QPushButton,
                            QComboBox, QDateEdit, QGroupBox, QGridLayout,
                            QMessageBox, QHeaderView, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
import sqlite3
from datetime import datetime, timedelta
import config  # 🔥 اضافه کردن import config


class DataLoadThread(QThread):
    """Thread برای بارگذاری داده‌ها در پس‌زمینه"""
    data_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, query, params=None):
        super().__init__()
        self.query = query
        self.params = params or []
        
    def run(self):
        try:
            # 🔥 استفاده از config.DB_PATH
            from database.db import get_connection
            conn = get_connection(config.DB_PATH)  # ✅ اضافه کردن db_path
            
            if conn is None:
                self.error_occurred.emit("خطا در اتصال به دیتابیس")
                return
                
            cursor = conn.cursor()
            cursor.execute(self.query, self.params)
            data = cursor.fetchall()
            conn.close()
            
            # تبدیل sqlite3.Row به list
            result = []
            for row in data:
                result.append([row[i] for i in range(len(row))])
                
            self.data_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری داده‌ها: {str(e)}")


class AdvancedReportsWidget(QWidget):
    """ویجت گزارش‌های تحلیلی پیشرفته"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 گزارش‌های تحلیلی پیشرفته")
        self.setup_ui()
        self.load_initial_data()
        
    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # عنوان اصلی
        title_label = QLabel("📊 گزارش‌های تحلیلی پیشرفته")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("QLabel { color: #2c3e50; margin: 10px; }")
        layout.addWidget(title_label)
        
        # تب‌ها
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # تب گزارش فروش
        self.sales_tab = self.create_sales_analysis_tab()
        self.tab_widget.addTab(self.sales_tab, "📈 تحلیل فروش")
        
        # تب گزارش موجودی
        self.inventory_tab = self.create_inventory_analysis_tab()
        self.tab_widget.addTab(self.inventory_tab, "📦 تحلیل موجودی")
        
        # تب گزارش مالی
        self.financial_tab = self.create_financial_analysis_tab()
        self.tab_widget.addTab(self.financial_tab, "💰 تحلیل مالی")
        
        # تب گزارش عملکرد
        self.performance_tab = self.create_performance_analysis_tab()
        self.tab_widget.addTab(self.performance_tab, "⚡ تحلیل عملکرد")
        
        layout.addWidget(self.tab_widget)
        
    def create_sales_analysis_tab(self):
        """ایجاد تب تحلیل فروش"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # فیلترها
        filter_group = QGroupBox("🔍 فیلترهای جستجو")
        filter_layout = QGridLayout(filter_group)
        
        # فیلتر بازه زمانی
        filter_layout.addWidget(QLabel("از تاریخ:"), 0, 0)
        self.sales_from_date = QDateEdit()
        self.sales_from_date.setDate(QDate.currentDate().addMonths(-1))
        self.sales_from_date.setCalendarPopup(True)
        filter_layout.addWidget(self.sales_from_date, 0, 1)
        
        filter_layout.addWidget(QLabel("تا تاریخ:"), 0, 2)
        self.sales_to_date = QDateEdit()
        self.sales_to_date.setDate(QDate.currentDate())
        self.sales_to_date.setCalendarPopup(True)
        filter_layout.addWidget(self.sales_to_date, 0, 3)
        
        # دکمه تحلیل
        analyze_btn = QPushButton("🔎 تحلیل فروش")
        analyze_btn.clicked.connect(self.analyze_sales)
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        filter_layout.addWidget(analyze_btn, 0, 4)
        
        layout.addWidget(filter_group)
        
        # جدول نتایج
        self.sales_table = QTableWidget()
        self.sales_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.sales_table.setAlternatingRowColors(True)
        layout.addWidget(self.sales_table)
        
        return widget
    
    def create_inventory_analysis_tab(self):
        """ایجاد تب تحلیل موجودی"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # آمار کلی موجودی
        stats_group = QGroupBox("📊 آمار کلی موجودی")
        stats_layout = QGridLayout(stats_group)
        
        self.total_drugs_label = QLabel("تعداد کل داروها: -")
        self.low_stock_label = QLabel("داروهای کم موجود: -")
        self.expired_label = QLabel("داروهای منقضی: -")
        self.near_expiry_label = QLabel("داروهای نزدیک انقضا: -")
        
        stats_layout.addWidget(self.total_drugs_label, 0, 0)
        stats_layout.addWidget(self.low_stock_label, 0, 1)
        stats_layout.addWidget(self.expired_label, 1, 0)
        stats_layout.addWidget(self.near_expiry_label, 1, 1)
        
        layout.addWidget(stats_group)
        
        # دکمه تحلیل موجودی
        inventory_btn = QPushButton("📦 تحلیل موجودی")
        inventory_btn.clicked.connect(self.analyze_inventory)
        inventory_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(inventory_btn)
        
        # جدول موجودی
        self.inventory_table = QTableWidget()
        self.inventory_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.inventory_table.setAlternatingRowColors(True)
        layout.addWidget(self.inventory_table)
        
        return widget
    
    def create_financial_analysis_tab(self):
        """ایجاد تب تحلیل مالی"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # آمار مالی
        financial_group = QGroupBox("💰 آمار مالی")
        financial_layout = QGridLayout(financial_group)
        
        self.total_sales_label = QLabel("کل فروش: -")
        self.total_profit_label = QLabel("کل سود: -")
        self.avg_sale_label = QLabel("میانگین فروش روزانه: -")
        self.top_revenue_label = QLabel("پردرآمدترین دارو: -")
        
        financial_layout.addWidget(self.total_sales_label, 0, 0)
        financial_layout.addWidget(self.total_profit_label, 0, 1)
        financial_layout.addWidget(self.avg_sale_label, 1, 0)
        financial_layout.addWidget(self.top_revenue_label, 1, 1)
        
        layout.addWidget(financial_group)
        
        # دکمه تحلیل مالی
        financial_btn = QPushButton("💰 تحلیل مالی")
        financial_btn.clicked.connect(self.analyze_financial)
        financial_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        layout.addWidget(financial_btn)
        
        # جدول تحلیل مالی
        self.financial_table = QTableWidget()
        self.financial_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.financial_table.setAlternatingRowColors(True)
        layout.addWidget(self.financial_table)
        
        return widget
    
    def create_performance_analysis_tab(self):
        """ایجاد تب تحلیل عملکرد"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # آمار عملکرد
        performance_group = QGroupBox("⚡ آمار عملکرد")
        performance_layout = QGridLayout(performance_group)
        
        self.fast_moving_label = QLabel("داروهای پرفروش: -")
        self.slow_moving_label = QLabel("داروهای کم‌فروش: -")
        self.turnover_label = QLabel("نرخ گردش موجودی: -")
        self.efficiency_label = QLabel("کارایی فروش: -")
        
        performance_layout.addWidget(self.fast_moving_label, 0, 0)
        performance_layout.addWidget(self.slow_moving_label, 0, 1)
        performance_layout.addWidget(self.turnover_label, 1, 0)
        performance_layout.addWidget(self.efficiency_label, 1, 1)
        
        layout.addWidget(performance_group)
        
        # دکمه تحلیل عملکرد
        performance_btn = QPushButton("⚡ تحلیل عملکرد")
        performance_btn.clicked.connect(self.analyze_performance)
        performance_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        layout.addWidget(performance_btn)
        
        # جدول عملکرد
        self.performance_table = QTableWidget()
        self.performance_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.performance_table.setAlternatingRowColors(True)
        layout.addWidget(self.performance_table)
        
        return widget
    
    def load_initial_data(self):
        """بارگذاری داده‌های اولیه"""
        self.analyze_inventory()
    
    def analyze_sales(self):
        """تحلیل فروش"""
        try:
            from_date = self.sales_from_date.date().toString("yyyy-MM-dd")
            to_date = self.sales_to_date.date().toString("yyyy-MM-dd")
            
            query = """
            SELECT 
                pi.drug_name,
                SUM(pi.quantity) as total_quantity,
                SUM(pi.total_price) as total_revenue,
                COUNT(DISTINCT p.id) as prescription_count,
                AVG(pi.unit_price) as avg_price
            FROM prescription_items pi
            JOIN prescriptions p ON pi.prescription_id = p.id
            WHERE DATE(p.date) BETWEEN ? AND ?
            GROUP BY pi.drug_name
            ORDER BY total_revenue DESC
            LIMIT 50
            """
            
            self.sales_thread = DataLoadThread(query, [from_date, to_date])
            self.sales_thread.data_ready.connect(self.display_sales_data)
            self.sales_thread.error_occurred.connect(self.show_error)
            self.sales_thread.start()
            
        except Exception as e:
            self.show_error(f"خطا در تحلیل فروش: {str(e)}")
    
    def analyze_inventory(self):
        """تحلیل موجودی"""
        try:
            # آمار کلی
            self.update_inventory_stats()
            
            # جدول موجودی
            query = """
            SELECT 
                d.generic_name,
                d.form,
                d.dosage,
                d.stock,
                d.min_stock_alert_level,
                d.price_per_unit,
                (d.stock * d.price_per_unit) as total_value,
                CASE 
                    WHEN d.stock <= d.min_stock_alert_level THEN 'کم موجود'
                    WHEN d.stock > d.min_stock_alert_level * 3 THEN 'موجودی زیاد'
                    ELSE 'عادی'
                END as status
            FROM drugs d
            ORDER BY total_value DESC
            """
            
            self.inventory_thread = DataLoadThread(query)
            self.inventory_thread.data_ready.connect(self.display_inventory_data)
            self.inventory_thread.error_occurred.connect(self.show_error)
            self.inventory_thread.start()
            
        except Exception as e:
            self.show_error(f"خطا در تحلیل موجودی: {str(e)}")
    
    def analyze_financial(self):
        """تحلیل مالی"""
        try:
            # آمار مالی
            self.update_financial_stats()
            
            # جدول تحلیل مالی
            query = """
            SELECT 
                pi.drug_name,
                SUM(pi.total_price) as revenue,
                SUM(pi.quantity) as quantity_sold,
                AVG(pi.unit_price) as avg_price,
                COUNT(DISTINCT DATE(p.date)) as active_days
            FROM prescription_items pi
            JOIN prescriptions p ON pi.prescription_id = p.id
            WHERE DATE(p.date) >= DATE('now', '-30 days')
            GROUP BY pi.drug_name
            HAVING revenue > 0
            ORDER BY revenue DESC
            LIMIT 30
            """
            
            self.financial_thread = DataLoadThread(query)
            self.financial_thread.data_ready.connect(self.display_financial_data)
            self.financial_thread.error_occurred.connect(self.show_error)
            self.financial_thread.start()
            
        except Exception as e:
            self.show_error(f"خطا در تحلیل مالی: {str(e)}")
    
    def analyze_performance(self):
        """تحلیل عملکرد"""
        try:
            # آمار عملکرد
            self.update_performance_stats()
            
            # جدول عملکرد
            query = """
            SELECT 
                pi.drug_name,
                SUM(pi.quantity) as total_sold,
                COUNT(DISTINCT p.id) as prescription_count,
                AVG(pi.quantity) as avg_quantity_per_prescription,
                SUM(pi.total_price) as total_revenue,
                MAX(DATE(p.date)) as last_sale_date
            FROM prescription_items pi
            JOIN prescriptions p ON pi.prescription_id = p.id
            WHERE DATE(p.date) >= DATE('now', '-90 days')
            GROUP BY pi.drug_name
            ORDER BY total_sold DESC
            LIMIT 40
            """
            
            self.performance_thread = DataLoadThread(query)
            self.performance_thread.data_ready.connect(self.display_performance_data)
            self.performance_thread.error_occurred.connect(self.show_error)
            self.performance_thread.start()
            
        except Exception as e:
            self.show_error(f"خطا در تحلیل عملکرد: {str(e)}")
    
    def update_inventory_stats(self):
        """به‌روزرسانی آمار موجودی"""
        try:
            from database.db import get_connection
            conn = get_connection(config.DB_PATH)  # ✅ اضافه کردن db_path
            
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # تعداد کل داروها
            cursor.execute("SELECT COUNT(*) FROM drugs")
            total_drugs = cursor.fetchone()[0]
            self.total_drugs_label.setText(f"تعداد کل داروها: {total_drugs:,}")
            
            # داروهای کم موجود
            cursor.execute("SELECT COUNT(*) FROM drugs WHERE stock <= min_stock_alert_level")
            low_stock = cursor.fetchone()[0]
            self.low_stock_label.setText(f"داروهای کم موجود: {low_stock:,}")
            
            conn.close()
            
        except Exception as e:
            print(f"خطا در به‌روزرسانی آمار موجودی: {e}")
    
    def update_financial_stats(self):
        """به‌روزرسانی آمار مالی"""
        try:
            from database.db import get_connection
            conn = get_connection(config.DB_PATH)  # ✅ اضافه کردن db_path
            
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # کل فروش ماه جاری
            cursor.execute("""
                SELECT COALESCE(SUM(total_price), 0) 
                FROM prescriptions 
                WHERE DATE(date) >= DATE('now', 'start of month')
            """)
            total_sales = cursor.fetchone()[0]
            self.total_sales_label.setText(f"کل فروش ماه جاری: {total_sales:,} تومان")
            
            conn.close()
            
        except Exception as e:
            print(f"خطا در به‌روزرسانی آمار مالی: {e}")
    
    def update_performance_stats(self):
        """به‌روزرسانی آمار عملکرد"""
        try:
            from database.db import get_connection
            conn = get_connection(config.DB_PATH)  # ✅ اضافه کردن db_path
            
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # پرفروش‌ترین دارو
            cursor.execute("""
                SELECT pi.drug_name, SUM(pi.quantity) as total
                FROM prescription_items pi
                JOIN prescriptions p ON pi.prescription_id = p.id
                WHERE DATE(p.date) >= DATE('now', '-30 days')
                GROUP BY pi.drug_name
                ORDER BY total DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                self.fast_moving_label.setText(f"پرفروش‌ترین: {result[0]} ({result[1]} عدد)")
            
            conn.close()
            
        except Exception as e:
            print(f"خطا در به‌روزرسانی آمار عملکرد: {e}")
    
    def display_sales_data(self, data):
        """نمایش داده‌های فروش"""
        headers = ["نام دارو", "تعداد فروخته شده", "درآمد کل", "تعداد نسخه", "قیمت میانگین"]
        self.populate_table(self.sales_table, data, headers)
    
    def display_inventory_data(self, data):
        """نمایش داده‌های موجودی"""
        headers = ["نام دارو", "فرم", "دوز", "موجودی", "حد هشدار", "قیمت واحد", "ارزش کل", "وضعیت"]
        self.populate_table(self.inventory_table, data, headers)
    
    def display_financial_data(self, data):
        """نمایش داده‌های مالی"""
        headers = ["نام دارو", "درآمد", "تعداد فروخته شده", "قیمت میانگین", "روزهای فعال"]
        self.populate_table(self.financial_table, data, headers)
    
    def display_performance_data(self, data):
        """نمایش داده‌های عملکرد"""
        headers = ["نام دارو", "کل فروش", "تعداد نسخه", "میانگین در نسخه", "کل درآمد", "آخرین فروش"]
        self.populate_table(self.performance_table, data, headers)
    
    def populate_table(self, table, data, headers):
        """پر کردن جدول با داده‌ها"""
        table.setRowCount(len(data))
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                if value is None:
                    value = "-"
                elif isinstance(value, (int, float)) and col_idx in [1, 2, 4, 5, 6]:  # ستون‌های عددی
                    value = f"{value:,}"
                    
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)
        
        # تنظیم عرض ستون‌ها
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # تنظیم آخرین ستون برای پر کردن فضای باقی‌مانده
        if table.columnCount() > 0:
            header.setSectionResizeMode(table.columnCount() - 1, QHeaderView.ResizeMode.Stretch)
    
    def show_error(self, error_message):
        """نمایش خطا"""
        QMessageBox.critical(self, "خطا", error_message)
