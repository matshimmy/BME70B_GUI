from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

from controllers.device_controller import DeviceController
from enums.connection_type import ConnectionType

class IdleWidget(QWidget):
    def __init__(self, device_controller : DeviceController):
        super().__init__()

        self.device_controller = device_controller

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Idle Screen")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.usb_button = QPushButton("Connect via USB")
        self.usb_button.setObjectName("blueButton")  # For QSS styling
        self.usb_button.clicked.connect(lambda: self.handle_connect_mcu(ConnectionType.USB))
        layout.addWidget(self.usb_button)

        self.bt_button = QPushButton("Connect via Bluetooth")
        self.bt_button.setObjectName("blueButton")  # For QSS styling
        self.bt_button.clicked.connect(lambda: self.handle_connect_mcu(ConnectionType.BLUETOOTH))
        layout.addWidget(self.bt_button)

        self.setLayout(layout)

    def handle_connect_mcu(self, connection_type : ConnectionType):
        self.device_controller.start_system_check(connection_type)
