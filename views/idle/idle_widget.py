from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from enums.connection_type import ConnectionType

from views.common.base_widget import BaseWidget

class IdleWidget(BaseWidget):
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Idle Screen")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.usb_button = QPushButton("Connect via USB")
        self.usb_button.setObjectName("blueButton")
        self.usb_button.clicked.connect(lambda: self.handle_connect_mcu(ConnectionType.USB))
        layout.addWidget(self.usb_button)

        self.bt_button = QPushButton("Connect via Bluetooth")
        self.bt_button.setObjectName("blueButton")
        self.bt_button.clicked.connect(lambda: self.handle_connect_mcu(ConnectionType.BLUETOOTH))
        layout.addWidget(self.bt_button)

        self.setLayout(layout)

    def reset_ui(self):
        pass

    def handle_connect_mcu(self, connection_type: ConnectionType):
        self.device_controller.start_system_check(connection_type)
