from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QComboBox
)
from PyQt5.QtCore import Qt

from views.common.base_widget import BaseWidget

class StimulationOptionsWidget(BaseWidget):
    def _setup_ui(self):

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
        # Drop-down (ComboBox) for Duty Cycle
        # ---------------------------
        self.duty_cycle_label = QLabel("Duty Cycle:")
        self.duty_cycle_label.setAlignment(Qt.AlignCenter)

        self.combo_duty_cycle = QComboBox()
        self.combo_duty_cycle.addItems([f"{i} %" for i in range(10, 101, 10)])
        self.combo_duty_cycle.setCurrentIndex(1)  # default "50 %"

        duty_cycle_layout = QVBoxLayout()
        duty_cycle_layout.setAlignment(Qt.AlignCenter)
        duty_cycle_layout.addWidget(self.duty_cycle_label)
        duty_cycle_layout.addWidget(self.combo_duty_cycle)
        options_layout.addLayout(duty_cycle_layout)

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

        duty_cycle_str = self.combo_duty_cycle.currentText()
        # Convert "50 %" to integer or store the string
        duty_cycle = int(duty_cycle_str.split()[0])

        # Update state machine
        self.state_machine.update_stimulation_options(frequency, duty_cycle)

        # Finally start the stimulation
        self.device_controller.start_stimulation()

    def reset_ui(self):
        pass
