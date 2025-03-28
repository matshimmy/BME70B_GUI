import serial
import time
import serial.tools.list_ports
from services.connection_interface import ConnectionInterface

class USBConnection(ConnectionInterface):
    """USB/Serial connection implementation"""
    
    @staticmethod
    def scan_for_arduino():
        """Scan all available COM ports and return a list of potential Arduino ports"""
        arduino_ports = []
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Check for Nano 33 IoT or Nano 33 BLE specific identifiers
            description = port.description.lower()
            hwid = port.hwid.lower()
            
            # Nano 33 IoT identifiers
            if any(identifier in description for identifier in ['nano 33 iot', 'nano33iot']):
                arduino_ports.append(port.device)
            # Nano 33 BLE identifiers
            elif any(identifier in description for identifier in ['nano 33 ble', 'nano33ble']):
                arduino_ports.append(port.device)
            # Check hardware IDs for both boards
            elif any(identifier in hwid for identifier in [
                '2341:805a',  # Nano 33 IoT
                '2341:8057',  # Nano 33 BLE
                '2341:8058'   # Alternative Nano 33 BLE ID
            ]):
                arduino_ports.append(port.device)
        
        return arduino_ports
    
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
            # Clear any existing data in the buffer
            self.arduino.reset_input_buffer()
            
            # Send the command
            self.arduino.write((command + "\n").encode())
            
            # Wait for acknowledgment with timeout
            start_time = time.time()
            ack_received = False
            while time.time() - start_time < 2.0:  # 2 second timeout
                if self.arduino.in_waiting:
                    ack = self.arduino.readline().decode().strip()
                    if ack == "ACK":
                        ack_received = True
                        break
                time.sleep(0.01)  # Small sleep to prevent CPU spinning
            
            if not ack_received:
                return "ERROR: No acknowledgment received"
            
            # Now wait for the actual response with timeout
            start_time = time.time()
            response = ""
            while time.time() - start_time < 2.0:  # 2 second timeout
                if self.arduino.in_waiting:
                    response = self.arduino.readline().decode().strip()
                    if response:  # If we got a non-empty response
                        break
                time.sleep(0.01)  # Small sleep to prevent CPU spinning
            
            if not response:
                return "ERROR: No response received"
                
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
    