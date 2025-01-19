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

    def do_system_check(self):
        """
        In SYSTEM_CHECK:
        - Check power
        - Test transmission
        - Then transition to next state if everything is OK
        """
        if self.current_state == AppState.SYSTEM_CHECK:
            self.model.check_power()
            self.model.test_transmission()
            # transition to MODE_SELECTION if all goes well
            # self.transition_to(AppState.MODE_SELECTION)
        else:
            # Handle error
            pass
