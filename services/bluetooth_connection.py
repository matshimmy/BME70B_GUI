import asyncio
import time
from bleak import BleakClient, BleakScanner
from services.connection_interface import ConnectionInterface

class BluetoothConnection(ConnectionInterface):
    """Bluetooth connection implementation using bleak library"""
    
    # You'll need to replace these with your actual device characteristics
    DEVICE_NAME = "YourDeviceName"
    COMMAND_CHARACTERISTIC = "0000ffxx-0000-1000-8000-00805f9b34fb"
    RESPONSE_CHARACTERISTIC = "0000ffyy-0000-1000-8000-00805f9b34fb"
    
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
        # Write the command
        await self.client.write_gatt_char(self.COMMAND_CHARACTERISTIC, (command + "\n").encode())
        
        # Read the response
        await asyncio.sleep(0.5)  # Give device time to process
        response = await self.client.read_gatt_char(self.RESPONSE_CHARACTERISTIC)
        return response.decode().strip()
    
    def check_power(self):
        """Check the power level of the device"""
        response = self.send_command("CHECK POWER")
        try:
            # Assuming the response is in the format "POWER:XX" where XX is the battery percentage
            if "POWER:" in response:
                power_level = int(response.split("POWER:")[1].strip())
                return power_level
            return 0
        except:
            return 0
    
    def test_transmission(self):
        """Test data transmission with the device"""
        response = self.send_command("TEST TRANSMISSION")
        return "OK" in response 