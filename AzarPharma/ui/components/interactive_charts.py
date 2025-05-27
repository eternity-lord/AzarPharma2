# ui/components/interactive_charts.py (نسخه کامل و اصلاح شده با رفع مشکل QPropertyAnimation)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QFrame, QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve,pyqtProperty, QRect, QObject # <--- pyqtProperty اینجا
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor, QLinearGradient
import sqlite3
import math
from datetime import datetime, timedelta
from config import DB_PATH

import sqlite3
import math
from datetime import datetime, timedelta
from config import DB_PATH

# تغییر: AnimatedChart به QWidget ساده تبدیل شد و تمامی کد انیمیشن حذف شد
class AnimatedChart(QWidget): # <--- ارث‌بری فقط از QWidget
    """کلاس پایه برای چارت‌ها (بدون انیمیشن)"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        print(f"--- DEBUG: AnimatedChart (Simple) '{title}' __init__ called. ---") # Debug print
        self.title = title
        self.data = []
        self.colors = [
            QColor(52, 152, 219),   # آبی
            QColor(46, 204, 113),   # سبز
            QColor(231, 76, 60),    # قرمز
            QColor(241, 196, 15),   # زرد
            QColor(155, 89, 182),   # بنفش
            QColor(230, 126, 34),   # نارنجی
            QColor(26, 188, 156),   # فیروزه‌ای
            QColor(243, 156, 18),   # نارنجی تیره
        ]
        # self._animation_progress حذف شد
        # setup_animation و start_animation حذف شدند
        
    # پراپرتی animationProgress و ست‌کننده/گت‌کننده آن حذف شد
    # @pyqtProperty(float)
    # def animationProgress(self): ...
    # @animationProgress.setter
    # def setAnimationProgress(self, value): ...

    # setup_animation و start_animation حذف شدند

# تغییر: PieChart اکنون فقط از QWidget ارث می‌برد (چون AnimatedChart هم QWidget شده)
class PieChart(AnimatedChart): # <--- ارث‌بری از AnimatedChart که خود QWidget است
    """چارت دایره‌ای ساده"""

    def __init__(self, title="", data=None, parent=None):
        super().__init__(title, parent)
        print(f"--- DEBUG: PieChart '{title}' __init__ called. ---") # Debug print
        self.setFixedSize(300, 250)
        if data:
            self.set_data(data)

    def set_data(self, data):
        """تنظیم داده‌های چارت"""
        self.data = data if data else []
        self.update() # اینجا update() فراخوانی می‌شود زیرا PieChart یک QWidget است

    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # محاسبه مجموع
        total = sum(item[1] for item in self.data if item[1] > 0)
        if total == 0:
            return

        # تنظیمات چارت
        rect = self.rect().adjusted(20, 30, -20, -60)

        # رسم عنوان
        painter.setPen(QColor(44, 62, 80))
        font = QFont("Tahoma", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect().x(), 5, self.rect().width(), 25,
                        Qt.AlignmentFlag.AlignCenter, self.title)

        # رسم بخش‌های دایره
        start_angle = 0
        for i, (label, value) in enumerate(self.data):
            if value <= 0:
                continue

            # محاسبه زاویه (بدون انیمیشن)
            angle = int((value / total) * 360) # <--- حذف * self._animation_progress

            # رسم بخش
            painter.setBrush(QBrush(self.colors[i % len(self.colors)]))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawPie(rect, start_angle * 16, angle * 16)

            start_angle += angle

        # رسم راهنما (Legend)
        legend_y = rect.bottom() + 10
        for i, (label, value) in enumerate(self.data):
            if value <= 0:
                continue

            # رسم مربع رنگ
            color_rect = QRect(rect.x() + (i * 100), legend_y, 10, 10)
            painter.setBrush(QBrush(self.colors[i % len(self.colors)]))
            painter.setPen(QPen(self.colors[i % len(self.colors)]))
            painter.drawRect(color_rect)

            # رسم متن
            painter.setPen(QColor(44, 62, 80))
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(color_rect.right() + 5, legend_y + 10,
                           f"{label[:8]}: {int(value)}")

# تغییر: BarChart اکنون فقط از QWidget ارث می‌برد
class BarChart(AnimatedChart): # <--- ارث‌بری از AnimatedChart که خود QWidget است
    """چارت میله‌ای ساده"""

    def __init__(self, title="", data=None, parent=None):
        super().__init__(title, parent)
        print(f"--- DEBUG: BarChart '{title}' __init__ called. ---") # Debug print
        self.setFixedSize(350, 250)
        if data:
            self.set_data(data)

    def set_data(self, data):
        """تنظیم داده‌های چارت"""
        self.data = data if data else []
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # تنظیمات چارت
        rect = self.rect().adjusted(40, 30, -20, -40)

        # رسم عنوان
        painter.setPen(QColor(44, 62, 80))
        font = QFont("Tahoma", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(0, 5, self.width(), 25,
                        Qt.AlignmentFlag.AlignCenter, self.title)

        if not self.data:
            return

        # محاسبه حداکثر مقدار
        max_value = max(item[1] for item in self.data if item[1] > 0)
        if max_value == 0:
            return

        # رسم میله‌ها
        bar_width = max(20, rect.width() // len(self.data) - 10)
        for i, (label, value) in enumerate(self.data):
            if value <= 0:
                continue

            # محاسبه ارتفاع (بدون انیمیشن)
            bar_height = int((value / max_value) * rect.height()) # <--- حذف * self._animation_progress

            # موقعیت میله
            x = rect.x() + i * (bar_width + 10)
            y = rect.bottom() - bar_height

            # رسم میله با گرادیان
            color = self.colors[i % len(self.colors)]
            gradient = QLinearGradient(0, y, 0, y + bar_height)
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color)

            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(color.darker(), 1))
            painter.drawRect(x, y, bar_width, bar_height)

            # رسم مقدار روی میله
            painter.setPen(QColor(255, 255, 255))
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            if bar_height > 20:
                painter.drawText(x, y + 15, bar_width, 20,
                               Qt.AlignmentFlag.AlignCenter, str(int(value)))

            # رسم برچسب
            painter.setPen(QColor(44, 62, 80))
            font.setBold(False)
            painter.setFont(font)
            painter.drawText(x, rect.bottom() + 15, bar_width, 20,
                           Qt.AlignmentFlag.AlignCenter, label[:8])

# تغییر: LineChart اکنون فقط از QWidget ارث می‌برد
class LineChart(AnimatedChart): # <--- ارث‌بری از AnimatedChart که خود QWidget است
    """چارت خطی ساده"""

    def __init__(self, title="", data=None, parent=None):
        super().__init__(title, parent)
        print(f"--- DEBUG: LineChart '{title}' __init__ called. ---") # Debug print
        self.setFixedSize(350, 250)
        if data:
            self.set_data(data)

    def set_data(self, data):
        """تنظیم داده‌های چارت"""
        self.data = data if data else []
        self.update()

    def paintEvent(self, event):
        if not self.data or len(self.data) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # تنظیمات چارت
        rect = self.rect().adjusted(40, 30, -20, -40)

        # رسم عنوان
        painter.setPen(QColor(44, 62, 80))
        font = QFont("Tahoma", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(0, 5, self.width(), 25,
                        Qt.AlignmentFlag.AlignCenter, self.title)

        # محاسبه حداکثر و حداقل
        values = [item[1] for item in self.data]
        if not values: return # جلوگیری از خطای max/min روی لیست خالی
        max_value = max(values)
        min_value = min(values)
        value_range = max_value - min_value if max_value != min_value else 1

        # محاسبه نقاط
        points = []
        for i, (label, value) in enumerate(self.data):
            x = rect.x() + (i * rect.width() / (len(self.data) - 1))
            y = rect.bottom() - ((value - min_value) / value_range * rect.height())
            points.append((x, y))

        # رسم خط (بدون انیمیشن)
        # animated_count = int(len(points) * self._animation_progress) # <--- حذف این خط

        if len(points) >= 2: # <--- تغییر شرط
            painter.setPen(QPen(QColor(52, 152, 219), 3))
            for i in range(len(points) - 1): # <--- تغییر حلقه
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i+1][0]), int(points[i+1][1]))

        # رسم نقاط
        for i in range(len(points)): # <--- تغییر حلقه
            x, y = points[i]
            painter.setBrush(QBrush(QColor(52, 152, 219)))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawEllipse(int(x-4), int(y-4), 8, 8)

class ChartCard(QFrame):
    """کارت نمایش چارت"""

    def __init__(self, title, chart_widget, parent=None):
        super().__init__(parent)
        self.title = title
        self.chart_widget = chart_widget
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
            QFrame:hover {
                border: 2px solid #3498db;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # عنوان کارت
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # چارت
        layout.addWidget(self.chart_widget)

class ChartsContainer(QWidget):
    """کانتینر اصلی چارت‌ها"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.charts = {}
        self.setup_ui()
        self.load_chart_data()

        # تایمر برای بروزرسانی خودکار
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_charts)
        self.refresh_timer.start(60000)  # هر دقیقه

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # عنوان بخش
        header_layout = QHBoxLayout()

        title_label = QLabel("📈 نمودارهای تعاملی")
        title_label.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        header_layout.addWidget(title_label)

        # دکمه بروزرسانی
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_charts)
        header_layout.addWidget(refresh_btn)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # کانتینر چارت‌ها
        self.charts_layout = QGridLayout()
        self.charts_layout.setSpacing(10)
        layout.addLayout(self.charts_layout)

    def load_chart_data(self):
        """بارگذاری داده‌های چارت‌ها"""
        try:
            # پاک کردن چارت‌های قبلی
            self.clear_charts()

            # ایجاد چارت‌های جدید
            self.create_sales_chart()
            self.create_top_drugs_chart()
            self.create_monthly_trend_chart()
            self.create_categories_chart()

        except Exception as e:
            print(f"خطا در بارگذاری داده‌های چارت: {e}")

    def clear_charts(self):
        """پاک کردن چارت‌های موجود"""
        for i in reversed(range(self.charts_layout.count())):
            child = self.charts_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        self.charts.clear()

    def create_sales_chart(self):
        """چارت فروش امروز"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            today = datetime.now().strftime('%Y/%m/%d') # فرمت تاریخ در دیتابیس شما
            
            # فروش نقدی (OTC)
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM otc_sales
                WHERE sale_date = ?
            """, (today,))
            cash_sales = cursor.fetchone()[0] or 0

            # فروش نسخه‌ای (Prescriptions)
            cursor.execute("""
                SELECT COALESCE(SUM(total_price), 0)
                FROM prescriptions
                WHERE date = ?
            """, (today,))
            prescription_sales = cursor.fetchone()[0] or 0

            conn.close()

            data = []
            if cash_sales > 0:
                data.append(("فروش آزاد", cash_sales))
            if prescription_sales > 0:
                data.append(("فروش نسخه‌ای", prescription_sales))

            if not data:
                data = [("هیچ فروشی", 1)]

            pie_chart = PieChart("فروش امروز", data)
            chart_card = ChartCard("📊 فروش امروز", pie_chart)

            self.charts_layout.addWidget(chart_card, 0, 0)
            self.charts['sales'] = pie_chart

            # شروع انیمیشن با تاخیر (این خط اکنون صرفا چارت را بروزرسانی می‌کند)
            # pie_chart.start_animation() # <--- این خط حذف شد
            
        except Exception as e:
            print(f"خطا در ایجاد چارت فروش: {e}")

    def create_top_drugs_chart(self):
        """چارت محبوب‌ترین داروها"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    d.generic_name,
                    COALESCE(SUM(all_sales.quantity), 0) as total_qty
                FROM (
                    SELECT drug_id, quantity FROM prescription_items pi
                    JOIN prescriptions p ON pi.prescription_id = p.id
                    WHERE DATE(p.date) >= DATE('now', '-7 days')
                    UNION ALL
                    SELECT drug_id, quantity FROM otc_sale_items osi
                    JOIN otc_sales os ON osi.otc_sale_id = os.id
                    WHERE DATE(os.sale_date) >= DATE('now', '-7 days')
                ) AS all_sales
                JOIN drugs d ON all_sales.drug_id = d.id
                GROUP BY d.generic_name
                ORDER BY total_qty DESC
                LIMIT 6
            """)

            drugs_data = cursor.fetchall()
            conn.close()

            if not drugs_data:
                drugs_data = [("داده‌ای نیست", 1)]

            data = [(row[0][:10], float(row[1])) for row in drugs_data]

            bar_chart = BarChart("محبوب‌ترین داروها", data)
            chart_card = ChartCard("💊 محبوب‌ترین داروها (7 روز)", bar_chart)

            self.charts_layout.addWidget(chart_card, 0, 1)
            self.charts['drugs'] = bar_chart

            # شروع انیمیشن با تاخیر (این خط اکنون صرفا چارت را بروزرسانی می‌کند)
            # bar_chart.start_animation() # <--- این خط حذف شد

        except Exception as e:
            print(f"خطا در ایجاد چارت داروها: {e}")

    def create_monthly_trend_chart(self):
        """چارت روند ماهانه"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # فروش 7 روز گذشته
            cursor.execute("""
                SELECT sale_date as day, SUM(daily_total) as daily_sales FROM (
                    SELECT date as sale_date, total_price as daily_total
                    FROM prescriptions
                    WHERE DATE(date) >= DATE('now', '-7 days')
                    UNION ALL
                    SELECT sale_date, total_amount as daily_total
                    FROM otc_sales
                    WHERE DATE(sale_date) >= DATE('now', '-7 days')
                ) AS all_daily_sales
                GROUP BY day
                ORDER BY day
            """)

            trend_data = cursor.fetchall()
            conn.close()

            if not trend_data:
                # داده‌های نمونه
                trend_data = [
                    ("روز 1", 100000),
                    ("روز 2", 150000),
                    ("روز 3", 120000),
                    ("روز 4", 180000),
                    ("روز 5", 200000),
                ]
            else:
                # تبدیل تاریخ از YYYY/MM/DD به "روز X"
                # (این قسمت به تاریخ‌های شمسی در دیتابیس بستگی دارد. اگر میلادی هستند، منطق تبدیل نیاز است.)
                # فعلا فرض می‌کنیم روزها به ترتیب هستند و فقط نام نمایشی می‌دهیم.
                trend_data = [(f"روز {i+1}", float(row[1])) for i, row in enumerate(trend_data)]

            line_chart = LineChart("روند هفتگی فروش", trend_data)
            chart_card = ChartCard("📈 روند فروش هفتگی", line_chart)

            self.charts_layout.addWidget(chart_card, 1, 0)
            self.charts['trend'] = line_chart

            # شروع انیمیشن با تاخیر (این خط اکنون صرفا چارت را بروزرسانی می‌کند)
            # line_chart.start_animation() # <--- این خط حذف شد

        except Exception as e:
            print(f"خطا در ایجاد چارت روند: {e}")

    def create_categories_chart(self):
        """چارت دسته‌بندی داروها"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # گروه‌بندی بر اساس ستون drug_type در جدول drugs
            cursor.execute("""
                SELECT
                    CASE
                        WHEN drug_type = 'PRESCRIPTION' THEN 'با نسخه'
                        WHEN drug_type = 'OTC' THEN 'بدون نسخه'
                        ELSE 'سایر/نامشخص'
                    END as category,
                    COUNT(*) as count
                FROM drugs
                WHERE drug_type IS NOT NULL AND drug_type != ''
                GROUP BY drug_type
                ORDER BY count DESC
            """)

            categories_data = cursor.fetchall()
            conn.close()

            if not categories_data:
                categories_data = [
                    ("بدون نسخه", 50),
                    ("با نسخه", 30),
                    ("سایر", 20)
                ]

            data = [(row[0], float(row[1])) for row in categories_data]

            pie_chart = PieChart("دسته‌بندی داروها", data)
            chart_card = ChartCard("🏷️ دسته‌بندی داروها", pie_chart)

            self.charts_layout.addWidget(chart_card, 1, 1)
            self.charts['categories'] = pie_chart

            # شروع انیمیشن با تاخیر (این خط اکنون صرفا چارت را بروزرسانی می‌کند)
            # pie_chart.start_animation() # <--- این خط حذف شد

        except Exception as e:
            print(f"خطا در ایجاد چارت دسته‌بندی: {e}")

    def refresh_charts(self):
        """بروزرسانی چارت‌ها"""
        try:
            print("در حال بروزرسانی چارت‌ها...")
            self.load_chart_data()
        except Exception as e:
            print(f"خطا در بروزرسانی چارت‌ها: {e}")