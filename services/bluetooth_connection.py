import asyncio
import time
from bleak import BleakClient, BleakScanner
from services.connection_interface import ConnectionInterface

class BluetoothConnection(ConnectionInterface):
    """Bluetooth connection implementation using bleak library"""
    
    # Define the service and characteristic UUIDs
    DEVICE_NAME = "Nano33BLE"
    SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
    COMMAND_CHARACTERISTIC = "12345678-1234-1234-1234-123456789def"
    RESPONSE_CHARACTERISTIC = "12345678-1234-1234-1234-12345678090e"
    
    def __init__(self):
        self.device = None
        self.client = None
        self._connected = False
        self.loop = asyncio.new_event_loop()
    
    def connect(self):
        """Establish connection to the Bluetooth device"""
        try:
            result = self.loop.run_until_complete(self._connect_async())
            self._connected = result
            return result
        except Exception as e:
            print(f"Bluetooth Connection error: {e}")
            self._connected = False
            return False
    
    async def _connect_async(self):
        """Async method to establish Bluetooth connection"""
        # Scan for devices
        print("Scanning for Bluetooth devices...")
        devices = await BleakScanner.discover()
        
        # Find our device by name
        for d in devices:
            if d.name == self.DEVICE_NAME:
                self.device = d
                break
        
        if not self.device:
            print(f"Device '{self.DEVICE_NAME}' not found")
            return False
        
        # Connect to the device
        print(f"Connecting to {self.device.name}...")
        self.client = BleakClient(self.device.address)
        connected = await self.client.connect()
        
        if connected:
            print(f"Connected to {self.device.name}")
            
            # Debug: List all services and characteristics
            for service in self.client.services:
                print(f"Service: {service.uuid}")
                for char in service.characteristics:
                    print(f"  Characteristic: {char.uuid}, Properties: {char.properties}")
            
            # Verify our required characteristics are available
            try:
                services = self.client.services
                service_found = False
                for service in services:
                    if service.uuid.lower() == self.SERVICE_UUID.lower():
                        service_found = True
                        print(f"Found service: {service.uuid}")
                        break
                
                if not service_found:
                    print(f"WARNING: Service {self.SERVICE_UUID} not found!")
                    # Continue anyway as the UUIDs might be registered in a different way
            
            except Exception as e:
                print(f"Error checking services: {e}")
                # Continue anyway, as we'll catch errors later when actually using characteristics
            
            return True
        else:
            print("Failed to connect")
            return False
    
    def disconnect(self):
        """Disconnect from the Bluetooth device"""
        if self.client:
            self.loop.run_until_complete(self._disconnect_async())
        self._connected = False
    
    async def _disconnect_async(self):
        """Async method to disconnect from Bluetooth device"""
        await self.client.disconnect()
        self.client = None
    
    def is_connected(self):
        """Check if the Bluetooth connection is active"""
        return self._connected and self.client and self.client.is_connected
    
    def send_command(self, command):
        """Send a command to the Bluetooth device and return the response"""
        if not self.is_connected():
            return "ERROR: Not connected"
        
        try:
            response = self.loop.run_until_complete(self._send_command_async(command))
            return response
        except Exception as e:
            print(f"Command error: {e}")
            return f"ERROR: {str(e)}"
    
    async def _send_command_async(self, command):
        """Async method to send command and receive response"""
        try:
            # Clean the command string and encode it
            command = command.strip()
            cmd_bytes = command.encode()
            print(f"Sending command: '{command}'")
            
            # Try to write to the characteristic
            await self.client.write_gatt_char(self.COMMAND_CHARACTERISTIC, cmd_bytes)
            
            # Read the response
            await asyncio.sleep(0.5)  # Give device time to process
            response = await self.client.read_gatt_char(self.RESPONSE_CHARACTERISTIC)
            
            # Decode response
            decoded = response.decode().strip()
            print(f"Received response: '{decoded}'")
            return decoded
            
        except Exception as e:
            print(f"Error in send_command_async: {e}")
            raise
    
    def check_power(self):
        """Check the power level of the device"""
        try:
            print("Checking power...")
            response = self.send_command("CHECK POWER")
            
            # If the response contains an error, return 0
            if "ERROR:" in response:
                print(f"Power check error: {response}")
                return 0
                
            # Assuming the response is in the format "POWER:XX" where XX is the battery percentage
            if "POWER:" in response:
                power_level = int(response.split("POWER:")[1].strip())
                print(f"Power level reported: {power_level}%")
                return power_level
                
            print(f"Unexpected power response format: {response}")
            return 0
        except Exception as e:
            print(f"Failed to check power level: {e}")
            return 0
    
    def test_transmission(self):
        """Test data transmission with the device"""
        try:
            print("Testing transmission...")
            response = self.send_command("TEST TRANSMISSION")
            return "OK" in response
        except Exception as e:
            print(f"Transmission test failed: {e}")
            return False 