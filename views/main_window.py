# main_window.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout
from controllers.states import AppState
from controllers.state_machine import StateMachine

from views.idle_widget import IdleWidget
from views.system_check_widget import SystemCheckWidget

windowTitlePrefix = "BME70B App | "

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the state machine
        self.state_machine = StateMachine()

        self.setWindowTitle(windowTitlePrefix + self.state_machine.current_state.value)
        self.setGeometry(100, 100, 800, 600)

        # Set up the central widget and the stacked widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_widget = QStackedWidget()

        # Instantiate screen widgets
        self.idle_screen = IdleWidget()
        self.system_check_screen = SystemCheckWidget()

        # Add widgets to the stacked widget in the order of your states
        self.stacked_widget.addWidget(self.idle_screen)         # index 0 (IDLE)
        self.stacked_widget.addWidget(self.system_check_screen) # index 1 (SYSTEM_CHECK)

        # Connect signals from the IdleWidget to state transitions
        self.idle_screen.usb_button.clicked.connect(lambda: self.handle_connect_mcu('USB'))
        self.idle_screen.bt_button.clicked.connect(lambda: self.handle_connect_mcu('Bluetooth'))

        # Layout for the central widget
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.stacked_widget)

    def handle_connect_mcu(self, connection_type):
        """
        Transition from IDLE to SYSTEM_CHECK using the state machine logic.
        """
        # Ask the state machine to handle the transition logic
        self.state_machine.connect_mcu(connection_type)

        # Update your UI based on the new state
        new_state = self.state_machine.current_state

        self.setWindowTitle(windowTitlePrefix + new_state.value)

        if new_state == AppState.SYSTEM_CHECK:
            self.stacked_widget.setCurrentIndex(1)  # system check widget
        # elif new_state == SomeOtherState:
        #     self.stacked_widget.setCurrentIndex(X)
