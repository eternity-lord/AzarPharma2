# ui/components/notification_system.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QPalette
from enum import Enum
import datetime

class NotificationType(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class NotificationWidget(QFrame):
    closed = pyqtSignal()
    
    def __init__(self, title, message, notification_type=NotificationType.INFO, 
                 auto_hide=True, duration=5000, parent=None):
        super().__init__(parent)
        self.notification_type = notification_type
        self.auto_hide = auto_hide
        self.duration = duration
        
        self.setObjectName("NotificationWidget")
        self.setFixedSize(350, 80)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # تنظیم استایل بر اساس نوع اعلان
        self.setup_style()
        self.setup_ui(title, message)
        self.setup_animation()
        
        # تایمر برای مخفی شدن خودکار
        if auto_hide:
            QTimer.singleShot(duration, self.hide_notification)
    
    def setup_style(self):
        colors = {
            NotificationType.INFO: {"bg": "#3498db", "border": "#2980b9"},
            NotificationType.WARNING: {"bg": "#f39c12", "border": "#e67e22"},
            NotificationType.ERROR: {"bg": "#e74c3c", "border": "#c0392b"},
            NotificationType.SUCCESS: {"bg": "#27ae60", "border": "#229954"}
        }
        
        color_scheme = colors[self.notification_type]
        
        self.setStyleSheet(f"""
            #NotificationWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {color_scheme['bg']}, stop:1 {color_scheme['border']});
                border: 1px solid {color_scheme['border']};
                border-radius: 8px;
                color: white;
                margin: 2px;
            }}
            #NotificationWidget QLabel {{
                background: transparent;
                border: none;
                color: white;
            }}
            #NotificationWidget QPushButton {{
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                color: white;
                padding: 2px 8px;
                font-weight: bold;
            }}
            #NotificationWidget QPushButton:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
        """)
    
    def setup_ui(self, title, message):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 10, 10)
        layout.setSpacing(10)
        
        # آیکون نوع اعلان
        icon_label = QLabel(self.get_type_icon())
        icon_font = QFont()
        icon_font.setPointSize(16)
        icon_label.setFont(icon_font)
        icon_label.setFixedSize(30, 30)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # متن اعلان
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        text_layout.addWidget(title_label)
        
        message_label = QLabel(message)
        message_font = QFont()
        message_font.setPointSize(8)
        message_label.setFont(message_font)
        message_label.setWordWrap(True)
        text_layout.addWidget(message_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # دکمه بستن
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.hide_notification)
        layout.addWidget(close_btn)
    
    def get_type_icon(self):
        icons = {
            NotificationType.INFO: "ℹ️",
            NotificationType.WARNING: "⚠️", 
            NotificationType.ERROR: "❌",
            NotificationType.SUCCESS: "✅"
        }
        return icons[self.notification_type]
    
    def setup_animation(self):
        # انیمیشن ظاهر شدن
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # انیمیشن مخفی شدن
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_animation.finished.connect(self.close)
        
        # شروع انیمیشن ظاهر شدن
        self.fade_in_animation.start()
    
    def hide_notification(self):
        self.fade_out_animation.start()
        self.closed.emit()

class NotificationManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NotificationManager")
        self.notifications = []
        
        # تنظیم موقعیت در گوشه بالا راست
        self.setFixedWidth(370)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Layout برای اعلان‌ها
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        self.layout.addStretch()
        
        # تنظیم موقعیت
        self.update_position()
    
    def update_position(self):
        """به‌روزرسانی موقعیت در گوشه بالا راست"""
        if self.parent():
            parent_rect = self.parent().rect()
            self.move(parent_rect.width() - self.width() - 20, 60)
    
    def show_notification(self, title, message, notification_type=NotificationType.INFO,
                         auto_hide=True, duration=5000):
        """نمایش اعلان جدید"""
        notification = NotificationWidget(
            title, message, notification_type, auto_hide, duration, self
        )
        
        # اضافه کردن به لیست و Layout
        self.notifications.append(notification)
        self.layout.insertWidget(self.layout.count() - 1, notification)
        
        # حذف اعلان بعد از بسته شدن
        notification.closed.connect(lambda: self.remove_notification(notification))
        
        # محدود کردن تعداد اعلان‌ها
        if len(self.notifications) > 5:
            oldest = self.notifications[0]
            oldest.hide_notification()
        
        # نمایش widget اگر مخفی بود
        self.show()
        self.raise_()
        
        return notification
    
    def remove_notification(self, notification):
        """حذف اعلان از لیست"""
        if notification in self.notifications:
            self.notifications.remove(notification)
        
        # مخفی کردن manager اگر اعلانی نمانده
        if not self.notifications:
            self.hide()
    
    def clear_all_notifications(self):
        """پاک کردن تمام اعلان‌ها"""
        for notification in self.notifications[:]:
            notification.hide_notification()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_position()
