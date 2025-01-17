from controllers.states import AppState

class StateMachine:
    def __init__(self):
        # Set the initial state
        self.current_state = AppState.IDLE

    def transition_to(self, new_state):
        """
        Generic transition method.
        You could add checks or logs here to validate or record state changes.
        """
        self.current_state = new_state

    def connect_mcu(self, connection_type):
        """
        An example method to move from IDLE -> SYSTEM_CHECK
        based on a connection type ('USB' or 'Bluetooth', etc.)
        """
        if self.current_state == AppState.IDLE:
            # Potentially do some logic:
            # e.g., check that 'USB' or 'Bluetooth' is valid
            # or set some internal flag
            self.current_state = AppState.SYSTEM_CHECK
        
        # If you have more advanced logic, you could handle it here:
        # elif self.current_state == SomeOtherState:
        #     ...
