# models/device_model.py

from PyQt5.QtCore import QObject, pyqtSignal

class DeviceModel(QObject):
    """
    Holds data about device connections, power, transmission, etc.
    Emits signals when data changes to notify interested views or controllers.
    """

    # A generic signal that says "the model changed"
    model_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.connection_type = None       # "USB" or "Bluetooth"
        self.is_connected = False
        self.power_level = 100           # starting power
        self.transmission_ok = False

    def connect(self, conn_type: str):
        """Connect to the device via USB or Bluetooth."""
        self.connection_type = conn_type
        self.is_connected = True
        
        # Optionally reset or set defaults
        self.transmission_ok = False
        # Emit signal to inform listeners that something changed
        self.model_changed.emit()

    def disconnect(self):
        self.connection_type = None
        self.is_connected = False
        self.transmission_ok = False
        self.model_changed.emit()

    def check_power(self):
        """
        Placeholder logic for checking power.
        read actual data from the hardware.
        """
        if self.is_connected:
            # keep it at 100 for now
            pass
        self.model_changed.emit()

    def test_transmission(self):
        """
        Test transmissions.
        """
        if self.is_connected:
            self.transmission_ok = True
        else:
            self.transmission_ok = False
        self.model_changed.emit()
