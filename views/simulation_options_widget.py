from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QRadioButton, QComboBox, QButtonGroup
)
from PyQt5.QtCore import Qt

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine
from enums.simulation_type import SimulationType

class SimulationOptionsWidget(QWidget):
    def __init__(self, state_machine : StateMachine, device_controller: DeviceController):
        super().__init__()
        self.device_controller = device_controller
        self.state_machine = state_machine

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        options_layout = QVBoxLayout()
        options_layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Simulation Type")
        self.label.setAlignment(Qt.AlignCenter)
        options_layout.addWidget(self.label)

        # ---------------------------
        # Radio Buttons for "Template" vs. "Full Signal"
        # ---------------------------
        radio_layout = QHBoxLayout()
        radio_layout.setAlignment(Qt.AlignCenter)

        self.template_radio = QRadioButton(SimulationType.TEMPLATE.value)
        self.full_signal_radio = QRadioButton(SimulationType.FULL_SIGNAL.value)

        self.template_radio.setChecked(True)

        radio_layout.addWidget(self.template_radio)
        radio_layout.addWidget(self.full_signal_radio)

        options_layout.addLayout(radio_layout)

        # QButtonGroup so we can see which button is checked more easily
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.template_radio, 0)
        self.radio_group.addButton(self.full_signal_radio, 1)

        # ---------------------------
        # Drop-down (ComboBox) for transmission rate
        # ---------------------------
        self.transmission_label = QLabel("Transmission Rate:")
        self.transmission_label.setAlignment(Qt.AlignCenter)

        self.combo_transmission = QComboBox()
        self.combo_transmission.addItems(["30 Hz", "100 Hz", "200 Hz", "500 Hz"])
        self.combo_transmission.setCurrentIndex(1)  # default "100 Hz"

        transmission_layout = QHBoxLayout()
        transmission_layout.setAlignment(Qt.AlignCenter)
        transmission_layout.addWidget(self.transmission_label)
        transmission_layout.addWidget(self.combo_transmission)
        options_layout.addLayout(transmission_layout)

        # Add artifacts checkboxes with the options of "Muscle", "Random Movement", and "60 Hz Grid"

        # Add custom noise by selecting a csv file

        main_layout.addLayout(options_layout)

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

        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("greenButton")
        self.start_button.clicked.connect(self.on_start_simulation)
        bottom_layout.addWidget(self.start_button)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def on_start_simulation(self):
        """
        Called when the user clicks "Start."
        
        """
        selected_radio_id = self.radio_group.checkedId()
        if selected_radio_id == 0:
            simulation_type = SimulationType.TEMPLATE
        else:
            simulation_type = SimulationType.FULL_SIGNAL

        transmission_rate_str = self.combo_transmission.currentText()
        # Convert "30 Hz" to integer or store the string
        transmission_rate = int(transmission_rate_str.split()[0])

        # Update state machine
        self.state_machine.update_simulation_options(simulation_type, transmission_rate)

        # Finally start the simulation
        self.device_controller.start_simulation()
