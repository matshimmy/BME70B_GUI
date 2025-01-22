from PyQt5.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout
from enums.app_state import AppState
from controllers.state_machine import StateMachine
from controllers.device_controller import DeviceController

from views.idle_widget import IdleWidget
from views.system_check_widget import SystemCheckWidget
from views.mode_selection_widget import ModeSelectionWidget
from views.acquisition_options_widget import AcquisitionOptionsWidget
from views.running_acquisition_widget import RunningAcquisitionWidget
from views.simulation_options_widget import SimulationOptionsWidget
from views.running_simulation_widget import RunningSimulationWidget
from views.stimulation_options_widget import StimulationOptionsWidget
from views.running_stimulation_widget import RunningStimulationWidget

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
        self.running_acquisition_screen = RunningAcquisitionWidget(state_machine=self.state_machine, device_controller=self.device_controller)
        self.simulation_options_screen = SimulationOptionsWidget(state_machine=self.state_machine, device_controller=self.device_controller)
        self.running_simulation_screen = RunningSimulationWidget(state_machine=self.state_machine, device_controller=self.device_controller)
        self.stimulation_options_screen = StimulationOptionsWidget(state_machine=self.state_machine, device_controller=self.device_controller)
        self.running_stimulation_screen = RunningStimulationWidget(state_machine=self.state_machine, device_controller=self.device_controller)

        # Add them to the stacked widget
        self.stacked_widget.addWidget(self.idle_screen)         # index 0 (IDLE)
        self.stacked_widget.addWidget(self.system_check_screen) # index 1 (SYSTEM_CHECK)
        self.stacked_widget.addWidget(self.mode_selection_screen) # index 2 (MODE_SELECTION)
        self.stacked_widget.addWidget(self.acquisition_options_screen) # index 3 (ACQUISITION_OPTIONS)
        self.stacked_widget.addWidget(self.running_acquisition_screen) # index 4 (RUNNING_ACQUISITION)
        self.stacked_widget.addWidget(self.simulation_options_screen) # index 5 (SIMULATION_OPTIONS)
        self.stacked_widget.addWidget(self.running_simulation_screen) # index 6 (RUNNING_SIMULATION)
        self.stacked_widget.addWidget(self.stimulation_options_screen) # index 7 (STIMULATION_OPTIONS)
        self.stacked_widget.addWidget(self.running_stimulation_screen) # index 8 (RUNNING_STIMULATION)

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
        elif new_state == AppState.RUNNING_ACQUISITION:
            self.stacked_widget.setCurrentIndex(4)
        elif new_state == AppState.SIMULATION_OPTIONS:
            self.stacked_widget.setCurrentIndex(5)
        elif new_state == AppState.RUNNING_SIMULATION:
            self.stacked_widget.setCurrentIndex(6)
        elif new_state == AppState.STIMULATION_OPTIONS:
            self.stacked_widget.setCurrentIndex(7)
        elif new_state == AppState.RUNNING_STIMULATION:
            self.stacked_widget.setCurrentIndex(8)
