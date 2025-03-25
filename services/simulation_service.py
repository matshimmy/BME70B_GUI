from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time

from models.model import Model
from services.connection_interface import ConnectionInterface
from enums.simulation_type import SimulationType

class SimulationService(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model: Model, connection: ConnectionInterface):
        super().__init__()
        self.model = model
        self.connection = connection
        self._running = False
        self.device_controller = None  # Will be set by the device controller

    def set_device_controller(self, controller):
        """Set the device controller for sending data"""
        self.device_controller = controller

    def configure_simulation(self):
        """Configure the simulation based on the model settings"""
        # Set template mode based on simulation type
        template_mode = self.model.simulation_type == SimulationType.TEMPLATE
        template_command = "SET TEMPLATE TRUE" if template_mode else "SET TEMPLATE FALSE"
        response = self.connection.send_command(template_command)
        if "ERROR" in response:
            raise Exception(f"Failed to configure template mode: {response}")

    def start_simulation(self):
        """Start the simulation process"""
        print("Starting simulation...")
        response = self.connection.send_command("START SIM")
        print(f"Start simulation response: {response}")
        
        if "ERROR" in response:
            self.error.emit(f"Failed to start simulation: {response}")
            return False
        
        return True

    def send_data(self, data: float) -> bool:
        """Send data to the Arduino for simulation using the command interface"""
        try:
            print(f"SimulationService: Checking if simulation is running...")  # Debug print
            print(f"SimulationService: _running flag: {self._running}")  # Debug print
            if not self._running:
                self.error.emit("Simulation not running")
                return False

            # Send the data as a command
            print(f"SimulationService: Sending data {data:.4f} to device")  # Debug print
            print(f"SimulationService: Connection status: {self.connection.is_connected()}")  # Debug print
            response = self.connection.send_command(f"{data:.6f}")
            print(f"SimulationService: Device response: {response}")  # Debug print
            if "ERROR" in response:
                print(f"SimulationService: Error response from device: {response}")  # Debug print
                return False
            return "OK" in response
            
        except Exception as e:
            print(f"SimulationService: Error sending data: {e}")  # Debug print
            return False

    def run_simulation(self):
        """Run the simulation process"""
        try:
            print("SimulationService: Starting run_simulation")
            
            # Configure simulation settings
            print("SimulationService: Configuring simulation...")
            self.configure_simulation()
            print("SimulationService: Configuration complete")
            
            # Start the simulation
            print("SimulationService: Starting simulation...")
            if not self.start_simulation():
                raise Exception("Failed to start simulation")
            print("SimulationService: Simulation started successfully")
                
            # Set running flag
            self._running = True
            print("SimulationService: Running flag set to True")
            
            # Main simulation loop
            print("SimulationService: Entering main simulation loop")
            while self._running and not self.thread().isInterruptionRequested():
                # Process any pending data
                time.sleep(0.01)  # Small sleep to prevent busy waiting
                
        except Exception as e:
            print(f"SimulationService: Error in run_simulation: {str(e)}")
            self.error.emit(str(e))
        finally:
            print("SimulationService: Cleaning up simulation...")
            # Stop the simulation
            self._running = False
            self.connection.send_command("STOP")
            self.finished.emit()
            print("SimulationService: Cleanup complete")
