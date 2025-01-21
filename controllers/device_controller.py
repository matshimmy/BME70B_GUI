from PyQt5.QtCore import QThread
from worker import Worker
from controllers.state_machine import StateMachine

class DeviceController:
    """
    Handles device-related tasks, such as system checks, 
    and owns the thread/worker that simulates those checks.
    """
    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine
        
        # Create the worker and thread
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        # Connect worker signals to methods in this controller
        self.worker.connection_checked.connect(self.handle_connect_checked)
        self.worker.power_checked.connect(self.handle_power_checked)
        self.worker.transmission_checked.connect(self.handle_transmission_checked)
        self.worker.finished.connect(self.handle_system_check_done)

        # Connect the thread’s started signal to the worker’s slot
        self.thread.started.connect(self.worker.run_system_check)
        
        # keep track of whether the thread is running
        self._running = False

    def start_system_check(self, connection_type : str):
        """
        Launch the worker thread to do the system check simulation.
        """
        self.state_machine.connect_device(connection_type)
        if not self._running:
            self._running = True
            self.thread.start()

    def abort_system_check(self):
        """
        Request an interruption and stop the thread gracefully.
        """
        if self._running:
            self.thread.requestInterruption()
            self.state_machine.disconnect_device()
            self.thread.quit()
            self.thread.wait()
            self._running = False

    def handle_connect_checked(self):
        """
        Called when the worker emits 'connection_checked'.
        Updates the model (through the state machine).
        """
        self.state_machine.do_system_check_connection()

    def handle_power_checked(self):
        self.state_machine.do_system_check_power()

    def handle_transmission_checked(self):
        self.state_machine.do_system_test_transmission()

    def handle_system_check_done(self):
        """
        The worker completed all checks. Stop the thread, 
        then tell the state machine to move on.
        """
        self._running = False
        self.thread.quit()
        self.thread.wait()
        self.state_machine.do_system_check_done()

    def disconnect_device(self):
        """
        Called when the user clicks the "Disconnect" button.
        """
        # add disconnect logic here
        self.state_machine.disconnect_device()

    def start_acquisition(self):
        """
        Called when the user clicks the "Start" button.
        """
        pass
        # add start acquisition logic here
        # self.state_machine.start_acquisition()
