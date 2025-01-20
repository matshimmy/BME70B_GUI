from controllers.states import AppState
from models.device_model import DeviceModel

class StateMachine:
    def __init__(self):
        self.current_state = AppState.IDLE
        self.model = DeviceModel()  # The model is part of the state machine

    def transition_to(self, new_state):
        """Generic method to transition to a new state."""
        # add validation or checks before assigning
        self.current_state = new_state

    def connect_device(self, connection_type: str):
        """
        Called to handle device connection logic from IDLE to SYSTEM_CHECK.
        """
        if self.current_state == AppState.IDLE:
            # 1) Update the model to connect
            self.model.connect(connection_type)
            # 2) Move to system check state
            self.transition_to(AppState.SYSTEM_CHECK)
        else:
            # log an error or handle invalid transitions
            pass

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
