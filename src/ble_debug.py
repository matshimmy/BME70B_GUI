import asyncio
from bleak import BleakClient, BleakScanner
import logging
from collections import deque
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UUIDs from your Arduino code
SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
WRITE_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789def"
READ_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-12345678090e"

# Global variables for data collection
data_buffer = deque()  # Current 1-second buffer
all_data = []  # All collected data
stop_event = asyncio.Event()
start_time = None

def calculate_crc(packet):
    """Calculate CRC for a packet (excluding the CRC value itself)."""
    # Find the start of the data (after the header)
    start_index = packet.find(',') + 1
    
    # Find the last comma (before the CRC)
    last_comma = packet.rfind(',')
    if last_comma == -1:
        return None
    
    # Get the data portion (excluding header and CRC)
    data_portion = packet[start_index:last_comma]
    
    # Calculate CRC (sum of all numbers mod 256)
    crc = 0
    for num_str in data_portion.split(','):
        try:
            crc += int(num_str)
        except ValueError:
            return None
    
    return crc % 256

def parse_data_packet(data_str):
    """Parse the data packet and return the values if CRC is valid."""
    try:
        # Split the packet into parts
        parts = data_str.split(',')
        
        # If this is not a data packet (doesn't start with SINE,), return None
        if not data_str.startswith("SINE,"):
            return None
            
        if len(parts) < 3:  # Need at least header, one value, and CRC
            logger.error("Invalid packet format")
            return None
            
        # Extract CRC from packet
        received_crc = int(parts[-1])
        
        # Calculate expected CRC
        expected_crc = calculate_crc(data_str)
        
        if expected_crc is None:
            logger.error("Failed to calculate CRC")
            return None
            
        # Verify CRC
        if received_crc != expected_crc:
            logger.error(f"CRC mismatch! Received: {received_crc}, Expected: {expected_crc}")
            return None
            
        # If CRC is valid, return the values
        values_str = parts[1:-1]  # Exclude header and CRC
        return [int(val) for val in values_str]
    except Exception as e:
        logger.error(f"Error parsing data packet: {e}")
        return None

async def notification_handler(sender, data):
    """Handle incoming notifications from the device."""
    global start_time, data_buffer, all_data
    
    if start_time is None:
        start_time = time.time()
    
    # Parse the data packet
    data_str = data.decode()
    
    # If this is a command response (not starting with SINE,), just log it
    if not data_str.startswith("SINE,"):
        logger.info(f"Received response: {data_str}")
        return
        
    # Parse the data packet
    values = parse_data_packet(data_str)
    
    # If values is None, CRC check failed
    if values is None:
        logger.error("CRC verification failed on data packet. Stopping collection...")
        stop_event.set()
        return
    
    # Add values to current buffer
    data_buffer.extend(values)
    
    # Check if we have a full second of data
    current_time = time.time()
    if current_time - start_time >= 1.0:
        # Add current buffer to all data
        all_data.extend(list(data_buffer))
        logger.info(f"Buffer full! Collected {len(data_buffer)} points. Total points: {len(all_data)}")
        
        # Clear buffer and reset start time
        data_buffer.clear()
        start_time = current_time
        
        # Check if we've collected 2 seconds of data
        if len(all_data) >= 40:  # 20 Hz * 2 seconds = 40 points
            logger.info("Collected 2 seconds of data. Stopping...")
            stop_event.set()

async def main():
    # Scan for devices
    logger.info("Scanning for devices...")
    devices = await BleakScanner.discover()
    
    # Find our device
    target_device = None
    for device in devices:
        if device.name == "Nano33BLE":
            target_device = device
            break
    
    if not target_device:
        logger.error("Nano33BLE device not found!")
        return
    
    logger.info(f"Found device: {target_device.name} ({target_device.address})")
    
    try:
        # Connect to the device
        async with BleakClient(target_device.address, timeout=20.0) as client:
            logger.info("Connected to device")
            
            # Set up notification handler
            await client.start_notify(READ_CHARACTERISTIC_UUID, notification_handler)
            
            # Set sampling rate (20 Hz)
            logger.info("Setting sampling rate to 20 Hz...")
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, "SET SAMPLE 20".encode())
            
            # Set signal frequency (1 Hz)
            logger.info("Setting signal frequency to 1 Hz...")
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, "SET FREQ 1".encode())
            
            # Start acquisition
            logger.info("Starting acquisition...")
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, "START ACQ".encode())
            
            # Wait until we've collected 2 seconds of data or CRC error occurs
            while not stop_event.is_set():
                await asyncio.sleep(0.1)
            
            # Stop acquisition
            logger.info("Stopping acquisition...")
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, "STOP ACQ".encode())
            
            # Log final results
            logger.info(f"Collection complete! Total points collected: {len(all_data)}")
            logger.info(f"Data points: {all_data}")
                
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 