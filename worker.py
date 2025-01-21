# worker.py
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time

class Worker(QObject):
    connection_checked = pyqtSignal()
    power_checked = pyqtSignal()
    transmission_checked = pyqtSignal()
    finished = pyqtSignal()

    def run_system_check(self):
        """
        Perform each check, but break the 2-second sleeps into 1-second chunks
        so we can check for interruption mid-sleep.
        """
        # 1) Connection check phase (2 seconds total)
        for _ in range(2):
            if QThread.currentThread().isInterruptionRequested():
                return  # Exit gracefully
            time.sleep(1)
        self.connection_checked.emit()

        # 2) Power check phase
        for _ in range(2):
            if QThread.currentThread().isInterruptionRequested():
                return
            time.sleep(1)
        self.power_checked.emit()

        # 3) Transmission check phase
        for _ in range(2):
            if QThread.currentThread().isInterruptionRequested():
                return
            time.sleep(1)
        self.transmission_checked.emit()

        self.finished.emit()
