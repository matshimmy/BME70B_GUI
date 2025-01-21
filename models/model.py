from PyQt5.QtCore import QObject, pyqtSignal

class Model(QObject):
    """
    Holds data about device connections, power, transmission, etc.
    Emits signals when data changes to notify interested views or controllers.
    """

    # A generic signal that says "the model changed"
    model_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.reset_model()

    def connect(self, conn_type: str):
        """Connect to the device via USB or Bluetooth."""
        self.connection_type = conn_type
        
        # set defaults
        self.transmission_ok = False
        self.model_changed.emit()

    def disconnect(self):
        self.reset_model()
        self.model_changed.emit()

    def check_connection(self):
        """
        Placeholder logic for checking connection.
        read actual data from the hardware.
        """
        self.is_connected = True
        self.model_changed.emit()

    def check_power(self):
        """
        Placeholder logic for checking power.
        read actual data from the hardware.
        """
        # keep it at 100 for now
        self.power_level = 100
        self.model_changed.emit()

    def test_transmission(self):
        """
        Test transmissions.
        """
        self.transmission_ok = True
        self.model_changed.emit()

    def reset_model(self):
        self.connection_type = None       # "USB" or "Bluetooth"
        self.is_connected = False
        self.power_level = -1           # starting power
        self.transmission_ok = False

        # Acquisition options
        self.acquisition_type = None
        self.sampling_rate = None

        # Simulation options
        self.simulation_type = None
        self.transmission_rate = None

