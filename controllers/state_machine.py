from PyQt5.QtCore import QObject, pyqtSignal
from enums.app_state import AppState
from enums.acquisition_type import AcquisitionType
from models.model import Model

class StateMachine(QObject):
    state_changed = pyqtSignal(AppState)

    def __init__(self):
        super().__init__()
        self.current_state = AppState.IDLE
        self.model = Model()  # The model is part of the state machine

    def transition_to(self, new_state : AppState):
        """Generic method to transition to a new state."""
        self.current_state = new_state
        self.state_changed.emit(new_state)

    def connect_device(self, connection_type: str):
        """
        Called to handle device connection logic from IDLE to SYSTEM_CHECK.
        """
        self.model.disconnect() # Reset the model
        self.model.connect(connection_type)
        self.transition_to(AppState.SYSTEM_CHECK)

    def disconnect_device(self):
        """
        Called to handle device disconnection logic from SYSTEM_CHECK to IDLE.
        """
        self.model.disconnect()
        self.transition_to(AppState.IDLE)

    def do_system_check_connection(self):
        """
        Called when connection check is done.
        """
        self.model.check_connection()

    def do_system_check_power(self):
        """
        Called when power check is done.
        """
        self.model.check_power()

    def do_system_test_transmission(self):
        """
        Called when transmission check is done.
        """
        self.model.test_transmission()

    def do_system_check_done(self):
        """
        Called when all system checks are done.
        """
        self.transition_to(AppState.MODE_SELECTION)

    def transition_to_acquisition_options(self):
        """
        Called to transition to the acquisition options screen.
        """
        self.transition_to(AppState.ACQUISITION_OPTIONS)
    
    def update_acquisition_options(self, acquisition_type: AcquisitionType, sampling_rate: int):
        """
        Called to update the acquisition options in the model.
        """
        self.model.acquisition_type = acquisition_type
        self.model.sampling_rate = sampling_rate
        self.model.model_changed.emit()
