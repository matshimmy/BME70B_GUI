# models/model.py

from PyQt5.QtCore import QObject, pyqtSignal

class Model(QObject):
    """
    The Model holds data about the device status (e.g. connection, power, transmission),
    as well as options/settings for acquisition, simulation, and stimulation.
    
    It emits a `model_changed` signal whenever data changes,
    allowing any connected views or controllers to update accordingly.
    """
    model_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.reset_model()

    # --------------------------------------------------------------------------
    # PUBLIC METHODS - Connection & Disconnection
    # --------------------------------------------------------------------------
    def connect(self, conn_type: str):
        """
        Sets the connection type (USB/Bluetooth).
        Clears some flags for transmission/power.
        Then emits model_changed.
        """
        self.connection_type = conn_type
        self.transmission_ok = False
        self.model_changed.emit()

    def disconnect(self):
        """
        Resets the model to default (fully disconnected, no data).
        Then emits model_changed.
        """
        self.reset_model()
        self.model_changed.emit()

    # --------------------------------------------------------------------------
    # PUBLIC METHODS - System Check Steps
    # --------------------------------------------------------------------------
    def check_connection(self):
        """
        Dummy logic to confirm connection is active.
        In a real scenario, you'd query hardware or test pings.
        """
        self.is_connected = True
        self.model_changed.emit()

    def check_power(self):
        """
        Dummy logic to confirm power is okay. 
        For now, set it to 100.
        """
        self.power_level = 100
        self.model_changed.emit()

    def test_transmission(self):
        """
        Dummy logic to confirm transmissions are working.
        """
        self.transmission_ok = True
        self.model_changed.emit()

    # --------------------------------------------------------------------------
    # PUBLIC METHODS - Graceful Disconnect Steps
    # --------------------------------------------------------------------------
    def set_disconnect_conn_done(self):
        """
        Worker calls this once the 'Ending Connection' step is done.
        """
        self.disconnect_conn_done = True
        self.model_changed.emit()

    def set_disconnect_power_done(self):
        """
        Worker calls this once the 'Shutting Off Power' step is done.
        """
        self.disconnect_power_done = True
        self.model_changed.emit()

    def set_disconnect_trans_done(self):
        """
        Worker calls this once the 'Ending Transmission' step is done.
        """
        self.disconnect_trans_done = True
        self.model_changed.emit()

    def reset_model(self):
        """
        Sets all fields to their default values for a disconnected, uninitialized state.
        """
        # Connection
        self.connection_type = None        # "USB" or "Bluetooth"
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
