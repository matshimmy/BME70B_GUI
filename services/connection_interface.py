from abc import ABC, abstractmethod
from enums.connection_type import ConnectionType

class ConnectionInterface(ABC):
    """Abstract base class for device connections (USB/Serial or Bluetooth)"""
    
    @abstractmethod
    def connect(self):
        """Establish connection to the device"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from the device"""
        pass
    
    @abstractmethod
    def is_connected(self):
        """Check if the connection is active"""
        pass
    
    @abstractmethod
    def send_command(self, command):
        """Send a command to the device and return the response"""
        pass
    
    @abstractmethod
    def check_power(self):
        """Check the power level of the device"""
        pass
    
    @abstractmethod
    def test_transmission(self):
        """Test data transmission with the device"""
        pass

class ConnectionFactory:
    """Factory for creating appropriate connection interface based on connection type"""
    
    @staticmethod
    def create_connection(connection_type: ConnectionType):
        """Create and return a connection interface based on the connection type"""
        if connection_type == ConnectionType.USB:
            from services.usb_connection import USBConnection
            return USBConnection()
        elif connection_type == ConnectionType.BLUETOOTH:
            from services.bluetooth_connection import BluetoothConnection
            return BluetoothConnection()
        else:
            raise ValueError(f"Unsupported connection type: {connection_type}") 