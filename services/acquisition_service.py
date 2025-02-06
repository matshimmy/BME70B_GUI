from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time
import numpy as np

from models.model import Model

class AcquisitionService(QObject):
    chunk_received = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, model: Model):
        super().__init__()
        self._running = False
        self.model = model

    def run_acquisition(self):
        self._running = True

        chunk_size = 10
        freq_hz = 1
        self.phase = 0.0

        while self._running:
            if QThread.currentThread().isInterruptionRequested():
                self._running = False

            # Generate a time array for this chunk from self.phase
            t = np.linspace(
                self.phase,
                self.phase + (chunk_size / self.model.sampling_rate),
                chunk_size,
                endpoint=False
            )
            self.phase += (chunk_size / self.model.sampling_rate)  # advance global phase

            # Generate sine wave + small random noise
            chunk = (np.sin(2 * np.pi * freq_hz * t) + 0.05 * np.random.randn(chunk_size)) * .01

            # Emit this chunk
            self.chunk_received.emit(chunk)

            time.sleep(chunk_size / self.model.sampling_rate)

        self.finished.emit()
