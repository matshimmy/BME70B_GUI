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
        
        # Set up notification callback if using Bluetooth
        if hasattr(self.connection, 'set_notification_callback'):
            self.connection.set_notification_callback(self._handle_notification)

    def configure_acquisition(self):
        """Configure the device for acquisition with the current model settings"""
        # Send configuration commands based on the model settings
        sampling_freq = str(self.model.sampling_rate)
        response = self.connection.send_command(f"SET SAMPLE {sampling_freq}")
        
        # for sine wave
        response = self.connection.send_command("SET FREQ 1")

    def start_acquisition(self):
        """Start the acquisition process"""
        # If using Bluetooth, start notifications first
        if hasattr(self.connection, 'start_notifications'):
            if not self.connection.start_notifications(self.model.sampling_rate):
                self.error.emit("Failed to start notifications")
                return False
        
        # Then send START ACQ command
        response = self.connection.send_command("START ACQ")
        
        if "ERROR" in response:
            self.error.emit(f"Failed to start acquisition: {response}")
            return False
        
        return True

    def _handle_notification(self, data):
        """Handle incoming notification data from Bluetooth"""
        if self._running:
            # Convert to numpy array and emit
            chunk = np.array(data)
            self.chunk_received.emit(chunk)
        else:
            # Ignore chunks if acquisition is not running
            pass

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

            # If using USB connection, use the old polling method
            if not hasattr(self.connection, 'start_notifications'):
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
                            
                            # When we have enough data for one second, emit the chunk
                            if len(self.chunk_buffer) >= self.model.sampling_rate:
                                chunk = np.array(self.chunk_buffer[:self.model.sampling_rate])
                                self.chunk_received.emit(chunk)
                                # Keep any remaining data
                                self.chunk_buffer = self.chunk_buffer[self.model.sampling_rate:]
                    
                    except Exception as e:
                        print(f"Error during acquisition: {str(e)}")
                        # Don't stop acquisition for occasional errors
            
            # For Bluetooth, we don't need to do anything here as notifications handle the data
            
            # Wait until we're stopped
            while self._running:
                if QThread.currentThread().isInterruptionRequested():
                    self._running = False
                    break
                QThread.msleep(100)  # Sleep to prevent busy waiting
            
            # Stop acquisition when we're done
            self.connection.send_command("STOP ACQ")
            
            # If using Bluetooth, stop notifications
            if hasattr(self.connection, 'stop_notifications'):
                self.connection.stop_notifications()
            
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
            self.connection.send_command("STOP ACQ")
            # If using Bluetooth, stop notifications
            if hasattr(self.connection, 'stop_notifications'):
                self.connection.stop_notifications()
        except:
            pass  # Ignore errors during stop
