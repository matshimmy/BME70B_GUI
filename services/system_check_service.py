from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time
from enums.connection_type import ConnectionType
from services.connection_interface import ConnectionFactory
from models.model import Model

class SystemCheckService(QObject):
    """
    Worker dedicated to running the system check in a separate thread.
    """
    connection_checked = pyqtSignal()
    power_checked = pyqtSignal(int)  # Now includes power level
    transmission_checked = pyqtSignal(bool)  # Now includes success status
    finished = pyqtSignal()
    error = pyqtSignal(str)  # New signal for error reporting

    def __init__(self, model: Model = None):
        super().__init__()
        self.model = model
        self.connection = None
        self.connection_type = None

    def set_connection_type(self, connection_type: ConnectionType):
        """Set the connection type to use for the system check"""
        self.connection_type = connection_type

    def run_system_check(self):
        """
        Perform actual hardware system check using the specified connection type.
        """
        if not self.connection_type:
            self.error.emit("Connection type not specified")
            return

        # Create the appropriate connection interface
        try:
            self.connection = ConnectionFactory.create_connection(self.connection_type)
        except Exception as e:
            self.error.emit(f"Failed to create connection: {str(e)}")
            return

        # 1) Connection check
        if QThread.currentThread().isInterruptionRequested():
            return
            
        print(f"Connecting via {self.connection_type.name}...")
        if self.connection.connect():
            print("Connection successful")
            self.connection_checked.emit()
        else:
            self.error.emit(f"Failed to connect via {self.connection_type.name}")
            return

        # 2) Power check
        if QThread.currentThread().isInterruptionRequested():
            return
            
        print("Checking power...")
        power_level = self.connection.check_power()
        if power_level > 0:
            print(f"Power level: {power_level}%")
            if self.model:
                self.model.power_level = power_level
            self.power_checked.emit(power_level)
        else:
            self.error.emit("Failed to check power level")
            return

        # 3) Transmission check
        if QThread.currentThread().isInterruptionRequested():
            return
            
        print("Testing transmission...")
        transmission_ok = self.connection.test_transmission()
        # print(transmission_ok)
        if self.model:
            self.model.transmission_ok = transmission_ok
        self.transmission_checked.emit(transmission_ok)
        
        # Complete
        if not QThread.currentThread().isInterruptionRequested():
            print("System check complete")
            self.finished.emit()
        else:
            # Clean up the connection if interrupted
            self.connection.disconnect()
            
    def abort(self):
        """Abort the system check and clean up"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
