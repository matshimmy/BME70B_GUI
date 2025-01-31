from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time
import numpy as np

class AcquisitionService(QObject):
    """
    Mock service that simulates data acquisition from an MCU.
    It generates a 1 Hz sine wave (plus optional noise) in chunks
    and emits them periodically.
    """
    chunk_received = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._running = False

        # Phase (time) tracking to keep a continuous sine wave
        self.phase = 0.0  

    def run_acquisition(self):
        """
        Generate data for ~30 seconds in a loop (mock).
        Each chunk is chunk_size samples at sample_rate.

        If chunk_size=1, you'll still get a perfect 1 Hz wave,
        just delivered 1 sample at a time at 100 samples/sec.
        """
        self._running = True

        sample_rate = 100.0   # e.g., 100 Hz
        total_time = 1000.0     # Acquire for 30 seconds
        chunk_size = 20        # try 1 or 50 etc.
        freq_hz = 0.5         # 1 Hz sine wave

        # Number of chunks total
        num_iterations = int(total_time * sample_rate / chunk_size)

        for _ in range(num_iterations):
            if QThread.currentThread().isInterruptionRequested():
                self._running = False
                return

            # Generate a time array for this chunk from self.phase
            t = np.linspace(
                self.phase,
                self.phase + (chunk_size / sample_rate),
                chunk_size,
                endpoint=False
            )
            self.phase += (chunk_size / sample_rate)  # advance global phase

            # Generate sine wave (1 Hz) + small random noise
            chunk = np.sin(2 * np.pi * freq_hz * t) + 0.05 * np.random.randn(chunk_size)

            # Emit this chunk
            self.chunk_received.emit(chunk)

            # Sleep to simulate real-time arrival
            time.sleep(chunk_size / sample_rate)

        self._running = False
        self.finished.emit()
