import time
import os
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from models.model import Model
from services.connection_interface import ConnectionInterface

class AcquisitionService(QObject):
    chunk_received = pyqtSignal(object)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model: Model, connection: ConnectionInterface):
        super().__init__()
        self.model = model
        self.connection = connection
        self._running = False
        self.chunk_buffer = []

    def configure_acquisition(self):
        """Configure the device for acquisition with the current model settings"""
        # Send configuration commands based on the model settings
        sampling_freq = str(self.model.sampling_rate)
        response = self.connection.send_command(f"SET SAMPLE {sampling_freq}")
        print(f"Configure sampling rate response: {response}")
        
        # You can add additional configuration commands here based on your protocol
        response = self.connection.send_command("SET FREQ 1")
        print(f"Configure signal frequency response: {response}")

    def start_acquisition(self):
        """Start the acquisition process"""
        response = self.connection.send_command("START")
        print(f"Start acquisition response: {response}")
        
        if "ERROR" in response:
            self.error.emit(f"Failed to start acquisition: {response}")
            return False
        
        return "Streaming started" in response

    def run_acquisition(self):
        """Main acquisition loop that collects data and emits chunks"""
        try:
            if not self.connection.is_connected():
                self.error.emit("Device not connected")
                return
                
            # Configure and start acquisition
            self.configure_acquisition()
            if not self.start_acquisition():
                self.error.emit("Failed to start acquisition")
                return
                
            self._running = True
            chunk_size = 30  # Number of samples to collect before emitting

            while self._running:
                if QThread.currentThread().isInterruptionRequested():
                    self._running = False
                    break

                # Get data from the device
                try:
                    # For serial connection, read directly from the device
                    if hasattr(self.connection, 'arduino') and self.connection.arduino.in_waiting:
                        data = float(self.connection.arduino.readline().decode().strip())
                        self.chunk_buffer.append(data)
                    # For other connections, use a command to get data
                    else:
                        response = self.connection.send_command("GET DATA")
                        if response and not response.startswith("ERROR"):
                            try:
                                data = float(response)
                                self.chunk_buffer.append(data)
                            except ValueError:
                                print(f"Invalid data received: {response}")
                    
                    # When we have enough data, emit the chunk
                    if len(self.chunk_buffer) >= chunk_size:
                        chunk = np.array(self.chunk_buffer[:chunk_size])
                        self.chunk_received.emit(chunk)
                        # Keep any remaining data
                        self.chunk_buffer = self.chunk_buffer[chunk_size:]
                
                except Exception as e:
                    print(f"Error during acquisition: {str(e)}")
                    # Don't stop acquisition for occasional errors
            
            # Stop acquisition when we're done
            self.connection.send_command("STOP")
            
        except Exception as e:
            self.error.emit(f"Acquisition error: {str(e)}")
        finally:
            self._running = False
            self.finished.emit()

    def stop(self):
        """Stop the acquisition process"""
        self._running = False
        try:
            # Send stop command to device
            self.connection.send_command("STOP")
        except:
            pass  # Ignore errors during stop
