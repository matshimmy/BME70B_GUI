# controllers/state_machine.py

from PyQt5.QtCore import QObject, pyqtSignal
from enums.app_state import AppState
from enums.acquisition_type import AcquisitionType
from models.model import Model

class StateMachine(QObject):
    """
    The StateMachine (or 'StateController') manages all high-level application states
    (IDLE, SYSTEM_CHECK, MODE_SELECTION, ACQUISITION_OPTIONS, etc.), and interacts
    with the Model to store or reset data accordingly.
    """
    state_changed = pyqtSignal(AppState)

    def __init__(self):
        super().__init__()
        self.current_state = AppState.IDLE
        self.model = Model()

    # --------------------------------------------------------------------------
    # INTERNAL: Generic State Transition
    # --------------------------------------------------------------------------
    def transition_to(self, new_state: AppState):
        """
        Moves the application from the current state to 'new_state'
        and emits state_changed, so the UI can switch screens.
        """
        self.current_state = new_state
        self.state_changed.emit(new_state)

    # --------------------------------------------------------------------------
    # BASIC CONNECT / DISCONNECT
    # --------------------------------------------------------------------------
    def connect_device(self, connection_type: str):
        """
        From IDLE to SYSTEM_CHECK, resetting the model, then connecting.
        """
        self.model.disconnect()  # reset model fully
        self.model.connect(connection_type)
        self.transition_to(AppState.SYSTEM_CHECK)

    def disconnect_device(self):
        """
        A direct / immediate disconnect: reset the model, go to IDLE.
        """
        self.model.disconnect()
        self.transition_to(AppState.IDLE)

    # --------------------------------------------------------------------------
    # SYSTEM CHECK
    # --------------------------------------------------------------------------
    def do_system_check_connection(self):
        """
        Worker step: system check for connection. Updates model if success.
        """
        self.model.check_connection()

    def do_system_check_power(self):
        """
        Worker step: system check for power level.
        """
        self.model.check_power()

    def do_system_test_transmission(self):
        """
        Worker step: system check for transmission.
        """
        self.model.test_transmission()

    def do_system_check_done(self):
        """
        After all system check steps complete, move to MODE_SELECTION.
        """
        self.transition_to(AppState.MODE_SELECTION)

    # --------------------------------------------------------------------------
    # ACQUISITION
    # --------------------------------------------------------------------------
    def transition_to_acquisition_options(self):
        self.transition_to(AppState.ACQUISITION_OPTIONS)
    
    def update_acquisition_options(self, acquisition_type: AcquisitionType, sampling_rate: int):
        """
        Store the acquisition options in the model.
        """
        self.model.acquisition_type = acquisition_type
        self.model.sampling_rate = sampling_rate
        self.model.model_changed.emit()

    def start_acquisition(self):
        """
        Proceed to RUNNING_ACQUISITION state.
        """
        self.transition_to(AppState.RUNNING_ACQUISITION)

    # --------------------------------------------------------------------------
    # SIMULATION
    # --------------------------------------------------------------------------
    def transition_to_simulation_options(self):
        self.transition_to(AppState.SIMULATION_OPTIONS)

    def update_simulation_options(
        self, simulation_type, transmission_rate, 
        muscle_artifact=False, random_artifact=False, 
        sixty_hz_artifact=False, custom_csv=None
    ):
        """
        Store the simulation options in the model.
        """
        self.model.simulation_type = simulation_type
        self.model.transmission_rate = transmission_rate
        self.model.muscle_artifact = muscle_artifact
        self.model.random_artifact = random_artifact
        self.model.sixty_hz_artifact = sixty_hz_artifact
        self.model.custom_csv_path = custom_csv
        self.model.model_changed.emit()

    def start_simulation(self):
        self.transition_to(AppState.RUNNING_SIMULATION)

    # --------------------------------------------------------------------------
    # STIMULATION
    # --------------------------------------------------------------------------
    def transition_to_stimulation_options(self):
        self.transition_to(AppState.STIMULATION_OPTIONS)

    def update_stimulation_options(self, frequency: int, pulse_width: int, current: int):
        """
        Store the stimulation options in the model.
        """
        self.model.stimulation_frequency = frequency
        self.model.stimulation_pulse_width = pulse_width
        self.model.stimulation_current = current
        self.model.model_changed.emit()

    def start_stimulation(self):
        self.transition_to(AppState.RUNNING_STIMULATION)

    # --------------------------------------------------------------------------
    # GRACEFUL DISCONNECT
    # --------------------------------------------------------------------------
    def do_graceful_disconnect(self):
        """
        The user wants a spinner-based, multi-step disconnect process.
        """
        self.transition_to(AppState.GRACEFUL_DISCONNECT)

    def do_graceful_disconnect_conn(self):
        """
        Worker step: graceful disconnect for connection.
        """
        self.model.set_disconnect_conn_done()

    def do_graceful_disconnect_power(self):
        """
        Worker step: graceful disconnect for power.
        """
        self.model.set_disconnect_power_done()

    def do_graceful_disconnect_trans(self):
        """
        Worker step: graceful disconnect for transmission.
        """
        self.model.set_disconnect_trans_done()

    def do_graceful_disconnect_done(self):
        """
        Once the graceful disconnect worker finishes, we revert to IDLE.
        """
        self.transition_to(AppState.IDLE)

    # --------------------------------------------------------------------------
    # GENERIC
    # --------------------------------------------------------------------------
    def on_back_options_clicked(self):
        """
        If the user clicks 'Back' on any options screen, we return to MODE_SELECTION.
        """
        self.transition_to(AppState.MODE_SELECTION)
