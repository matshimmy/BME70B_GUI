from PyQt5.QtCore import QObject, pyqtSignal
from enums.app_state import AppState
from enums.acquisition_type import AcquisitionType
from enums.connection_type import ConnectionType
from models.model import Model

class StateMachine(QObject):
    state_changed = pyqtSignal(AppState)
    acquisition_chunk_received = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_state = AppState.IDLE
        self.model = Model()

    # --------------------------------------------------------------------------
    # INTERNAL: Generic State Transition
    # --------------------------------------------------------------------------
    def transition_to(self, new_state: AppState):
        self.current_state = new_state
        self.state_changed.emit(new_state)

    # --------------------------------------------------------------------------
    # BASIC CONNECT / DISCONNECT
    # --------------------------------------------------------------------------
    def connect_device(self, connection_type: ConnectionType):
        self.model.disconnect()  # reset model fully
        self.model.connect(connection_type)
        self.transition_to(AppState.SYSTEM_CHECK)

    def disconnect_device(self):
        self.model.disconnect()
        self.transition_to(AppState.IDLE)

    # --------------------------------------------------------------------------
    # SYSTEM CHECK
    # --------------------------------------------------------------------------
    def do_system_check_connection(self):
        self.model.check_connection()

    def do_system_check_power(self):
        self.model.check_power()

    def do_system_test_transmission(self):
        self.model.test_transmission()

    def do_system_check_done(self):
        self.transition_to(AppState.MODE_SELECTION)

    # --------------------------------------------------------------------------
    # ACQUISITION
    # --------------------------------------------------------------------------
    def transition_to_acquisition_options(self):
        self.transition_to(AppState.ACQUISITION_OPTIONS)
    
    def update_acquisition_options(self, acquisition_type: AcquisitionType, sampling_rate: float):
        self.model.acquisition_type = acquisition_type
        self.model.sampling_rate = sampling_rate
        self.model.model_changed.emit()

    def start_acquisition(self):
        self.transition_to(AppState.RUNNING_ACQUISITION)
        self.model.start_acquisition()

    def toggle_acquisition(self):
        self.model.acquisition_running = not self.model.acquisition_running
        self.model.model_changed.emit()

    def stop_acquisition(self):
        self.model.acquisition_running = False
        self.model.model_changed.emit()

    def append_acquisition_data(self, chunk):
        if not self.model.acquisition_running:
            return
        self.model.signal_data.append_chunck(chunk)
        self.model.model_changed.emit()
        self.acquisition_chunk_received.emit()

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
        self.transition_to(AppState.GRACEFUL_DISCONNECT)

    def do_graceful_disconnect_conn(self):
        self.model.set_disconnect_conn_done()

    def do_graceful_disconnect_power(self):
        self.model.set_disconnect_power_done()

    def do_graceful_disconnect_trans(self):
        self.model.set_disconnect_trans_done()

    def do_graceful_disconnect_done(self):
        self.transition_to(AppState.IDLE)

    # --------------------------------------------------------------------------
    # GENERIC
    # --------------------------------------------------------------------------
    def on_back_options_clicked(self):
        self.transition_to(AppState.MODE_SELECTION)
