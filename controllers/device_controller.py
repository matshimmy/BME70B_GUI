from PyQt5.QtCore import QThread
from services.system_check_service import SystemCheckService
from services.graceful_disconnect_service import GracefulDisconnectService
from services.acquisition_service import AcquisitionService
from controllers.state_machine import StateMachine

class DeviceController:
    """
    The DeviceController manages two separate Services and threads:
      1) systemCheckThread / SystemCheckService, for system checks
      2) disconnectThread / GracefulDisconnectService, for graceful disconnect
    Each thread is started/stopped independently.
    """
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
        self.acquisitionService = AcquisitionService()

        # Move the service to the acquisitionThread
        self.acquisitionService.moveToThread(self.acquisitionThread)

        # Connect the thread's started signal to run_acquisition
        self.acquisitionThread.started.connect(self.acquisitionService.run_acquisition)

        # Connect service signals
        self.acquisitionService.chunk_received.connect(self.handle_data_chunk_received)
        self.acquisitionService.finished.connect(self.handle_acquisition_done)

        self.acquisition_running = False

    # --------------------------------------------------------------------------
    # SYSTEM CHECK TASK
    # --------------------------------------------------------------------------
    def start_system_check(self, connection_type: str):
        """
        1) Tells the state machine to connect the device (e.g. USB or Bluetooth).
        2) Starts the system check thread to run the system check Service logic.
        """
        self.state_machine.connect_device(connection_type)

        if not self.system_check_running:
            self.system_check_running = True
            self.systemCheckThread.start()

    def abort_system_check(self):
        """
        Cancels an ongoing system check by requesting interruption,
        quitting the thread, and telling the state machine to disconnect.
        """
        if self.system_check_running:
            self.systemCheckThread.requestInterruption()
            self.state_machine.disconnect_device()
            self.systemCheckThread.quit()
            self.systemCheckThread.wait()
            self.system_check_running = False

    # Handlers for system check signals
    def handle_connect_checked(self):
        """
        Service signals that the device connection check step is done.
        """
        self.state_machine.do_system_check_connection()

    def handle_power_checked(self):
        self.state_machine.do_system_check_power()

    def handle_transmission_checked(self):
        self.state_machine.do_system_test_transmission()

    def handle_system_check_done(self):
        """
        Service signals the entire system check is finished. 
        Stop the thread and let the state machine proceed.
        """
        self.system_check_running = False
        self.systemCheckThread.quit()
        self.systemCheckThread.wait()
        self.state_machine.do_system_check_done()

    # --------------------------------------------------------------------------
    # GRACEFUL DISCONNECT TASK
    # --------------------------------------------------------------------------
    def start_graceful_disconnect(self):
        """
        Tells the state machine to transition to the graceful disconnect state,
        then starts the disconnect thread to run the gracefulDisconnectService logic.
        """
        self.state_machine.do_graceful_disconnect()

        if not self.disconnect_running:
            self.disconnect_running = True
            self.disconnectThread.start()

    def force_disconnect(self):
        """
        Cancels an ongoing graceful disconnect by requesting interruption 
        and stopping the thread.
        NOTE: Depending on your desired logic, you might still want to forcibly 
        finalize or skip steps.
        """
        if self.disconnect_running:
            self.disconnectThread.requestInterruption()
            self.state_machine.disconnect_device()
            self.disconnectThread.quit()
            self.disconnectThread.wait()
            self.disconnect_running = False

    # Handlers for graceful disconnect signals
    def handle_disconnect_conn_done(self):
        """
        Service signals that the "Ending Connection" step is finished.
        Optionally, update the model or log progress.
        """
        self.state_machine.do_graceful_disconnect_conn()

    def handle_disconnect_power_done(self):
        self.state_machine.do_graceful_disconnect_power()

    def handle_disconnect_trans_done(self):
        self.state_machine.do_graceful_disconnect_trans()

    def handle_graceful_disconnect_done(self):
        """
        Service signals the entire graceful disconnect is finished.
        Stop the thread, reset flags, and let the state machine finalize.
        """
        self.disconnect_running = False
        self.disconnectThread.quit()
        self.disconnectThread.wait()
        self.state_machine.do_graceful_disconnect_done()


    # --------------------------------------------------------------------------
    # ACQUISITION TASK
    # --------------------------------------------------------------------------
    def start_acquisition(self):
        """
        Called from the RunningAcquisitionWidget or state machine
        to begin data acquisition.
        """
        # Possibly transition states
        self.state_machine.start_acquisition()

        if not self.acquisition_running:
            self.acquisition_running = True
            self.acquisitionThread.start()

    def abort_acquisition(self):
        """
        Cancels an ongoing acquisition by requesting interruption,
        quitting the thread, etc.
        """
        if self.acquisition_running:
            self.acquisitionThread.requestInterruption()
            # Optionally: self.state_machine.disconnect_device() or something else
            self.acquisitionThread.quit()
            self.acquisitionThread.wait()
            self.acquisition_running = False

    def handle_data_chunk_received(self, chunk):
        """
        A new chunk of mock data arrived. Store it in the model.
        """
        # for example, if you have model.signal_data
        self.state_machine.model.signal_data.append_samples(chunk)
        self.state_machine.model.model_changed.emit()

    def handle_acquisition_done(self):
        """
        The entire mock acquisition finished (time limit reached).
        Stop the thread and finalize the state if needed.
        """
        self.acquisition_running = False
        self.acquisitionThread.quit()
        self.acquisitionThread.wait()
        # Possibly transition states or notify
        # e.g., self.state_machine.acquisition_complete()

    # --------------------------------------------------------------------------
    # OTHER DEVICE TASKS (ACQUISITION, SIMULATION, STIMULATION)
    # --------------------------------------------------------------------------
    def disconnect_device(self):
        """
        Immediate or forced disconnect (bypassing graceful).
        """
        self.state_machine.disconnect_device()

    def start_simulation(self):
        self.state_machine.start_simulation()

    def start_stimulation(self):
        self.state_machine.start_stimulation()
