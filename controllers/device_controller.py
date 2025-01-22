from PyQt5.QtCore import QThread
from system_check_worker import SystemCheckWorker
from graceful_disconnect_worker import GracefulDisconnectWorker
from controllers.state_machine import StateMachine

class DeviceController:
    """
    The DeviceController manages two separate workers and threads:
      1) systemCheckThread / SystemCheckWorker, for system checks
      2) disconnectThread / GracefulDisconnectWorker, for graceful disconnect
    Each thread is started/stopped independently.
    """
    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine

        # ----------------------------------------------------------------
        # System Check Thread & Worker
        # ----------------------------------------------------------------
        self.systemCheckThread = QThread()
        self.systemCheckWorker = SystemCheckWorker()

        # Move the systemCheckWorker to the systemCheckThread
        self.systemCheckWorker.moveToThread(self.systemCheckThread)

        # Connect the systemCheckThread's started signal
        self.systemCheckThread.started.connect(self.systemCheckWorker.run_system_check)

        # Connect system check signals to local handlers
        self.systemCheckWorker.connection_checked.connect(self.handle_connect_checked)
        self.systemCheckWorker.power_checked.connect(self.handle_power_checked)
        self.systemCheckWorker.transmission_checked.connect(self.handle_transmission_checked)
        self.systemCheckWorker.finished.connect(self.handle_system_check_done)

        self.system_check_running = False

        # ----------------------------------------------------------------
        # Graceful Disconnect Thread & Worker
        # ----------------------------------------------------------------
        self.disconnectThread = QThread()
        self.disconnectWorker = GracefulDisconnectWorker()

        # Move the gracefulDisconnectWorker to the disconnectThread
        self.disconnectWorker.moveToThread(self.disconnectThread)

        # Connect the thread's started signal to run_graceful_disconnect
        self.disconnectThread.started.connect(self.disconnectWorker.run_graceful_disconnect)

        # Connect graceful disconnect signals to local handlers
        self.disconnectWorker.disconnect_conn_done.connect(self.handle_disconnect_conn_done)
        self.disconnectWorker.disconnect_power_done.connect(self.handle_disconnect_power_done)
        self.disconnectWorker.disconnect_trans_done.connect(self.handle_disconnect_trans_done)
        self.disconnectWorker.disconnect_finished.connect(self.handle_graceful_disconnect_done)

        self.disconnect_running = False

    # --------------------------------------------------------------------------
    # SYSTEM CHECK TASK
    # --------------------------------------------------------------------------
    def start_system_check(self, connection_type: str):
        """
        1) Tells the state machine to connect the device (e.g. USB or Bluetooth).
        2) Starts the system check thread to run the system check worker logic.
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
        Worker signals that the device connection check step is done.
        """
        self.state_machine.do_system_check_connection()

    def handle_power_checked(self):
        self.state_machine.do_system_check_power()

    def handle_transmission_checked(self):
        self.state_machine.do_system_test_transmission()

    def handle_system_check_done(self):
        """
        Worker signals the entire system check is finished. 
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
        then starts the disconnect thread to run the gracefulDisconnectWorker logic.
        """
        self.state_machine.do_graceful_disconnect()

        if not self.disconnect_running:
            self.disconnect_running = True
            self.disconnectThread.start()

    def abort_graceful_disconnect(self):
        """
        Cancels an ongoing graceful disconnect by requesting interruption 
        and stopping the thread.
        NOTE: Depending on your desired logic, you might still want to forcibly 
        finalize or skip steps.
        """
        if self.disconnect_running:
            self.disconnectThread.requestInterruption()
            # Potentially call some 'disconnect_device' or forcibly set IDLE
            # e.g. self.state_machine.disconnect_device() or do_graceful_disconnect_done()

            self.disconnectThread.quit()
            self.disconnectThread.wait()
            self.disconnect_running = False

    # Handlers for graceful disconnect signals
    def handle_disconnect_conn_done(self):
        """
        Worker signals that the "Ending Connection" step is finished.
        Optionally, update the model or log progress.
        """
        # self.model.xxx = ...
        pass

    def handle_disconnect_power_done(self):
        pass

    def handle_disconnect_trans_done(self):
        pass

    def handle_graceful_disconnect_done(self):
        """
        Worker signals the entire graceful disconnect is finished.
        Stop the thread, reset flags, and let the state machine finalize.
        """
        self.disconnect_running = False
        self.disconnectThread.quit()
        self.disconnectThread.wait()
        self.state_machine.do_graceful_disconnect_done()

    # --------------------------------------------------------------------------
    # OTHER DEVICE TASKS (ACQUISITION, SIMULATION, STIMULATION)
    # --------------------------------------------------------------------------
    def disconnect_device(self):
        """
        Immediate or forced disconnect (bypassing graceful).
        """
        self.state_machine.disconnect_device()

    def start_acquisition(self):
        self.state_machine.start_acquisition()

    def start_simulation(self):
        self.state_machine.start_simulation()

    def start_stimulation(self):
        self.state_machine.start_stimulation()
