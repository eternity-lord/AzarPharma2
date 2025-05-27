# ui/components/modern_card.py
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

class ModernCard(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, title, value, subtitle="", icon_path="", color="#3498db", parent=None):
        super().__init__(parent)
        self.setObjectName("ModernCard")
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color
        
        self.setFixedSize(280, 120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # استایل کارت
        self.setStyleSheet(f"""
            #ModernCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {color}, stop:1 {self._darken_color(color)});
                border: none;
                border-radius: 15px;
                color: white;
                margin: 5px;
            }}
            #ModernCard:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {self._lighten_color(color)}, stop:1 {color});
                transform: scale(1.05);
            }}
            #ModernCard QLabel {{
                background: transparent;
                border: none;
                color: white;
            }}
        """)
        
        self.setup_ui()
    
    def _darken_color(self, color):
        """رنگ را تیره‌تر می‌کند"""
        colors = {
            "#3498db": "#2980b9",  # آبی
            "#e74c3c": "#c0392b",  # قرمز
            "#f39c12": "#e67e22",  # نارنجی
            "#27ae60": "#229954",  # سبز
            "#9b59b6": "#8e44ad",  # بنفش
            "#34495e": "#2c3e50"   # خاکستری
        }
        return colors.get(color, "#2c3e50")
    
    def _lighten_color(self, color):
        """رنگ را روشن‌تر می‌کند"""
        colors = {
            "#3498db": "#5dade2",  # آبی روشن
            "#e74c3c": "#ec7063",  # قرمز روشن
            "#f39c12": "#f8c471",  # نارنجی روشن
            "#27ae60": "#58d68d",  # سبز روشن
            "#9b59b6": "#bb8fce",  # بنفش روشن
            "#34495e": "#5d6d7e"   # خاکستری روشن
        }
        return colors.get(color, "#5d6d7e")
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)
        
        # ردیف بالا: آیکون + عنوان
        top_layout = QHBoxLayout()
        
        # عنوان
        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        # آیکون (اختیاری)
        icon_label = QLabel("📊")  # فعلاً از ایموجی استفاده می‌کنیم
        icon_font = QFont()
        icon_font.setPointSize(16)
        icon_label.setFont(icon_font)
        top_layout.addWidget(icon_label)
        
        layout.addLayout(top_layout)
        
        # مقدار اصلی
        value_label = QLabel(str(self.value))
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(value_label)
        
        # زیرنویس
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_font = QFont()
            subtitle_font.setPointSize(9)
            subtitle_label.setFont(subtitle_font)
            subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
            layout.addWidget(subtitle_label)
        
        layout.addStretch()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def update_value(self, new_value, new_subtitle=""):
        """به‌روزرسانی مقدار کارت"""
        # این متد رو بعداً پیاده‌سازی می‌کنیم
        pass
