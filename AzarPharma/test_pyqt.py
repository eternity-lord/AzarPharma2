import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QObject, pyqtProperty, Qt, QTimer, QPropertyAnimation
import PyQt6

print(f"Python Version: {sys.version}")
print(f"PyQt6 Version: {PyQt6.QtCore.PYQT_VERSION_STR}")
print(f"QObject type: {type(QObject)}")
print(f"pyqtProperty type: {type(pyqtProperty)}")

class MyWidget(QWidget):
    _my_value = 0

    @pyqtProperty(int)
    def myValue(self):
        return self._my_value

    @myValue.setter
    def setMyValue(self, value):
        if self._my_value != value:
            self._my_value = value
            print(f"MyValue changed to: {self._my_value}")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Test")
        layout = QVBoxLayout(self)
        self.label = QLabel("Animating...")
        layout.addWidget(self.label)

        self.anim = QPropertyAnimation(self, b"myValue")
        self.anim.setDuration(2000)
        self.anim.setStartValue(0)
        self.anim.setEndValue(100)
        self.anim.setLoopCount(-1)
        self.anim.start()

app = QApplication(sys.argv)
window = MyWidget()
window.show()
sys.exit(app.exec())