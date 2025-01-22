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

    def start_acquisition(self):
        """
        Called to start the acquisition.
        """
        self.transition_to(AppState.RUNNING_ACQUISITION)

    def transition_to_simulation_options(self):
        """
        Called to transition to the simulation options screen.
        """
        self.transition_to(AppState.SIMULATION_OPTIONS)

    def update_simulation_options(
        self, simulation_type, transmission_rate, 
        muscle_artifact=False, random_artifact=False, 
        sixty_hz_artifact=False, custom_csv=None
    ):
        # Store in the model
        self.model.simulation_type = simulation_type
        self.model.transmission_rate = transmission_rate
        self.model.muscle_artifact = muscle_artifact
        self.model.random_artifact = random_artifact
        self.model.sixty_hz_artifact = sixty_hz_artifact
        self.model.custom_csv_path = custom_csv
        self.model.model_changed.emit()

    def start_simulation(self):
        """
        Called to start the simulation.
        """
        self.transition_to(AppState.RUNNING_SIMULATION)

    def transition_to_stimulation_options(self):
        """
        Called to transition to the stimulation options screen.
        """
        self.transition_to(AppState.STIMULATION_OPTIONS)

    def update_stimulation_options(self, frequency: int, pulse_width: int, current: int):
        """
        Called to update the stimulation options in the model.
        """
        self.model.stimulation_frequency = frequency
        self.model.stimulation_pulse_width = pulse_width
        self.model.stimulation_current = current
        self.model.model_changed.emit()

    def start_stimulation(self):
        """
        Called to start the stimulation.
        """
        self.transition_to(AppState.RUNNING_STIMULATION)
