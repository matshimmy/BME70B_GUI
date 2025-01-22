from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QRadioButton, QComboBox, QButtonGroup,
    QCheckBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine
from enums.simulation_type import SimulationType

class SimulationOptionsWidget(QWidget):
    def __init__(self, state_machine: StateMachine, device_controller: DeviceController):
        super().__init__()
        self.device_controller = device_controller
        self.state_machine = state_machine

        # Will store the chosen CSV path
        self.custom_noise_file = None

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

        # Default to Template
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

        # ---------------------------
        # CheckBoxes for artifacts
        # ---------------------------
        artifacts_label = QLabel("Artifacts:")
        artifacts_label.setAlignment(Qt.AlignCenter)
        options_layout.addWidget(artifacts_label)

        artifacts_layout = QVBoxLayout()
        artifacts_layout.setAlignment(Qt.AlignCenter)

        self.muscle_checkbox = QCheckBox("Muscle")
        self.random_movement_checkbox = QCheckBox("Random Movement")
        self.sixty_hz_checkbox = QCheckBox("60 Hz Grid")

        artifacts_layout.addWidget(self.muscle_checkbox)
        artifacts_layout.addWidget(self.random_movement_checkbox)
        artifacts_layout.addWidget(self.sixty_hz_checkbox)

        options_layout.addLayout(artifacts_layout)

        # ---------------------------
        # Custom Noise File (CSV)
        # ---------------------------
        custom_noise_layout = QVBoxLayout()
        custom_noise_layout.setAlignment(Qt.AlignCenter)
        self.custom_noise_file = None

        self.custom_noise_label = QLabel("Custom Noise CSV:")
        self.custom_noise_label.setAlignment(Qt.AlignCenter)
        custom_noise_layout.addWidget(self.custom_noise_label)

        self.custom_noise_path = QLabel("[None Selected]")
        self.custom_noise_path.setWordWrap(False)
        self.custom_noise_path.setFixedWidth(300)
        self.custom_noise_path.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.custom_noise_path.setAlignment(Qt.AlignCenter)
        self.custom_noise_path.setStyleSheet("color: gray;")

        custom_noise_layout.addWidget(self.custom_noise_path)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.setFixedWidth(100)
        self.browse_button.clicked.connect(self.select_csv_file)
        custom_noise_layout.addWidget(self.browse_button)

        options_layout.addLayout(custom_noise_layout)

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
        self.start_button.clicked.connect(self.on_start_simulation)
        bottom_layout.addWidget(self.start_button)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    # ---------------------------
    # File Dialog for Selecting a CSV
    # ---------------------------
    def select_csv_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv)"
        )
        if file_name:
            self.custom_noise_file = file_name
            # Ellipsize
            elided = self.elide_text(file_name, self.custom_noise_path.width())
            self.custom_noise_path.setText(elided)
        else:
            self.custom_noise_file = None
            self.custom_noise_path.setText("[None Selected]")

    def elide_text(self, text, max_width):
        """
        Returns an elided version of 'text' that does not exceed 'max_width' px,
        using middle-ellipsizing (e.g., "C:/some/.../file.csv").
        """
        fm = QFontMetrics(self.custom_noise_path.font())
        return fm.elidedText(text, Qt.ElideMiddle, max_width)

    # ---------------------------
    # Start Simulation
    # ---------------------------
    def on_start_simulation(self):
        """
        Called when the user clicks "Start."
        Gather radio button, transmission rate, artifacts checkboxes, and custom CSV file.
        Pass them to the state machine/device controller, then start the simulation.
        """

        selected_radio_id = self.radio_group.checkedId()
        if selected_radio_id == 0:
            simulation_type = SimulationType.TEMPLATE
        else:
            simulation_type = SimulationType.FULL_SIGNAL

        # Transmission Rate (e.g., "100 Hz" -> 100)
        transmission_rate_str = self.combo_transmission.currentText()
        transmission_rate = int(transmission_rate_str.split()[0])

        # Artifact checkboxes
        muscle = self.muscle_checkbox.isChecked()
        random_movement = self.random_movement_checkbox.isChecked()
        sixty_hz = self.sixty_hz_checkbox.isChecked()

        # Update the state machine with all selected options
        self.state_machine.update_simulation_options(
            simulation_type,
            transmission_rate,
            muscle_artifact=muscle,
            random_artifact=random_movement,
            sixty_hz_artifact=sixty_hz,
            custom_csv=self.custom_noise_file
        )

        # Finally start the simulation
        self.device_controller.start_simulation()
