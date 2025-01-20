from PyQt5.QtCore import QObject, pyqtSignal
import time

class SystemCheckWorker(QObject):
    # emit signals at each step
    connection_checked = pyqtSignal()
    power_checked = pyqtSignal()
    transmission_checked = pyqtSignal()
    finished = pyqtSignal()

    def run_system_check(self):
        """
        Blocks for a bit to simulate real hardware checks.
        """
        time.sleep(2)
        self.connection_checked.emit() # Signal that connection is checked

        time.sleep(2)  # Simulate checking power
        self.power_checked.emit()
        
        time.sleep(2)  # Simulate checking transmission
        self.transmission_checked.emit()

        self.finished.emit()
