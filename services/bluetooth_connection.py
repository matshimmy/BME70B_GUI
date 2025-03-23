import asyncio
import threading
from queue import Queue, Empty
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
        self._notification_callback = None
        self._data_buffer = []
        self._sampling_rate = 0
        self._ble_thread = None
        self._command_queue = Queue()
        self._response_queue = Queue()
        self._stop_event = threading.Event()
    
    def connect(self):
        """Establish connection to the Bluetooth device"""
        try:
            # Start BLE thread
            self._ble_thread = threading.Thread(target=self._ble_thread_loop)
            self._ble_thread.daemon = True
            self._ble_thread.start()
            
            # Wait for connection result
            result = self._response_queue.get(timeout=10.0)
            self._connected = result
            return result
        except Exception as e:
            print(f"Bluetooth Connection error: {e}")
            self._connected = False
            return False
    
    def _ble_thread_loop(self):
        """Run BLE operations in a separate thread with its own event loop"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            # Connect to device
            self._loop.run_until_complete(self._connect_async())
            
            # Process commands until stopped
            while not self._stop_event.is_set():
                try:
                    # Check for commands
                    command = self._command_queue.get_nowait()
                    # Handle special commands
                    if isinstance(command, tuple):
                        if command[0] == "START_NOTIFY":
                            try:
                                self._loop.run_until_complete(self._start_notifications_async())
                                self._response_queue.put(True)
                            except Exception as e:
                                print(f"Error starting notifications: {e}")
                                self._response_queue.put(False)
                        elif command[0] == "STOP_NOTIFY":
                            try:
                                self._loop.run_until_complete(self._stop_notifications_async())
                                self._response_queue.put(True)
                            except Exception as e:
                                print(f"Error stopping notifications: {e}")
                                self._response_queue.put(False)
                        elif command[0] == "DISCONNECT":
                            # Handle disconnect command
                            try:
                                success = self._loop.run_until_complete(self._disconnect_async())
                                self._response_queue.put(success)
                            except Exception as e:
                                print(f"Error during disconnect: {e}")
                                self._response_queue.put(False)
                            break  # Exit the command processing loop
                    else:
                        # Handle regular commands
                        response = self._loop.run_until_complete(self._send_command_async(command))
                        self._response_queue.put(response)
                except Empty:
                    pass
                
                # Run event loop for a short time
                self._loop.run_until_complete(asyncio.sleep(0.1))
                
        except Exception as e:
            print(f"BLE thread error: {e}")
        finally:
            if not self._loop.is_closed():
                self._loop.close()
    
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
            self._response_queue.put(False)
            return False
        
        # Connect to the device
        print(f"Connecting to {self.device.name}...")
        self.client = BleakClient(self.device.address)
        connected = await self.client.connect()
        
        if connected:
            print(f"Connected to {self.device.name}")
            self._response_queue.put(True)
            return True
        else:
            print("Failed to connect")
            self._response_queue.put(False)
            return False
    
    async def _disconnect_async(self):
        """Async method to disconnect from the Bluetooth device"""
        try:
            if self.client:
                # Try to stop notifications, but don't fail if they're already stopped
                try:
                    await self.client.stop_notify(self.RESPONSE_CHARACTERISTIC)
                except Exception as e:
                    pass  # Ignore errors when stopping notifications
                
                # Then disconnect
                await self.client.disconnect()
                return True
        except Exception as e:
            print(f"Error in disconnect_async: {e}")
        return False

    def disconnect(self):
        """Disconnect from the Bluetooth device"""
        try:
            # First stop any ongoing data transmission
            if self.is_connected():
                self.send_command("STOP ACQ")
            
            # Send disconnect command to the BLE thread
            if self._command_queue:
                self._command_queue.put(("DISCONNECT", None))
                # Wait for disconnect to complete
                try:
                    success = self._response_queue.get(timeout=1.0)
                except:
                    pass
            
            # Set stop event to signal thread to terminate
            self._stop_event.set()
            
            # Wait for thread to finish with timeout
            if self._ble_thread:
                self._ble_thread.join(timeout=1.0)  # Wait up to 1 second
            
            self._connected = False
        except Exception as e:
            print(f"Error during disconnect: {e}")
            self._connected = False
    
    def is_connected(self):
        """Check if the Bluetooth connection is active"""
        return self._connected and self.client and self.client.is_connected
    
    def send_command(self, command):
        """Send a command to the Bluetooth device and return the response"""
        if not self.is_connected():
            return "ERROR: Not connected"
        
        try:
            self._command_queue.put(command)
            response = self._response_queue.get(timeout=5.0)
            return response
        except Exception as e:
            print(f"Command error: {e}")
            return f"ERROR: {str(e)}"
    
    async def _send_command_async(self, command):
        """Async method to send command and receive response"""
        try:
            # Handle special commands
            if isinstance(command, tuple):
                if command[0] == "STOP_NOTIFY":
                    await self._stop_notifications_async()
                    return True
                else:
                    raise ValueError(f"Unknown special command: {command[0]}")
            
            # Handle regular string commands
            command = command.strip()
            cmd_bytes = command.encode()
            
            # Try to write to the characteristic
            await self.client.write_gatt_char(self.COMMAND_CHARACTERISTIC, cmd_bytes)
            
            # For START ACQ command, we don't need to wait for a response
            # as data will come through notifications
            if command == "START ACQ":
                return "Streaming started"
            
            # For other commands, read the response
            await asyncio.sleep(0.5)  # Give device time to process
            response = await self.client.read_gatt_char(self.RESPONSE_CHARACTERISTIC)
            
            # Decode response
            return response.decode().strip()
            
        except Exception as e:
            print(f"Error in send_command_async: {e}")
            raise
    
    def set_notification_callback(self, callback):
        """Set the callback function for notifications"""
        self._notification_callback = callback
    
    async def _notification_handler(self, sender, data):
        """Handle incoming notifications from the device"""
        try:
            data_str = data.decode()
            
            # If this is a command response (not starting with SINE,), ignore it
            if not data_str.startswith("SINE,"):
                return
                
            # Parse the data packet
            parts = data_str.split(',')
            if len(parts) < 3:  # Need at least header, one value, and CRC
                return
                
            # Extract CRC from packet
            received_crc = int(parts[-1])
            
            # Calculate expected CRC
            values = [int(val) for val in parts[1:-1]]  # Exclude header and CRC
            calculated_crc = sum(values) % 256
            
            # Verify CRC
            if received_crc != calculated_crc:
                return
            
            # Convert ADC values to voltage: V = ADC * (3.3/4095)
            voltages = [adc * (3.3/4095) for adc in values]
            
            # Add to buffer
            self._data_buffer.extend(voltages)
            
            # If we have enough data for one second, emit it
            if len(self._data_buffer) >= self._sampling_rate:
                if self._notification_callback:
                    self._notification_callback(self._data_buffer[:self._sampling_rate])
                self._data_buffer = self._data_buffer[self._sampling_rate:]
                
        except Exception as e:
            print(f"Error in notification handler: {e}")
            import traceback
            traceback.print_exc()
    
    def start_notifications(self, sampling_rate):
        """Start receiving notifications from the device"""
        if not self.is_connected():
            return False
            
        try:
            # Convert sampling rate to integer
            self._sampling_rate = int(sampling_rate)
            self._data_buffer = []
            # Send command to start notifications through the command queue
            self._command_queue.put(("START_NOTIFY", self._sampling_rate))
            # Wait for confirmation
            response = self._response_queue.get(timeout=5.0)
            return response
        except Exception as e:
            print(f"Error starting notifications: {e}")
            return False
    
    async def _start_notifications_async(self):
        """Async method to start notifications"""
        await self.client.start_notify(self.RESPONSE_CHARACTERISTIC, self._notification_handler)
    
    def stop_notifications(self):
        """Stop receiving notifications from the device"""
        if not self.is_connected():
            return
            
        try:
            # Send command to stop notifications through the command queue
            self._command_queue.put(("STOP_NOTIFY", None))
            # Wait for confirmation
            response = self._response_queue.get(timeout=5.0)
            if not response:
                print("Failed to stop notifications")
        except Exception as e:
            print(f"Error stopping notifications: {e}")
    
    async def _stop_notifications_async(self):
        """Async method to stop notifications"""
        await self.client.stop_notify(self.RESPONSE_CHARACTERISTIC)
        return True
    
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
