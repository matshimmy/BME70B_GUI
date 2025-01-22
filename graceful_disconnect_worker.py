from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time

class GracefulDisconnectWorker(QObject):
    """
    Worker dedicated to running a graceful disconnect in a separate thread.
    """
    disconnect_conn_done = pyqtSignal()
    disconnect_power_done = pyqtSignal()
    disconnect_trans_done = pyqtSignal()
    disconnect_finished = pyqtSignal()

    def run_graceful_disconnect(self):
        """
        Simulate a ~6-second graceful disconnect sequence, 
        with checks for interruption after each 1-second sleep.
        """
        # 1) Ending connection (2 seconds)
        for _ in range(2):
            if QThread.currentThread().isInterruptionRequested():
                return
            time.sleep(1)
        self.disconnect_conn_done.emit()

        # 2) Shutting off power (2 seconds)
        for _ in range(2):
            if QThread.currentThread().isInterruptionRequested():
                return
            time.sleep(1)
        self.disconnect_power_done.emit()

        # 3) Ending transmission (2 seconds)
        for _ in range(2):
            if QThread.currentThread().isInterruptionRequested():
                return
            time.sleep(1)
        self.disconnect_trans_done.emit()

        # Final 1-second pause
        if not QThread.currentThread().isInterruptionRequested():
            time.sleep(1)
            self.disconnect_finished.emit()
