from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine

class AcquisitionOptionsWidget(QWidget):
    def __init__(self, state_machine : StateMachine, device_controller: DeviceController):
        super().__init__()
        self.device_controller = device_controller
        self.state_machine = state_machine

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # ---------------------------
        # Back Button at the Top-Left
        # ---------------------------
        back_button_layout = QHBoxLayout()
        self.back_button = QPushButton(" ← ")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.state_machine.on_back_options_clicked)

        # Add an expanding spacer to push the button to the left
        back_button_layout.addWidget(self.back_button)
        back_button_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Add the back button layout to the main layout
        main_layout.addLayout(back_button_layout)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        options_layout = QVBoxLayout()
        options_layout.setAlignment(Qt.AlignCenter)

        # ---------------------------
        # CheckBox for "Template"
        # ---------------------------
        self.template_checkbox = QCheckBox("Calculate Template Plot")
        self.template_checkbox.setChecked(True)
        options_layout.addWidget(self.template_checkbox)

        # ---------------------------
        # Drop-down (ComboBox) for sampling rates
        # ---------------------------
        self.sampling_label = QLabel("Sampling Rate:")
        self.sampling_label.setAlignment(Qt.AlignCenter)

        self.combo_sampling = QComboBox()
        self.combo_sampling.addItems(["5 Hz", "30 Hz", "100 Hz", "250 Hz", "500 Hz"])
        self.combo_sampling.setCurrentIndex(3)

        sampling_layout = QHBoxLayout()
        sampling_layout.setAlignment(Qt.AlignCenter)
        sampling_layout.addWidget(self.sampling_label)
        sampling_layout.addWidget(self.combo_sampling)
        options_layout.addLayout(sampling_layout)

        main_layout.addLayout(options_layout)

        # Spacer below the buttons
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom layout for the Disconnect and Start buttons
        bottom_layout = QHBoxLayout()

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("redButton")  # For QSS styling
        self.disconnect_button.clicked.connect(self.device_controller.start_graceful_disconnect)
        bottom_layout.addWidget(self.disconnect_button)

        # Spacer to push the Start button to the right
        bottom_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("greenButton")
        self.start_button.clicked.connect(self.on_start_acquisition)
        bottom_layout.addWidget(self.start_button)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def on_start_acquisition(self):
        sampling_rate_str = self.combo_sampling.currentText()

        sampling_rate = float(sampling_rate_str.split()[0])

        # Update state machine
        self.state_machine.update_acquisition_options(self.template_checkbox.isChecked(), sampling_rate)

        # Finally start the acquisition
        self.device_controller.start_acquisition()
