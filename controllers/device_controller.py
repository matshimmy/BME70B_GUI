from PyQt5.QtCore import QThread
from services.system_check_service import SystemCheckService
from services.graceful_disconnect_service import GracefulDisconnectService
from services.acquisition_service import AcquisitionService
from controllers.state_machine import StateMachine

from enums.connection_type import ConnectionType

class DeviceController:
    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine

        # ----------------------------------------------------------------
        # System Check Thread & Service
        # ----------------------------------------------------------------
        self.systemCheckThread = QThread()
        self.systemCheckService = SystemCheckService()

        # Move the systemCheckService to the systemCheckThread
        self.systemCheckService.moveToThread(self.systemCheckThread)

        # Connect the systemCheckThread's started signal
        self.systemCheckThread.started.connect(self.systemCheckService.run_system_check)

        # Connect system check signals to local handlers
        self.systemCheckService.connection_checked.connect(self.handle_connect_checked)
        self.systemCheckService.power_checked.connect(self.handle_power_checked)
        self.systemCheckService.transmission_checked.connect(self.handle_transmission_checked)
        self.systemCheckService.finished.connect(self.handle_system_check_done)

        self.system_check_running = False

        # ----------------------------------------------------------------
        # Graceful Disconnect Thread & Service
        # ----------------------------------------------------------------
        self.disconnectThread = QThread()
        self.disconnectService = GracefulDisconnectService()

        # Move the gracefulDisconnectService to the disconnectThread
        self.disconnectService.moveToThread(self.disconnectThread)

        # Connect the thread's started signal to run_graceful_disconnect
        self.disconnectThread.started.connect(self.disconnectService.run_graceful_disconnect)

        # Connect graceful disconnect signals to local handlers
        self.disconnectService.disconnect_conn_done.connect(self.handle_disconnect_conn_done)
        self.disconnectService.disconnect_power_done.connect(self.handle_disconnect_power_done)
        self.disconnectService.disconnect_trans_done.connect(self.handle_disconnect_trans_done)
        self.disconnectService.disconnect_finished.connect(self.handle_graceful_disconnect_done)

        self.disconnect_running = False

        # ----------------------------------------------------------------
        # Acquisition Thread & Service
        # ----------------------------------------------------------------
        self.acquisitionThread = QThread()
        self.acquisitionService = AcquisitionService(self.state_machine.model)

        # Move the service to the acquisitionThread
        self.acquisitionService.moveToThread(self.acquisitionThread)

        # Connect the thread's started signal to run_acquisition
        self.acquisitionThread.started.connect(self.acquisitionService.run_acquisition)

        # Connect service signals
        self.acquisitionService.chunk_received.connect(self.handle_data_chunk_received)

        self.acquisition_running = False

    # --------------------------------------------------------------------------
    # SYSTEM CHECK TASK
    # --------------------------------------------------------------------------
    def start_system_check(self, connection_type : ConnectionType):
        self.state_machine.connect_device(connection_type)

        if not self.system_check_running:
            self.system_check_running = True
            self.systemCheckThread.start()

    def abort_system_check(self):
        if self.system_check_running:
            self.systemCheckThread.requestInterruption()
            self.state_machine.disconnect_device()
            self.systemCheckThread.quit()
            self.systemCheckThread.wait()
            self.system_check_running = False

    # Handlers for system check signals
    def handle_connect_checked(self):
        self.state_machine.do_system_check_connection()

    def handle_power_checked(self):
        self.state_machine.do_system_check_power()

    def handle_transmission_checked(self):
        self.state_machine.do_system_test_transmission()

    def handle_system_check_done(self):
        self.system_check_running = False
        self.systemCheckThread.quit()
        self.systemCheckThread.wait()
        self.state_machine.do_system_check_done()

    # --------------------------------------------------------------------------
    # GRACEFUL DISCONNECT TASK
    # --------------------------------------------------------------------------
    def start_graceful_disconnect(self):
        self.state_machine.do_graceful_disconnect()

        if not self.disconnect_running:
            self.disconnect_running = True
            self.disconnectThread.start()

    def force_disconnect(self):
        if self.disconnect_running:
            self.state_machine.disconnect_device()
            self.disconnectThread.requestInterruption()
            self.disconnectThread.quit()
            self.disconnect_running = False

    # Handlers for graceful disconnect signals
    def handle_disconnect_conn_done(self):
        self.state_machine.do_graceful_disconnect_conn()

    def handle_disconnect_power_done(self):
        self.state_machine.do_graceful_disconnect_power()

    def handle_disconnect_trans_done(self):
        self.state_machine.do_graceful_disconnect_trans()

    def handle_graceful_disconnect_done(self):
        self.disconnect_running = False
        self.disconnectThread.quit()
        self.disconnectThread.wait()
        self.state_machine.do_graceful_disconnect_done()

    # --------------------------------------------------------------------------
    # ACQUISITION TASK
    # --------------------------------------------------------------------------
    def start_acquisition(self):
        if not self.acquisition_running:
            self.state_machine.start_acquisition()
            self.acquisition_running = True
            self.acquisitionThread.start()

    def stop_acquisition(self):
        if self.acquisition_running:
            self.state_machine.stop_acquisition()
            self.acquisitionThread.requestInterruption()
            self.acquisitionThread.quit()
            self.acquisition_running = False

    def handle_data_chunk_received(self, chunk):
        self.state_machine.append_acquisition_data(chunk)

    # --------------------------------------------------------------------------
    # OTHER DEVICE TASKS (ACQUISITION, SIMULATION, STIMULATION)
    # --------------------------------------------------------------------------
    def disconnect_device(self):
        self.state_machine.disconnect_device()

    def start_simulation(self):
        self.state_machine.start_simulation()

    def start_stimulation(self):
        self.state_machine.start_stimulation()
