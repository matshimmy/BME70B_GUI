from PyQt5.QtWidgets import QWidget
from controllers.state_machine import StateMachine
from controllers.device_controller import DeviceController

class BaseWidget(QWidget):
    """Base widget class for all application main window widgets."""
    
    def __init__(self, state_machine: StateMachine, device_controller: DeviceController):
        super().__init__()
        self.state_machine = state_machine
        self.device_controller = device_controller
        self.model = state_machine.model
        
        # Common setup
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _setup_ui")
        
    def reset_ui(self):
        """Reset the UI to its initial state. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement reset_ui")
