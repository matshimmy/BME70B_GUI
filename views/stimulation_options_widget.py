from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QComboBox
)
from PyQt5.QtCore import Qt

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine

class StimulationOptionsWidget(QWidget):
    def __init__(self, state_machine : StateMachine, device_controller: DeviceController):
        super().__init__()
        self.device_controller = device_controller
        self.state_machine = state_machine

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        options_layout = QHBoxLayout()
        options_layout.setAlignment(Qt.AlignCenter)

        # Horizontal spacer
        options_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        # ---------------------------
        # Drop-down (ComboBox) for Frequency
        # ---------------------------
        self.frequency_label = QLabel("Frequency:")
        self.frequency_label.setAlignment(Qt.AlignCenter)

        self.combo_frequency = QComboBox()
        self.combo_frequency.addItems(["20 Hz", "35 Hz", "50 Hz", "75 Hz"])
        self.combo_frequency.setCurrentIndex(1)  # default "35 Hz"

        frequency_layout = QVBoxLayout()
        frequency_layout.setAlignment(Qt.AlignCenter)
        frequency_layout.addWidget(self.frequency_label)
        frequency_layout.addWidget(self.combo_frequency)
        options_layout.addLayout(frequency_layout)

        # Horizontal spacer
        options_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        # ---------------------------
        # Drop-down (ComboBox) for Pulse Width
        # ---------------------------
        self.pulse_width_label = QLabel("Pulse Width:")
        self.pulse_width_label.setAlignment(Qt.AlignCenter)

        self.combo_pulse_width = QComboBox()
        self.combo_pulse_width.addItems([f"{i} µs" for i in range(200, 501, 100)])
        self.combo_pulse_width.setCurrentIndex(1)  # default "300 µs"

        pulse_width_layout = QVBoxLayout()
        pulse_width_layout.setAlignment(Qt.AlignCenter)
        pulse_width_layout.addWidget(self.pulse_width_label)
        pulse_width_layout.addWidget(self.combo_pulse_width)
        options_layout.addLayout(pulse_width_layout)

        # Horizontal spacer
        options_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        # ---------------------------
        # Drop-down (ComboBox) for Current
        # ---------------------------
        self.current_label = QLabel("Current:")
        self.current_label.setAlignment(Qt.AlignCenter)

        self.combo_current = QComboBox()
        self.combo_current.addItems([f"{i} mA" for i in range(15, 61, 15)])
        self.combo_current.setCurrentIndex(1)  # default "30 mA"

        current_layout = QVBoxLayout()
        current_layout.setAlignment(Qt.AlignCenter)
        current_layout.addWidget(self.current_label)
        current_layout.addWidget(self.combo_current)
        options_layout.addLayout(current_layout)

        # Horizontal spacer
        options_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
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
        self.start_button.clicked.connect(self.on_start_stimulation)
        bottom_layout.addWidget(self.start_button)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def on_start_stimulation(self):
        frequency_str = self.combo_frequency.currentText()
        # Convert "30 Hz" to integer or store the string
        frequency = int(frequency_str.split()[0])

        pulse_width_str = self.combo_pulse_width.currentText()
        # Convert "300 µs" to integer or store the string
        pulse_width = int(pulse_width_str.split()[0])

        current_str = self.combo_current.currentText()
        # Convert "30 mA" to integer or store the string
        current = int(current_str.split()[0])

        # Update state machine
        self.state_machine.update_stimulation_options(frequency, pulse_width, current)

        # Finally start the stimulation
        self.device_controller.start_stimulation()
