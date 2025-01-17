from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

class IdleWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Idle Screen")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.usb_button = QPushButton("Connect via USB")
        self.usb_button.setObjectName("blueButton")  # For QSS styling
        layout.addWidget(self.usb_button)

        self.bt_button = QPushButton("Connect via Bluetooth")
        self.bt_button.setObjectName("blueButton")  # For QSS styling
        layout.addWidget(self.bt_button)

        self.setLayout(layout)
