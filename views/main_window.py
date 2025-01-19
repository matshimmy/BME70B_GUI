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

        # Central widget + stacked widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_widget = QStackedWidget()

        # Create screen widgets
        self.idle_screen = IdleWidget()
        self.system_check_screen = SystemCheckWidget()

        # Provide the same model to the system check widget
        self.system_check_screen.setModel(self.state_machine.model)

        # Add to the stacked widget
        self.stacked_widget.addWidget(self.idle_screen)         # index 0
        self.stacked_widget.addWidget(self.system_check_screen) # index 1

        # Connect signals from IdleWidget
        self.idle_screen.usb_button.clicked.connect(lambda: self.handle_connect_mcu('USB'))
        self.idle_screen.bt_button.clicked.connect(lambda: self.handle_connect_mcu('Bluetooth'))

        # Layout
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.stacked_widget)

    def handle_connect_mcu(self, connection_type):
        """
        Called when user clicks "Connect via USB" or "Connect via Bluetooth."
        """
        self.state_machine.connect_device(connection_type)

        # Retrieve the new state
        new_state = self.state_machine.current_state
        self.setWindowTitle(windowTitlePrefix + new_state.value)

        # If we’re now in SYSTEM_CHECK, show that screen
        if new_state == AppState.SYSTEM_CHECK:
            self.stacked_widget.setCurrentIndex(1)
            # Optionally run system checks immediately
            self.state_machine.do_system_check()
