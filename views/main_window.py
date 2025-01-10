from PyQt5.QtWidgets import (
    QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt

# Import your states
from controllers.states import AppState

windowTitlePrefix = "BME70B App | "

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize list of states
        self.states = [
            AppState.IDLE,
            AppState.SYSTEM_CHECK,
            AppState.MODE_SELECTION,
            AppState.OPTIONS,
            AppState.RUNNING
        ]
        self.state_index = 0
        self.state = self.states[self.state_index]

        # Set up main window
        self.setWindowTitle(windowTitlePrefix + self.state.value)
        self.setGeometry(100, 100, 800, 600)

        # Central widget & main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Top label
        self.state_label = QLabel(f"Placeholder for {self.state.value} screen.")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.state_label, 0, Qt.AlignCenter)

        # Middle layout for two buttons
        self.button_layout = QVBoxLayout()
        self.button_layout.setSpacing(10)
        self.button_layout.setAlignment(Qt.AlignCenter)

        # Blue button 1
        self.blue_button_1 = QPushButton("Connect via USB")
        self.blue_button_1.setObjectName("blueButton")  # For QSS matching
        self.blue_button_1.clicked.connect(lambda: print("USB button clicked"))
        self.button_layout.addWidget(self.blue_button_1)

        # Blue button 2
        self.blue_button_2 = QPushButton("Connect via Bluetooth")
        self.blue_button_2.setObjectName("blueButton")  # For QSS matching
        self.blue_button_2.clicked.connect(lambda: print("Bluetooth button clicked"))
        self.button_layout.addWidget(self.blue_button_2)

        self.main_layout.addLayout(self.button_layout)

        # Bottom layout for red "Next"
        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignRight)

        self.red_next_button = QPushButton("Next")
        self.red_next_button.setObjectName("redButton")  # For QSS matching
        self.red_next_button.clicked.connect(self.go_to_next_state)
        bottom_layout.addWidget(self.red_next_button)

        self.main_layout.addLayout(bottom_layout)

    def go_to_next_state(self):
        """
        Move to the next state in the list, cycle back to IDLE when we reach the end.
        """
        self.state_index = (self.state_index + 1) % len(self.states)
        self.state = self.states[self.state_index]
        self.update_ui_for_state()

    def update_ui_for_state(self):
        """
        Update the window title and label text to reflect the current state.
        """
        self.setWindowTitle(windowTitlePrefix + self.state.value)
        self.state_label.setText(f"Placeholder for {self.state.value} screen.")
