from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel
)
from PyQt5.QtCore import Qt

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine

class RunningAcquisitionWidget(QWidget):
    def __init__(self, state_machine : StateMachine, device_controller: DeviceController):
        super().__init__()
        self.device_controller = device_controller
        self.state_machine = state_machine

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.label = QLabel("Signal acquisition algorithm to be implemented in Phase II")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        # Spacer below the buttons
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom layout for the Disconnect and Start buttons
        bottom_layout = QHBoxLayout()

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("redButton")  # For QSS styling
        self.disconnect_button.clicked.connect(self.device_controller.disconnect_device)
        bottom_layout.addWidget(self.disconnect_button)

        # Spacer to push the Start button to the right
        bottom_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.save_data_button = QPushButton("Save Data")
        self.save_data_button.setObjectName("amberButton")  # For QSS styling
        bottom_layout.addWidget(self.save_data_button)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)
