from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel
)
from PyQt5.QtCore import Qt

from views.common.base_widget import BaseWidget

class RunningStimulationWidget(BaseWidget):
    # Class-level constants for label text
    STIMULATING_TEXT = "CAUTION: STIMULATING..."
    READY_TEXT = "CAUTION: Pressing button below will start STIMULATION"

    def _setup_ui(self):

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        top_row_layout = self._setup_top_row()
        main_layout.addLayout(top_row_layout)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.label = QLabel(self.READY_TEXT)
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        self.start_button = QPushButton("Start Stimulation")
        self.start_button.setObjectName("greenButton")  # For QSS styling
        self.start_button.clicked.connect(self.toggle_stimulation)
        main_layout.addWidget(self.start_button)

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

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def _setup_top_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        # Back button
        self.back_button = QPushButton(" ← ")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.back)
        layout.addWidget(self.back_button)

        # Spacer for centering
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        return layout
    
    def toggle_stimulation(self):
        if self.model.stimulation_running:
            self.start_button.setText("Stop Stimulation")
            self.start_button.setObjectName("redButton")
            self._update_button_style(self.start_button)
            self.label.setText(self.STIMULATING_TEXT)

            # Disconnect button
            self.disconnect_button.setEnabled(False)
            self.disconnect_button.setObjectName("greyButton")
            self._update_button_style(self.disconnect_button)

            self.back_button.setEnabled(False)
            self.model.stimulation_running = False
        else:
            self.start_button.setText("Start Stimulation")
            self.start_button.setObjectName("greenButton")
            self._update_button_style(self.start_button)
            self.label.setText(self.READY_TEXT)

            # Disconnect button
            self.disconnect_button.setEnabled(True)
            self.disconnect_button.setObjectName("redButton")
            self._update_button_style(self.disconnect_button)

            self.back_button.setEnabled(True)
            self.model.stimulation_running = True

    def reset_ui(self):
        pass

    def _update_button_style(self, button: QPushButton):
        """Force a style refresh for a button that changes objectName."""
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    # -------------------------------------------------------------------------
    #  Navigation
    # -------------------------------------------------------------------------
    def back(self):
        self.device_controller.stop_stimulation()
        self.state_machine.transition_to_stimulation_options()
