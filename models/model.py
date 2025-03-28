from PyQt5.QtCore import QObject, pyqtSignal
from models.signal_data import SignalData
from models.template_processor import TemplateProcessor
from models.template_model import TemplateModel
from enums.connection_type import ConnectionType
from enums.connection_status import ConnectionStatus
from models.signal_simulation_model import SignalSimulationModel
from enums.simulation_type import SimulationType

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
        self.connection_status = ConnectionStatus.NOT_CONNECTED
        self.transmission_ok = None
        self.model_changed.emit()

    def disconnect(self):
        self.reset_model()
        self.model_changed.emit()

    # --------------------------------------------------------------------------
    # PUBLIC METHODS - System Check Steps
    # --------------------------------------------------------------------------
    def check_connection(self, success: bool):
        if success:
            self.connection_status = ConnectionStatus.CONNECTED
        else:
            self.connection_status = ConnectionStatus.CONNECTION_FAILED
        self.model_changed.emit()

    def check_power(self):
        self.model_changed.emit()

    def test_transmission(self, transmission_ok: bool):
        self.transmission_ok = transmission_ok
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
        if self.get_template:
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

    def set_simulation_type(self, simulation_type: SimulationType):
        self.simulation_type = simulation_type
        self.model_changed.emit()

    def reset_model(self):
        self.signal_data = SignalData()
        self.template_processor = TemplateProcessor()

        # Connection
        self.connection_type = None
        self.connection_status = ConnectionStatus.NOT_CONNECTED
        self.power_level = -1
        self.transmission_ok = None

        # Graceful Disconnect Steps
        self.disconnect_conn_done = False
        self.disconnect_power_done = False
        self.disconnect_trans_done = False

        # Acquisition
        self.get_template = None
        self.sampling_rate = None
        self.acquisition_running = False

        # Simulation
        self.template_model = TemplateModel()
        # Initialize signal_simulation if it doesn't exist, otherwise reset it
        if not hasattr(self, 'signal_simulation'):
            self.signal_simulation = SignalSimulationModel(model=self)
        else:
            self.signal_simulation.reset()

        self.simulation_type = SimulationType.TEMPLATE

        self.simulation_running = False

        # Stimulation
        self.stimulation_frequency = None
        self.stimulation_pulse_width = None
        self.stimulation_current = None
