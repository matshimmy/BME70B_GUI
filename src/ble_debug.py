import asyncio
from bleak import BleakClient, BleakScanner
import logging
from collections import deque
import time

# Set up logging with less verbose output
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# UUIDs from your Arduino code
SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
WRITE_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789def"
READ_CHARACTERISTIC_UUID = "12345678-1234-1234-1234-12345678090e"

# Global variables for data collection
data_buffer = deque()
all_data = []
stop_event = asyncio.Event()
start_time = None
packet_times = []
sampling_rate = None
collection_start_time = None

def calculate_crc(packet):
    """Calculate CRC for a packet (excluding the CRC value itself)."""
    start_index = packet.find(',') + 1
    last_comma = packet.rfind(',')
    if last_comma == -1:
        return None
    data_portion = packet[start_index:last_comma]
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
        parts = data_str.split(',')
        if not data_str.startswith("SINE,"):
            return None
        if len(parts) < 3:
            return None
        received_crc = int(parts[-1])
        expected_crc = calculate_crc(data_str)
        if expected_crc is None or received_crc != expected_crc:
            return None
        values_str = parts[1:-1]
        return [int(val) for val in values_str]
    except Exception:
        return None

def calculate_timing_stats():
    """Calculate and display timing statistics"""
    if len(packet_times) < 2:
        return
    
    # Only print final statistics when we have enough data
    if len(all_data) >= sampling_rate * 5:
        collection_time = time.time() - collection_start_time
        expected_packets = (sampling_rate * 5) / 6  # 6 samples per packet
        expected_samples = sampling_rate * 5
        
        # Calculate actual sampling rate based on total samples received
        actual_sampling_rate = len(all_data) / collection_time
        
        logger.info(f"\nSampling Rate Test Results:")
        logger.info(f"Requested: {sampling_rate} Hz")
        logger.info(f"Actual: {actual_sampling_rate:.2f} Hz")
        logger.info(f"Expected collection time: 5.00 seconds")
        logger.info(f"Actual collection time: {collection_time:.2f} seconds")
        logger.info(f"Packets received: {len(packet_times)}")
        logger.info(f"Expected packets: {expected_packets:.1f}")
        logger.info(f"Total samples received: {len(all_data)}")
        logger.info(f"Expected samples: {expected_samples}")
        logger.info("------------------------")

async def notification_handler(sender, data):
    """Handle incoming notifications from the device."""
    global start_time, data_buffer, all_data, packet_times
    
    if start_time is None:
        start_time = time.time()
    
    current_time = time.time()
    packet_times.append(current_time)
    
    data_str = data.decode()
    if not data_str.startswith("SINE,"):
        return
        
    values = parse_data_packet(data_str)
    if values is None:
        stop_event.set()
        return
    
    data_buffer.extend(values)
    
    if current_time - start_time >= 1.0:
        all_data.extend(list(data_buffer))
        data_buffer.clear()
        start_time = current_time
        calculate_timing_stats()
        
        # Check if we have enough samples (5 seconds worth)
        if len(all_data) >= sampling_rate * 5:
            stop_event.set()

async def main():
    global sampling_rate, collection_start_time
    
    logger.info("Scanning for devices...")
    devices = await BleakScanner.discover()
    
    target_device = None
    for device in devices:
        if device.name == "Nano33BLE":
            target_device = device
            break
    
    if not target_device:
        logger.error("Nano33BLE device not found!")
        return
    
    logger.info(f"Found device: {target_device.name}")
    
    try:
        async with BleakClient(target_device.address, timeout=20.0) as client:
            logger.info("Connected to device")
            await client.start_notify(READ_CHARACTERISTIC_UUID, notification_handler)
            
            # Test lower sampling rates
            test_rates = [90, 210, 420, 600]
            for rate in test_rates:
                logger.info(f"\nTesting {rate} Hz...")
                sampling_rate = rate
                packet_times.clear()
                all_data.clear()
                data_buffer.clear()
                start_time = None
                collection_start_time = time.time()
                
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, f"SET SAMPLE {rate}".encode())
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, "SET FREQ 1".encode())
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, "START ACQ".encode())
                
                while not stop_event.is_set():
                    await asyncio.sleep(0.1)
                
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, "STOP ACQ".encode())
                stop_event.clear()
                await asyncio.sleep(1.0)
                
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 