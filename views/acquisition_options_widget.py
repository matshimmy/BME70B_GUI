from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QLabel
)
from PyQt5.QtCore import Qt

from controllers.device_controller import DeviceController

class AcquisitionOptionsWidget(QWidget):
    def __init__(self, device_controller : DeviceController):
        super().__init__()

        self.device_controller = device_controller
        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        options_layout = QVBoxLayout()
        options_layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Acquisition Type")
        self.label.setAlignment(Qt.AlignCenter)
        options_layout.addWidget(self.label)

        # Add radio buttons for template for full signal

        # Add drop down menu with sampling rates 30 Hz, 100 Hz, 200 Hz, 500 Hz

        main_layout.addLayout(options_layout)

        # Spacer below the buttons
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom layout for the Disconnect button
        bottom_layout = QHBoxLayout()

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("redButton")  # For QSS styling
        self.disconnect_button.clicked.connect(self.device_controller.disconnect_device)
        bottom_layout.addWidget(self.disconnect_button)

        # Spacer to center the Simulation button
        center_spacer_left = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        bottom_layout.addSpacerItem(center_spacer_left)

        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("greenButton")
        self.start_button.clicked.connect(self.device_controller.start_acquisition)
        bottom_layout.addWidget(self.start_button)

        # Add bottom layout to main layout
        main_layout.addLayout(bottom_layout)

        # Set the main layout
        self.setLayout(main_layout)
