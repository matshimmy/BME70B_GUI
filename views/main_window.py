from PyQt5.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout
from controllers.states import AppState
from controllers.state_machine import StateMachine
from controllers.device_controller import DeviceController
from models.model import Model

from views.idle_widget import IdleWidget
from views.system_check_widget import SystemCheckWidget
from views.mode_selection_widget import ModeSelectionWidget

windowTitlePrefix = "BME70B App | "

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.model = Model()
        # Create the state machine
        self.state_machine = StateMachine(self.model)
        # Listen for state changes
        self.state_machine.state_changed.connect(self.on_state_changed)

        # Create the device controller
        self.device_controller = DeviceController(self.state_machine)

        self.setWindowTitle(windowTitlePrefix + self.state_machine.current_state.value)
        self.setGeometry(100, 100, 800, 600)

        # Central widget + stacked widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_widget = QStackedWidget()

        # Create screen widgets
        self.idle_screen = IdleWidget()
        self.system_check_screen = SystemCheckWidget(
            model=self.model,
            device_controller=self.device_controller
        )
        self.mode_selection_screen = ModeSelectionWidget()

        # Add them to the stacked widget
        self.stacked_widget.addWidget(self.idle_screen)         # index 0 (IDLE)
        self.stacked_widget.addWidget(self.system_check_screen) # index 1 (SYSTEM_CHECK)
        self.stacked_widget.addWidget(self.mode_selection_screen) # index 2 (MODE_SELECTION)

        # Connect signals from IdleWidget
        self.idle_screen.usb_button.clicked.connect(lambda: self.handle_connect_mcu('USB'))
        self.idle_screen.bt_button.clicked.connect(lambda: self.handle_connect_mcu('Bluetooth'))

        # Connect signals for ModeSelectionWidget
        self.mode_selection_screen.disconnect_button.clicked.connect(self.handle_disconnect)

        # Layout
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.stacked_widget)

    def on_state_changed(self, new_state):
        """
        Called when the state machine changes state.
        """
        self.setWindowTitle(windowTitlePrefix + new_state.value)
        if new_state == AppState.IDLE:
            self.stacked_widget.setCurrentIndex(0)
        elif new_state == AppState.SYSTEM_CHECK:
            self.stacked_widget.setCurrentIndex(1)
        elif new_state == AppState.MODE_SELECTION:
            self.stacked_widget.setCurrentIndex(2)

    def handle_connect_mcu(self, connection_type):
        """
        Called when user clicks "Connect via USB" or "Connect via Bluetooth."
        """
        self.state_machine.connect_device(connection_type)
        # Start the system check in the device controller
        self.device_controller.start_system_check()

    def handle_disconnect(self):
        self.state_machine.disconnect_device()
