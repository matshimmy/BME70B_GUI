from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QRadioButton, QComboBox, QButtonGroup,
    QCheckBox, QFileDialog, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics

from views.common.base_widget import BaseWidget
from enums.simulation_type import SimulationType

class SimulationOptionsWidget(BaseWidget):
    def _setup_ui(self):
        self.template_model = self.state_machine.model.template_model
        self.signal_simulation = self.state_machine.model.signal_simulation

        # ---------------------------
        # Main Layout
        # ---------------------------
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # ---------------------------
        # Back Button at the Top-Left
        # ---------------------------
        back_button_layout = QHBoxLayout()
        self.back_button = QPushButton(" ← ")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.state_machine.on_back_options_clicked)

        back_button_layout.addWidget(self.back_button)
        back_button_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(back_button_layout)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # ---------------------------
        # Options Layout
        # ---------------------------
        options_layout = QVBoxLayout()
        options_layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Simulation Type")
        self.label.setAlignment(Qt.AlignCenter)
        options_layout.addWidget(self.label)

        # ---------------------------
        # Radio Buttons (Template vs. Full Signal)
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

        # Group the radio buttons
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.template_radio, 0)
        self.radio_group.addButton(self.full_signal_radio, 1)

        # ---------------------------
        # Custom Signal File (CSV)
        # ---------------------------
        self.custom_signal_container = QWidget()
        self.custom_signal_layout = QVBoxLayout()
        self.custom_signal_layout.setAlignment(Qt.AlignCenter)

        self.custom_signal_file = None

        self.custom_signal_label = QLabel("Custom Signal CSV:")
        self.custom_signal_label.setAlignment(Qt.AlignCenter)
        self.custom_signal_layout.addWidget(self.custom_signal_label)

        self.custom_signal_path = QLabel("[None Selected]")
        self.custom_signal_path.setWordWrap(False)
        self.custom_signal_path.setFixedWidth(300)
        self.custom_signal_path.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.custom_signal_path.setAlignment(Qt.AlignCenter)
        self.custom_signal_path.setStyleSheet("color: gray;")
        self.custom_signal_layout.addWidget(self.custom_signal_path)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.setFixedWidth(100)
        self.browse_button.clicked.connect(self.select_csv_file)
        self.custom_signal_layout.addWidget(self.browse_button)

        self.custom_signal_container.setLayout(self.custom_signal_layout)
        options_layout.addWidget(self.custom_signal_container)

        # Initially hidden (since Template is the default)
        self.custom_signal_container.setVisible(False)
        self.full_signal_radio.toggled.connect(self.toggle_radio_layout)

        # ---------------------------
        # Template Length Spin Box
        # ---------------------------
        self.template_length_container = QWidget()
        template_length_layout = QHBoxLayout()
        self.template_length_label = QLabel("Template Length (ms):")
        self.template_length_label.setAlignment(Qt.AlignCenter)

        self.template_length_spinbox = QSpinBox()
        self.template_length_spinbox.setRange(500, 1000)
        self.template_length_spinbox.setValue(int(self.template_model._duration * 1000))
        self.template_length_spinbox.valueChanged.connect(self.template_model.set_duration_ms)

        template_length_layout.addWidget(self.template_length_label)
        template_length_layout.addWidget(self.template_length_spinbox)
        self.template_length_container.setLayout(template_length_layout)
        options_layout.addWidget(self.template_length_container)

        self.template_length_container.setVisible(True)
        # ---------------------------
        # Transmission Rate ComboBox
        # ---------------------------
        self.transmission_label = QLabel("Transmission Rate:")
        self.transmission_label.setAlignment(Qt.AlignCenter)

        self.combo_transmission = QComboBox()
        self.combo_transmission.addItems(["10 Hz", "30 Hz", "100 Hz", "200 Hz", "500 Hz", "1000 Hz", "2000 Hz"])
        self.combo_transmission.setCurrentIndex(1)  # default "100 Hz"

        transmission_layout = QHBoxLayout()
        transmission_layout.setAlignment(Qt.AlignCenter)
        transmission_layout.addWidget(self.transmission_label)
        transmission_layout.addWidget(self.combo_transmission)
        options_layout.addLayout(transmission_layout)

        # ---------------------------
        # Artifacts Checkboxes
        # ---------------------------
        artifacts_label = QLabel("Artifacts:")
        artifacts_label.setAlignment(Qt.AlignCenter)
        options_layout.addWidget(artifacts_label)

        artifacts_layout = QVBoxLayout()
        artifacts_layout.setAlignment(Qt.AlignCenter)

        self.muscle_checkbox = QCheckBox("Muscle EMG")
        self.random_movement_checkbox = QCheckBox("Random Movement")
        self.sixty_hz_checkbox = QCheckBox("60 Hz Grid")

        artifacts_layout.addWidget(self.muscle_checkbox)
        artifacts_layout.addWidget(self.random_movement_checkbox)
        artifacts_layout.addWidget(self.sixty_hz_checkbox)
        options_layout.addLayout(artifacts_layout)

        # Add the options layout to the main layout
        main_layout.addLayout(options_layout)

        # Spacer below
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # ---------------------------
        # Bottom Buttons Layout
        # ---------------------------
        bottom_layout = QHBoxLayout()

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("redButton")  # For QSS styling
        self.disconnect_button.clicked.connect(self.device_controller.start_graceful_disconnect)
        bottom_layout.addWidget(self.disconnect_button)

        bottom_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("greenButton")
        self.start_button.clicked.connect(self.on_start_simulation)
        bottom_layout.addWidget(self.start_button)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        self._update_start_button_state()

    # ---------------------------
    # Toggle the Custom Signal Container
    # ---------------------------
    def toggle_radio_layout(self, checked: bool):
        self.custom_signal_container.setVisible(checked)
        self.template_length_container.setVisible(not checked)
        self._update_start_button_state()

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
            self.custom_signal_file = file_name
            # Ellipsize long file paths
            elided = self.elide_text(file_name, self.custom_signal_path.width())
            self.custom_signal_path.setText(elided)
        else:
            self.custom_signal_file = None
            self.custom_signal_path.setText("[None Selected]")

        self._update_start_button_state()

    # ---------------------------
    # Helper: Update "Start" Button State
    # ---------------------------
    def _update_start_button_state(self):
        # Full Signal requires a CSV
        full_signal_chosen = self.full_signal_radio.isChecked()
        if full_signal_chosen and not self.custom_signal_file:
            # No file selected yet
            self.start_button.setEnabled(False)
            self.start_button.setText("Select custom signal CSV file.")
            self.start_button.setObjectName("greyButton")
        else:
            # Either Template mode or CSV is provided
            self.start_button.setEnabled(True)
            self.start_button.setText("Next")
            self.start_button.setObjectName("greenButton")

        self._update_button_style(self.start_button)

    # ---------------------------
    # Helper: Force Re-polish Button Style
    # ---------------------------
    def _update_button_style(self, button: QPushButton):
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    # ---------------------------
    # Helper: Ellide Text
    # ---------------------------
    def elide_text(self, text: str, max_width: int) -> str:
        """
        Returns an elided version of 'text' that does not exceed 'max_width' px,
        using middle-ellipsizing (e.g., "C:/some/.../file.csv").
        """
        fm = QFontMetrics(self.custom_signal_path.font())
        return fm.elidedText(text, Qt.ElideMiddle, max_width)

    # ---------------------------
    # Start Simulation
    # ---------------------------
    def on_start_simulation(self):
        # Transmission Rate (e.g., "100 Hz" -> 100)
        transmission_rate_str = self.combo_transmission.currentText()
        transmission_rate = int(transmission_rate_str.split()[0])
        # Artifact checkboxes
        muscle = self.muscle_checkbox.isChecked()
        random_movement = self.random_movement_checkbox.isChecked()
        sixty_hz = self.sixty_hz_checkbox.isChecked()

        self.signal_simulation.reset()
        self.signal_simulation.set_artifacts(muscle, random_movement, sixty_hz)
        selected_radio_id = self.radio_group.checkedId()
        if selected_radio_id == 0:
            simulation_type = SimulationType.TEMPLATE
            self.template_model.set_transmission_rate(transmission_rate)
            self.template_model.set_duration_ms(self.template_length_spinbox.value())
        else:
            simulation_type = SimulationType.FULL_SIGNAL
            self.signal_simulation.load_csv_data(self.custom_signal_file, transmission_rate)

        self.signal_simulation.set_transmission_rate(transmission_rate)

        self.model.set_simulation_type(simulation_type)
        # Just transition to the running simulation widget without starting simulation
        self.state_machine.transition_to_running_simulation()

    def reset_ui(self):
        pass
