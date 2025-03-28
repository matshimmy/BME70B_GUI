from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time

from models.model import Model
from services.usb_connection import USBConnection
from enums.simulation_type import SimulationType

class SimulationService(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    ready = pyqtSignal()  # New signal to indicate setup is complete

    def __init__(self, model: Model, connection: USBConnection):
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
        response = self.connection.send_command("START SIM")
        
        if "ERROR" in response:
            self.error.emit(f"Failed to start simulation: {response}")
            return False
        
        return True

    def send_data(self, data: float) -> bool:
        """Send data to the Arduino for simulation using the command interface"""
        try:
            if not self._running:
                self.error.emit("Simulation not running")
                return False

            # Send the data with DATA: prefix
            response = self.connection.send_command(f"DATA:{data:.6f}")
            if "ERROR" in response:
                print(f"SimulationService: Error response from device: {response}")  # Debug print
                return False
            
            # Try to convert response to integer and verify it's in valid range
            try:
                dac_value = int(response)
                return 0 <= dac_value <= 4095
            except ValueError:
                print(f"SimulationService: Invalid response format: {response}")  # Debug print
                return False
            
        except Exception as e:
            print(f"SimulationService: Error sending data: {e}")  # Debug print
            return False

    def run_simulation(self):
        """Run the simulation process"""
        try:
            # Configure simulation settings
            self.configure_simulation()
            
            # Start the simulation
            if not self.start_simulation():
                raise Exception("Failed to start simulation")
                
            # Set running flag
            self._running = True

            # Emit ready signal after setup is complete
            self.ready.emit()
            
            # Main simulation loop
            while self._running and not self.thread().isInterruptionRequested():
                # Process any pending data
                time.sleep(0.01)  # Small sleep to prevent busy waiting
                
        except Exception as e:
            print(f"SimulationService: Error in run_simulation: {str(e)}")
            self.error.emit(str(e))
        finally:
            # Stop the simulation
            self._running = False
            self.connection.send_command("STOP")
            self.finished.emit()
