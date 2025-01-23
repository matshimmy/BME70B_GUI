from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QRadioButton, QComboBox, QButtonGroup
)
from PyQt5.QtCore import Qt

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine
from enums.acquisition_type import AcquisitionType

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
        # Radio Buttons for "Template" vs. "Full Signal"
        # ---------------------------
        self.label = QLabel("Acquisition Type")
        self.label.setAlignment(Qt.AlignCenter)
        options_layout.addWidget(self.label)

        radio_layout = QHBoxLayout()
        radio_layout.setAlignment(Qt.AlignCenter)

        self.template_radio = QRadioButton(AcquisitionType.TEMPLATE.value)
        self.full_signal_radio = QRadioButton(AcquisitionType.FULL_SIGNAL.value)

        self.template_radio.setChecked(True)

        radio_layout.addWidget(self.template_radio)
        radio_layout.addWidget(self.full_signal_radio)

        options_layout.addLayout(radio_layout)

        # QButtonGroup so we can see which button is checked more easily
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.template_radio, 0)
        self.radio_group.addButton(self.full_signal_radio, 1)

        # ---------------------------
        # Drop-down (ComboBox) for sampling rates
        # ---------------------------
        self.sampling_label = QLabel("Sampling Rate:")
        self.sampling_label.setAlignment(Qt.AlignCenter)

        self.combo_sampling = QComboBox()
        self.combo_sampling.addItems(["30 Hz", "100 Hz", "200 Hz", "500 Hz"])
        self.combo_sampling.setCurrentIndex(1)  # default "100 Hz"

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
        """
        Called when the user clicks "Start."
        Gather the selected acquisition type (template/full) and sampling rate,
        and then pass them to the device controller or state machine as needed.
        """
        selected_radio_id = self.radio_group.checkedId()
        if selected_radio_id == 0:
            acquisition_type = AcquisitionType.TEMPLATE
        else:
            acquisition_type = AcquisitionType.FULL_SIGNAL

        sampling_rate_str = self.combo_sampling.currentText()
        # Convert "30 Hz" to integer or store the string
        sampling_rate = int(sampling_rate_str.split()[0])

        # Update state machine
        self.state_machine.update_acquisition_options(acquisition_type, sampling_rate)

        # Finally start the acquisition
        self.device_controller.start_acquisition()
