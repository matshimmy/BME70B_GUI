from PyQt5.QtCore import QObject, pyqtSignal, QThread

from models.model import Model
from services.connection_interface import ConnectionInterface

class StimulationService(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    ready = pyqtSignal()  # Signal to indicate service is ready

    def __init__(self, model: Model, connection: ConnectionInterface):
        super().__init__()
        self.model = model
        self.connection = connection
        self._running = False
        self._configured = False

    def configure_stimulation(self):
        """Configure the device for stimulation with the current model settings"""
        try:
            # Send frequency command
            frequency = str(self.model.stimulation_frequency)
            response = self.connection.send_command(f"SET FREQ {frequency}")
            if "ERROR" in response:
                self.error.emit(f"Failed to set frequency: {response}")
                return False

            # Send duty cycle command
            duty_cycle = str(self.model.stimulation_duty_cycle)
            response = self.connection.send_command(f"SET DUTY {duty_cycle}")
            if "ERROR" in response:
                self.error.emit(f"Failed to set duty cycle: {response}")
                return False

            self._configured = True
            return True
        except Exception as e:
            self.error.emit(f"Error configuring stimulation: {str(e)}")
            return False

    def send_command(self, command: str):
        """Send a stimulation command"""
        try:
            response = self.connection.send_command(command)
            return response
        except Exception as e:
            self.error.emit(f"Error sending command: {str(e)}")
            return False

    def stop_stimulation(self):
        """Stop the stimulation process"""
        try:
            response = self.connection.send_command("STOP")
            if "ERROR" in response:
                self.error.emit(f"Failed to stop stimulation: {response}")
                return False
            return True
        except Exception as e:
            self.error.emit(f"Error stopping stimulation: {str(e)}")
            return False

    def run_stimulation(self):
        """Main stimulation control loop"""
        try:
            if not self.connection.is_connected():
                self.error.emit("Device not connected")
                return

            self.configure_stimulation()

            self._running = True
            self.ready.emit()  # Signal that service is ready

            # Keep running until stopped
            while self._running:
                if QThread.currentThread().isInterruptionRequested():
                    self._running = False
                    break
                QThread.msleep(100)  # Sleep to prevent busy waiting

        except Exception as e:
            self.error.emit(f"Stimulation error: {str(e)}")
        finally:
            # Clean up when stopping
            self._running = False
            try:
                self.stop_stimulation()
            except Exception as e:
                print(f"Error during cleanup: {e}")
            finally:
                self.finished.emit() 