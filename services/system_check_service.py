from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time

class SystemCheckService(QObject):
    """
    Worker dedicated to running the system check in a separate thread.
    """
    connection_checked = pyqtSignal()
    power_checked = pyqtSignal()
    transmission_checked = pyqtSignal()
    finished = pyqtSignal()

    def run_system_check(self):
        """
        Perform each check in ~7 seconds total,
        with checks for interruption after each 1-second sleep.
        """
        # 1) Connection check (2 seconds)
        for _ in range(2):
            if QThread.currentThread().isInterruptionRequested():
                return
            time.sleep(1)
        self.connection_checked.emit()

        # 2) Power check (2 seconds)
        for _ in range(2):
            if QThread.currentThread().isInterruptionRequested():
                return
            time.sleep(1)
        self.power_checked.emit()

        # 3) Transmission check (2 seconds)
        for _ in range(2):
            if QThread.currentThread().isInterruptionRequested():
                return
            time.sleep(1)
        self.transmission_checked.emit()

        # Final 1-second pause
        if not QThread.currentThread().isInterruptionRequested():
            time.sleep(1)
            self.finished.emit()
