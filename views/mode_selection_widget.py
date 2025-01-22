from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine

class ModeSelectionWidget(QWidget):
    def __init__(self, state_machine : StateMachine, device_controller: DeviceController):
        super().__init__()

        self.device_controller = device_controller
        self.state_machine = state_machine

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Row with three buttons spaced dynamically
        button_row = QHBoxLayout()

        self.acquisition_button = QPushButton("Acquisition")
        self.acquisition_button.setObjectName("blueButton")  # For QSS styling
        self.acquisition_button.clicked.connect(self.state_machine.transition_to_acquisition_options)
        button_row.addWidget(self.acquisition_button)

        # Spacer to center the Simulation button
        center_spacer_left = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_row.addSpacerItem(center_spacer_left)

        self.simulation_button = QPushButton("Simulation")
        self.simulation_button.setObjectName("blueButton")  # For QSS styling
        self.simulation_button.clicked.connect(self.state_machine.transition_to_simulation_options)
        button_row.addWidget(self.simulation_button)

        center_spacer_right = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_row.addSpacerItem(center_spacer_right)

        # Stimulation button and spacer to push it to the right
        self.stimulation_button = QPushButton("Stimulation")
        self.stimulation_button.setObjectName("amberButton")  # For QSS styling
        self.stimulation_button.clicked.connect(self.state_machine.transition_to_stimulation_options)
        button_row.addWidget(self.stimulation_button)

        main_layout.addLayout(button_row)

        # Spacer below the buttons
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom layout for the Disconnect button
        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignLeft)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("redButton")  # For QSS styling
        self.disconnect_button.clicked.connect(self.device_controller.start_graceful_disconnect)
        bottom_layout.addWidget(self.disconnect_button)

        # Add bottom layout to main layout
        main_layout.addLayout(bottom_layout)

        # Set the main layout
        self.setLayout(main_layout)
