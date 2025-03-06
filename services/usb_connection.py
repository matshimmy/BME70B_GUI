import serial
import time
from services.connection_interface import ConnectionInterface

class USBConnection(ConnectionInterface):
    """USB/Serial connection implementation"""
    
    def __init__(self, port='COM4', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.arduino = None
        self._connected = False
    
    def connect(self):
        """Establish connection to the device via serial port"""
        try:
            self.arduino = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=2)
            time.sleep(2)  # Wait for Arduino to reset
            self._connected = True
            return True
        except Exception as e:
            print(f"USB Connection error: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the serial port"""
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
        self._connected = False
    
    def is_connected(self):
        """Check if the serial connection is active"""
        return self._connected and self.arduino and self.arduino.is_open
    
    def send_command(self, command):
        """Send a command to the Arduino and return the response"""
        if not self.is_connected():
            return "ERROR: Not connected"
        try:
            self.arduino.write((command + "\n").encode())
            # Wait for response with timeout
            time.sleep(0.1)
            response = ""
            while self.arduino.in_waiting:
                print(1)
                response += self.arduino.readline().decode().strip()
            print("try")
            return response
        except Exception as e:
            print(f"Command error: {e}")
            return f"ERROR: {str(e)}"
    
    def check_power(self):
        """Check the power level of the device"""
        response = self.send_command("CHECK POWER")
        try:
            # Assuming the response is in the format "POWER:XX" where XX is the power percentage
            if "POWER:" in response:
                power_level = int(response.split("POWER:")[1].strip())
                return power_level
            return 0
        except:
            return 0
    
    def test_transmission(self):
        """Test data transmission with the device"""
        response = self.send_command("TEST TRANSMISSION")
        print("response: ", response)
        return "OK" in response
    