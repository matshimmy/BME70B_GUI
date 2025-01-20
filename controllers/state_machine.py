from PyQt5.QtCore import QObject, pyqtSignal
from controllers.states import AppState
from models.device_model import DeviceModel

class StateMachine(QObject):
    state_changed = pyqtSignal(AppState)

    def __init__(self):
        super().__init__()
        self.current_state = AppState.IDLE
        self.model = DeviceModel()  # The model is part of the state machine

    def transition_to(self, new_state):
        """Generic method to transition to a new state."""
        self.current_state = new_state
        self.state_changed.emit(new_state)

    def connect_device(self, connection_type: str):
        """
        Called to handle device connection logic from IDLE to SYSTEM_CHECK.
        """
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
