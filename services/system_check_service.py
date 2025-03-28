from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer, QEventLoop
from enums.connection_type import ConnectionType
from services.connection_interface import ConnectionFactory
from models.model import Model
from services.usb_connection import USBConnection

class SystemCheckService(QObject):
    """
    Worker dedicated to running the system check in a separate thread.
    """
    connection_checked = pyqtSignal(bool)
    power_checked = pyqtSignal(int)  # Now includes power level
    transmission_checked = pyqtSignal(bool)  # Now includes success status
    finished = pyqtSignal()
    error = pyqtSignal(str)  # New signal for error reporting
    
    # Add delay between check steps (in milliseconds)
    STEP_DELAY = 1500  # 1.5 seconds

    def __init__(self, model: Model = None):
        super().__init__()
        self.model = model
        self.connection = None
        self.connection_type = None

    def set_connection_type(self, connection_type: ConnectionType):
        """Set the connection type to use for the system check"""
        self.connection_type = connection_type
        
    def delay(self, milliseconds):
        """Non-blocking delay using QTimer and QEventLoop"""
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)
        loop.exec_()

    def run_system_check(self):
        """
        Perform actual hardware system check using the specified connection type.
        """
        if not self.connection_type:
            self.error.emit("Connection type not specified")
            return

        # Create the appropriate connection interface
        try:
            if self.connection_type == ConnectionType.USB:
                # For USB, first scan for available Arduino ports
                arduino_ports = USBConnection.scan_for_arduino()
                
                if not arduino_ports:
                    self.error.emit("No Arduino devices found on any COM port")
                    self.connection_checked.emit(False)
                    return
                
                # Try to connect to the first found Arduino port
                self.connection = USBConnection(port=arduino_ports[0])
            else:
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
            self.connection_checked.emit(True)
            
            # Add delay to allow the UI to update and show success
            self.delay(self.STEP_DELAY)
        else:
            self.error.emit(f"Failed to connect via {self.connection_type.name}")
            self.connection_checked.emit(False)
            return

        # 2) Transmission check
        if QThread.currentThread().isInterruptionRequested():
            return
            
        print("Testing transmission...")
        transmission_ok = self.connection.test_transmission()
        self.transmission_checked.emit(transmission_ok)
        if not transmission_ok:
            self.error.emit("Failed to test transmission")
            return
        
        # Add delay to allow the UI to update and show success
        self.delay(self.STEP_DELAY)

        # 3) Power check
        if QThread.currentThread().isInterruptionRequested():
            return
            
        print("Checking power...")
        power_level = self.connection.check_power()
        if power_level > 0:
            print(f"Power level: {power_level}%")
            if self.model:
                self.model.power_level = power_level
            self.power_checked.emit(power_level)
            
            # Add delay to allow the UI to update and show success
            self.delay(self.STEP_DELAY)
        else:
            self.error.emit("Failed to check power level")
            return
        
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
