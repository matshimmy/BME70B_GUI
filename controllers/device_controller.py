from PyQt5.QtCore import QThread
from services.system_check_service import SystemCheckService
from services.graceful_disconnect_service import GracefulDisconnectService
from services.acquisition_service import AcquisitionService
from services.simulation_service import SimulationService
from controllers.state_machine import StateMachine
from services.usb_connection import USBConnection
from enums.connection_type import ConnectionType

class DeviceController:
    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine
        self.active_connection = None  # Store the active connection for reuse

        # ----------------------------------------------------------------
        # System Check Thread & Service
        # ----------------------------------------------------------------
        self.systemCheckThread = QThread()
        self.systemCheckService = SystemCheckService(self.state_machine.model)

        # Move the systemCheckService to the systemCheckThread
        self.systemCheckService.moveToThread(self.systemCheckThread)

        # Connect the systemCheckThread's started signal
        self.systemCheckThread.started.connect(self.systemCheckService.run_system_check)

        # Connect system check signals to local handlers
        self.systemCheckService.connection_checked.connect(self.handle_connect_checked)
        self.systemCheckService.power_checked.connect(self.handle_power_checked)
        self.systemCheckService.transmission_checked.connect(self.handle_transmission_checked)
        self.systemCheckService.finished.connect(self.handle_system_check_done)
        self.systemCheckService.error.connect(self.handle_system_check_error)

        self.system_check_running = False

        # ----------------------------------------------------------------
        # Graceful Disconnect Thread & Service
        # ----------------------------------------------------------------
        self.disconnectThread = QThread()
        self.disconnectService = GracefulDisconnectService()
        self.disconnectService.moveToThread(self.disconnectThread)
        self.disconnectThread.started.connect(self.disconnectService.run_disconnect)

        # Connect graceful disconnect signals to local handlers
        self.disconnectService.disconnect_conn_done.connect(self.handle_disconnect_conn_done)
        self.disconnectService.disconnect_power_done.connect(self.handle_disconnect_power_done)
        self.disconnectService.disconnect_trans_done.connect(self.handle_disconnect_trans_done)
        self.disconnectService.disconnect_finished.connect(self.handle_graceful_disconnect_done)
        self.disconnectService.error.connect(self.handle_disconnect_error)

        self.disconnect_running = False

        # ----------------------------------------------------------------
        # Acquisition Thread & Service
        # ----------------------------------------------------------------
        self.acquisitionThread = QThread()
        # We'll create the acquisition service when needed with the active connection
        self.acquisitionService = None
        self.acquisition_running = False

        # ----------------------------------------------------------------
        # Simulation Thread & Service
        # ----------------------------------------------------------------
        self.simulationThread = QThread()
        # We'll create the simulation service when needed with the active connection
        self.simulationService = None
        self.simulation_running = False

    # --------------------------------------------------------------------------
    # SYSTEM CHECK TASK
    # --------------------------------------------------------------------------
    def start_system_check(self, connection_type: ConnectionType):
        """Start the system check with the specified connection type"""
        # Set the connection type for the system check
        self.systemCheckService.set_connection_type(connection_type)
        
        # Connect the device in the state machine
        self.state_machine.connect_device(connection_type)
        
        # Start the system check thread if it's not running
        if not self.systemCheckThread.isRunning():
            self.systemCheckThread.start()

    def abort_system_check(self):
        """Abort the system check"""
        if self.systemCheckThread.isRunning():
            # Request interruption
            self.systemCheckThread.requestInterruption()
            # Abort the system check service
            self.systemCheckService.abort()
            # Wait for the thread to finish
            self.systemCheckThread.quit()
            self.systemCheckThread.wait()
            # Return to idle state
            self.state_machine.disconnect_device()
        else:
            self.state_machine.disconnect_device()
        self.active_connection = None

    def handle_connect_checked(self, success: bool):
        """Handle when connection check is complete"""
        self.state_machine.do_system_check_connection(success)

    def handle_power_checked(self, power_level: int):
        """Handle when power check is complete"""
        # Update the model with the power level
        self.state_machine.do_system_check_power()

    def handle_transmission_checked(self, transmission_ok: bool):
        """Handle when transmission check is complete"""
        # Update the model with the transmission status
        self.state_machine.do_system_test_transmission(transmission_ok)

    def handle_system_check_done(self):
        """Handle when the system check is complete"""
        # Save the active connection for later use
        self.active_connection = self.systemCheckService.connection
        
        # Clean up the thread
        self.systemCheckThread.quit()
        self.systemCheckThread.wait()
        # Update the state machine
        self.state_machine.do_system_check_done()

    def handle_system_check_error(self, error_message: str):
        """Handle system check errors"""
        print(f"System check error: {error_message}")
        # Clean up the thread
        self.systemCheckThread.quit()
        self.systemCheckThread.wait()
        # Don't transition to IDLE - let user click abort to do that

    # --------------------------------------------------------------------------
    # GRACEFUL DISCONNECT TASK
    # --------------------------------------------------------------------------
    def start_graceful_disconnect(self):
        """Start the graceful disconnect process"""
        if not self.active_connection:
            print("Error: No active connection to disconnect")
            self.state_machine.disconnect_device()
            return
            
        if not self.disconnect_running:
            self.disconnect_running = True
            
            # Set the connection for the disconnect service
            self.disconnectService.set_connection(self.active_connection)
            
            # Update the state machine
            self.state_machine.do_graceful_disconnect()
            
            # Start the disconnect thread
            if not self.disconnectThread.isRunning():
                self.disconnectThread.start()

    def force_disconnect(self):
        """Force an immediate disconnect"""
        # If a graceful disconnect is in progress, abort it
        if self.disconnectThread.isRunning():
            self.disconnectThread.requestInterruption()
            self.disconnectService.abort()
            self.disconnectThread.quit()
            self.disconnectThread.wait()
            
        # If we have an active connection, disconnect it
        if self.active_connection:
            try:
                self.active_connection.disconnect()
            except Exception as e:
                print(f"Error during force disconnect: {e}")
            
        # Clear the active connection
        self.active_connection = None
        
        # Update the state machine
        self.state_machine.disconnect_device()
        
        self.disconnect_running = False

    def handle_disconnect_conn_done(self):
        """Handle when connection disconnect is complete"""
        self.state_machine.do_graceful_disconnect_conn()

    def handle_disconnect_power_done(self):
        """Handle when power disconnect is complete"""
        self.state_machine.do_graceful_disconnect_power()

    def handle_disconnect_trans_done(self):
        """Handle when transmission disconnect is complete"""
        self.state_machine.do_graceful_disconnect_trans()

    def handle_graceful_disconnect_done(self):
        """Handle when the graceful disconnect is complete"""
        self.disconnect_running = False
        self.disconnectThread.quit()
        self.disconnectThread.wait()
        
        # Clear the active connection
        self.active_connection = None
        
        # Update the state machine
        self.state_machine.do_graceful_disconnect_done()
        
    def handle_disconnect_error(self, error_message: str):
        """Handle disconnect errors"""
        print(f"Disconnect error: {error_message}")
        # Just force disconnect if there's an error
        self.force_disconnect()

    # --------------------------------------------------------------------------
    # ACQUISITION TASK
    # --------------------------------------------------------------------------
    def start_acquisition(self):
        """Start the acquisition process"""
        if self.active_connection is None:
            print("Error: No active connection available")
            return
            
        if not self.acquisition_running:
            self.acquisition_running = True
            
            # Create the acquisition service with the active connection
            self.acquisitionService = AcquisitionService(self.state_machine.model, self.active_connection)
            
            # Move the service to the acquisitionThread
            self.acquisitionService.moveToThread(self.acquisitionThread)
            
            # Connect the thread's started signal to run_acquisition
            self.acquisitionThread.started.connect(self.acquisitionService.run_acquisition)
            
            # Connect service signals
            self.acquisitionService.chunk_received.connect(self.handle_data_chunk_received)
            self.acquisitionService.finished.connect(self.handle_acquisition_finished)
            self.acquisitionService.error.connect(self.handle_acquisition_error)
            
            # Start the thread
            self.acquisitionThread.start()
            
            # Update the state machine
            self.state_machine.start_acquisition()

    def stop_acquisition(self):
        """Stop the acquisition process"""
        if self.acquisition_running:
            # Request interruption and quit the thread
            self.acquisitionThread.requestInterruption()
            self.acquisitionThread.quit()
            self.acquisitionThread.wait()
            self.acquisition_running = False
            
            # Update the state machine
            self.state_machine.stop_acquisition()

    def handle_data_chunk_received(self, chunk):
        """Handle received data chunks"""
        # Pass the data to the state machine for processing
        self.state_machine.append_acquisition_data(chunk)
        
    def handle_acquisition_finished(self):
        """Handle acquisition completion"""
        self.acquisition_running = False
        self.acquisitionThread.quit()
        self.acquisitionThread.wait()
        
    def handle_acquisition_error(self, error_message):
        """Handle acquisition errors"""
        print(f"Acquisition error: {error_message}")
        self.stop_acquisition()

    # --------------------------------------------------------------------------
    # SIMULATION TASK
    # --------------------------------------------------------------------------
    def start_simulation(self):
        """Start the simulation process"""
        if self.active_connection is None:
            print("Error: No active connection available")
            return
            
        if not isinstance(self.active_connection, USBConnection):
            print("Error: Simulation only supports USB connections")
            return
            
        if not self.simulation_running:
            self.simulation_running = True
            
            # Set up the device controller in the signal simulation model first
            self.state_machine.model.signal_simulation.set_device_controller(self)
            
            # Create the simulation service with the active connection
            self.simulationService = SimulationService(self.state_machine.model, self.active_connection)
            
            # Move the service to the simulationThread
            self.simulationService.moveToThread(self.simulationThread)
            
            # Connect the thread's started signal to run_simulation
            self.simulationThread.started.connect(self.simulationService.run_simulation)
            
            # Connect service signals
            self.simulationService.finished.connect(self.handle_simulation_finished)
            self.simulationService.error.connect(self.handle_simulation_error)
            self.simulationService.ready.connect(self.handle_simulation_ready)  # Connect to ready signal
            
            # Start the thread
            self.simulationThread.start()

    def stop_simulation(self):
        """Stop the simulation process"""
        if self.simulation_running:
            # Request interruption and quit the thread
            self.simulationThread.requestInterruption()
            self.simulationThread.quit()
            self.simulationThread.wait()
            self.simulation_running = False
            
            # Update the state machine
            self.state_machine.stop_simulation()

    def handle_simulation_finished(self):
        """Handle simulation completion"""
        self.simulation_running = False
        self.simulationThread.quit()
        self.simulationThread.wait()
        
    def handle_simulation_error(self, error_message):
        """Handle simulation errors"""
        print(f"Simulation error: {error_message}")
        self.stop_simulation()

    def handle_simulation_ready(self):
        """Handle when simulation service is ready"""
        # Update the state machine after service is ready
        self.state_machine.start_simulation()

    def send_simulation_data(self, data):
        """Send data to the simulation service"""
        if self.simulationService and self.simulation_running:
            return self.simulationService.send_data(data)
        return False

    # --------------------------------------------------------------------------
    # OTHER DEVICE TASKS (ACQUISITION, STIMULATION)
    # --------------------------------------------------------------------------
    def disconnect_device(self):
        self.state_machine.disconnect_device()

    def start_stimulation(self):
        pass
        # self.state_machine.start_stimulation()

    def stop_stimulation(self):
        pass
        # self.state_machine.stop_stimulation()
