from PyQt5.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout
from enums.app_state import AppState
from controllers.state_machine import StateMachine
from controllers.device_controller import DeviceController

from views.idle_widget import IdleWidget
from views.system_check_widget import SystemCheckWidget
from views.mode_selection_widget import ModeSelectionWidget
from views.acquisition_options_widget import AcquisitionOptionsWidget

windowTitlePrefix = "BME70B App | "

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the state machine
        self.state_machine = StateMachine()
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
        self.idle_screen = IdleWidget(device_controller=self.device_controller)
        self.system_check_screen = SystemCheckWidget(model=self.state_machine.model, device_controller=self.device_controller)
        self.mode_selection_screen = ModeSelectionWidget(state_machine=self.state_machine, device_controller=self.device_controller)
        self.acquisition_options_screen = AcquisitionOptionsWidget(state_machine=self.state_machine, device_controller=self.device_controller)

        # Add them to the stacked widget
        self.stacked_widget.addWidget(self.idle_screen)         # index 0 (IDLE)
        self.stacked_widget.addWidget(self.system_check_screen) # index 1 (SYSTEM_CHECK)
        self.stacked_widget.addWidget(self.mode_selection_screen) # index 2 (MODE_SELECTION)
        self.stacked_widget.addWidget(self.acquisition_options_screen) # index 3 (ACQUISITION_OPTIONS)

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
        elif new_state == AppState.ACQUISITION_OPTIONS:
            self.stacked_widget.setCurrentIndex(3)
