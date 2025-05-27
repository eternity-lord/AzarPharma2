# ui/components/barcode_scanner.py

import cv2
import numpy as np
from pyzbar import pyzbar
import qrcode
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QDialog, QTextEdit, QMessageBox, QFrame,
                            QProgressBar, QCheckBox, QSpinBox, QLineEdit)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap, QFont
import io
import base64
from datetime import datetime
import config
from database.db import get_connection


class BarcodeScanner(QThread):
    """Thread برای اسکن بارکد در پس‌زمینه"""
    barcode_detected = pyqtSignal(str, str)  # (type, data)
    frame_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.camera = None
        
    def start_scanning(self):
        """شروع اسکن"""
        self.running = True
        self.start()
        
    def stop_scanning(self):
        """توقف اسکن"""
        self.running = False
        if self.camera is not None:
            self.camera.release()
        self.quit()
        self.wait()
        
    def run(self):
        """حلقه اصلی اسکن"""
        try:
            # تلاش برای باز کردن دوربین
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                self.error_occurred.emit("دوربین در دسترس نیست")
                return
                
            # تنظیمات دوربین
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            while self.running:
                ret, frame = self.camera.read()
                
                if not ret:
                    continue
                    
                # ارسال فریم برای نمایش
                self.frame_ready.emit(frame)
                
                # جستجوی بارکد در فریم
                barcodes = pyzbar.decode(frame)
                
                for barcode in barcodes:
                    # دریافت داده‌های بارکد
                    barcode_data = barcode.data.decode('utf-8')
                    barcode_type = barcode.type
                    
                    # رسم مستطیل دور بارکد
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # ارسال سیگنال تشخیص بارکد
                    self.barcode_detected.emit(barcode_type, barcode_data)
                    
                self.msleep(30)  # 30ms تاخیر
                
        except Exception as e:
            self.error_occurred.emit(f"خطا در اسکن: {str(e)}")
        finally:
            if self.camera is not None:
                self.camera.release()


class QRCodeGenerator:
    """کلاس تولید QR Code"""
    
    @staticmethod
    def generate_prescription_qr(prescription_data):
        """تولید QR Code برای نسخه"""
        try:
            # ایجاد متن QR شامل اطلاعات نسخه
            qr_text = f"""نسخه #{prescription_data.get('prescription_number', 'نامشخص')}
تاریخ: {prescription_data.get('date', 'نامشخص')}
بیمار: {prescription_data.get('patient_name', 'نامشخص')}
مبلغ کل: {prescription_data.get('total_price', 0):,} تومان
آذر فارما - {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
            
            # ایجاد QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_text)
            qr.make(fit=True)
            
            # تولید تصویر
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # تبدیل به bytes
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            return base64.b64encode(img_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"خطا در تولید QR Code: {e}")
            return None
    
    @staticmethod
    def generate_drug_label_qr(drug_data):
        """تولید QR Code برای برچسب دارو"""
        try:
            qr_text = f"""کد: {drug_data.get('generic_code', '')}
نام: {drug_data.get('generic_name', '')}
فرم: {drug_data.get('form', '')}
دوز: {drug_data.get('dosage', '')}
موجودی: {drug_data.get('stock', 0)}
قیمت: {drug_data.get('price_per_unit', 0):,} تومان"""
            
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(qr_text)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            return base64.b64encode(img_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"خطا در تولید QR برچسب دارو: {e}")
            return None


class BarcodeScannerDialog(QDialog):
    """دیالوگ اسکن بارکد"""
    barcode_scanned = pyqtSignal(str, str)  # (type, data)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 اسکن بارکد و QR Code")
        self.setFixedSize(700, 600)
        self.scanner = None
        self.setup_ui()
        
    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # عنوان
        title_label = QLabel("🔍 اسکن بارکد و QR Code")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # ناحیه نمایش دوربین
        self.camera_frame = QFrame()
        self.camera_frame.setFixedSize(640, 480)
        self.camera_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: #ecf0f1;
            }
        """)
        
        camera_layout = QVBoxLayout(self.camera_frame)
        self.camera_label = QLabel("دوربین آماده نیست")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("color: #7f8c8d; font-size: 16px;")
        camera_layout.addWidget(self.camera_label)
        
        layout.addWidget(self.camera_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # دکمه‌های کنترل
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("📷 شروع اسکن")
        self.start_btn.clicked.connect(self.start_scanning)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        
        self.stop_btn = QPushButton("⏹️ توقف اسکن")
        self.stop_btn.clicked.connect(self.stop_scanning)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # نتایج اسکن
        results_group = QFrame()
        results_group.setStyleSheet("""
            QFrame {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
            }
        """)
        results_layout = QVBoxLayout(results_group)
        
        results_title = QLabel("📋 نتایج اسکن:")
        results_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        results_layout.addWidget(results_title)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(100)
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("نتایج اسکن در اینجا نمایش داده می‌شود...")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # دکمه بستن
        close_btn = QPushButton("❌ بستن")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def start_scanning(self):
        """شروع اسکن"""
        try:
            self.scanner = BarcodeScanner()
            self.scanner.barcode_detected.connect(self.on_barcode_detected)
            self.scanner.frame_ready.connect(self.update_camera_frame)
            self.scanner.error_occurred.connect(self.on_scan_error)
            
            self.scanner.start_scanning()
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.camera_label.setText("در حال اسکن...")
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در شروع اسکن: {e}")
    
    def stop_scanning(self):
        """توقف اسکن"""
        if self.scanner:
            self.scanner.stop_scanning()
            self.scanner = None
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.camera_label.setText("اسکن متوقف شد")
    
    def update_camera_frame(self, frame):
        """به‌روزرسانی تصویر دوربین"""
        try:
            # تبدیل فریم OpenCV به QImage
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
            
            # تبدیل به QPixmap و نمایش
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.camera_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"خطا در به‌روزرسانی فریم: {e}")
    
    def on_barcode_detected(self, barcode_type, data):
        """مدیریت تشخیص بارکد"""
        current_time = datetime.now().strftime("%H:%M:%S")
        result_text = f"[{current_time}] نوع: {barcode_type} | داده: {data}\n"
        
        self.results_text.append(result_text)
        self.barcode_scanned.emit(barcode_type, data)
        
        # جستجوی خودکار دارو در دیتابیس
        self.search_drug_by_barcode(data)
    
    def search_drug_by_barcode(self, barcode_data):
        """جستجوی دارو با بارکد"""
        try:
            conn = get_connection(config.DB_PATH)
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # جستجو در جدول داروها
            cursor.execute("""
                SELECT generic_name, generic_code, form, dosage, stock, price_per_unit
                FROM drugs 
                WHERE generic_code = ? OR en_brand_name LIKE ?
            """, (barcode_data, f"%{barcode_data}%"))
            
            result = cursor.fetchone()
            
            if result:
                drug_info = f"""
💊 دارو پیدا شد:
نام: {result[0]}
کد: {result[1]}
فرم: {result[2]}
دوز: {result[3]}
موجودی: {result[4]}
قیمت: {result[5]:,} تومان
"""
                self.results_text.append(drug_info)
                
                # نمایش اطلاعات در پیغام
                QMessageBox.information(self, "دارو پیدا شد", drug_info)
            else:
                self.results_text.append("❌ دارو با این بارکد پیدا نشد\n")
                
            conn.close()
            
        except Exception as e:
            print(f"خطا در جستجوی دارو: {e}")
            self.results_text.append(f"❌ خطا در جستجو: {e}\n")
    
    def on_scan_error(self, error_message):
        """مدیریت خطای اسکن"""
        self.camera_label.setText(f"خطا: {error_message}")
        QMessageBox.critical(self, "خطای اسکن", error_message)
        self.stop_scanning()
    
    def closeEvent(self, event):
        """مدیریت بستن پنجره"""
        self.stop_scanning()
        event.accept()
