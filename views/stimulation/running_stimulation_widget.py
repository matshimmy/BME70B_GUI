from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel
)
from PyQt5.QtCore import Qt

from views.common.base_widget import BaseWidget

class RunningStimulationWidget(BaseWidget):
    def _setup_ui(self):

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.label = QLabel("Signal stimulation algorithm to be implemented in Phase IV")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

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

        self.pause_button = QPushButton("Pause")
        self.pause_button.setObjectName("amberButton")  # For QSS styling
        bottom_layout.addWidget(self.pause_button)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def reset_ui(self):
        pass
