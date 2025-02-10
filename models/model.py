from PyQt5.QtCore import QObject, pyqtSignal
from models.signal_data import SignalData
from models.template_processor import TemplateProcessor
from enums.connection_type import ConnectionType

class Model(QObject):
    model_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.reset_model()

    # --------------------------------------------------------------------------
    # PUBLIC METHODS - Connection & Disconnection
    # --------------------------------------------------------------------------
    def connect(self, conn_type: ConnectionType):
        self.connection_type = conn_type
        self.transmission_ok = False
        self.model_changed.emit()

    def disconnect(self):
        self.reset_model()
        self.model_changed.emit()

    # --------------------------------------------------------------------------
    # PUBLIC METHODS - System Check Steps
    # --------------------------------------------------------------------------
    def check_connection(self):
        self.is_connected = True
        self.model_changed.emit()

    def check_power(self):
        self.power_level = 100
        self.model_changed.emit()

    def test_transmission(self):
        self.transmission_ok = True
        self.model_changed.emit()

    # --------------------------------------------------------------------------
    # PUBLIC METHODS - Graceful Disconnect Steps
    # --------------------------------------------------------------------------
    def set_disconnect_conn_done(self):
        self.disconnect_conn_done = True
        self.model_changed.emit()

    def set_disconnect_power_done(self):
        self.disconnect_power_done = True
        self.model_changed.emit()

    def set_disconnect_trans_done(self):
        self.disconnect_trans_done = True
        self.model_changed.emit()

    # --------------------------------------------------------------------------
    # PUBLIC METHODS - Acquisition
    # --------------------------------------------------------------------------
    def start_acquisition(self):
        self.signal_data = SignalData(sample_rate=self.sampling_rate)
        # Create TemplateProcessor
        self.template_processor = TemplateProcessor(
            sample_rate=self.sampling_rate,
            look_back_time_s=4.0,
            update_interval_s=4.0
        )
        # Connect the signal from SignalData to the processor's slot
        self.signal_data.new_chunk_appended.connect(
            self.template_processor.append_data
        )
        self.acquisition_running = True
        self.model_changed.emit()

    def reset_model(self):
        self.signal_data = SignalData()
        self.template_processor = TemplateProcessor()

        # Connection
        self.connection_type = None
        self.is_connected = False
        self.power_level = -1
        self.transmission_ok = False

        # Graceful Disconnect Steps
        self.disconnect_conn_done = False
        self.disconnect_power_done = False
        self.disconnect_trans_done = False

        # Acquisition
        self.acquisition_type = None
        self.sampling_rate = None
        self.acquisition_running = False

        # Simulation
        self.simulation_type = None
        self.transmission_rate = None
        self.muscle_artifact = False
        self.random_artifact = False
        self.sixty_hz_artifact = False
        self.custom_csv_path = None

        # Stimulation
        self.stimulation_frequency = None
        self.stimulation_pulse_width = None
        self.stimulation_current = None
