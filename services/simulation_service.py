from PyQt5.QtCore import QObject, pyqtSignal
import time
from models.signal_simulation_model import SignalSimulationModel
from services.connection_interface import ConnectionInterface

class SimulationService(QObject):
    """Service to handle simulation in a separate thread"""
    
    # Signals
    chunk_received = pyqtSignal(object)  # Emitted when a chunk is received
    finished = pyqtSignal()  # Emitted when simulation is complete
    error = pyqtSignal(str)  # Emitted when an error occurs
    
    def __init__(self, model: SignalSimulationModel, connection: ConnectionInterface):
        super().__init__()
        self.model = model
        self.connection = connection
        self._running = False
        
        # Calculate interval between chunks in seconds
        self._interval = self.model._buffer_size / self.model._transmission_rate
    
    def run_simulation(self):
        """Main simulation loop"""
        try:
            self._running = True
            
            # Start the simulation in the model
            self.model.start_simulation()
            
            # Main simulation loop
            while self._running:
                # Get the latest data from the model
                time_data = self.model._time_transferred_data
                signal_data = self.model._signal_transferred_data
                
                # Send the data chunk through the connection
                if self.connection and self.connection.is_connected():
                    success = self.connection.send_data_chunk(time_data, signal_data)
                    if not success:
                        self.error.emit("Failed to send data chunk")
                        self.stop()
                        break
                else:
                    self.error.emit("Connection lost during simulation")
                    self.stop()
                    break
                
                # Wait for the next chunk
                time.sleep(self._interval)
            
        except Exception as e:
            self.error.emit(f"Simulation error: {str(e)}")
            self._running = False
        finally:
            self.model.pause_simulation()
    
    def stop(self):
        """Stop the simulation"""
        self._running = False 