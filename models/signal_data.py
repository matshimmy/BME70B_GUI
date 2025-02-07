from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

class SignalData(QObject):
    new_chunk_appended = pyqtSignal(np.ndarray)

    def __init__(self, sample_rate=100):
        super().__init__()
        self.reset(sample_rate)

    def reset(self, sample_rate):
        self.sample_rate = sample_rate
        self.data = np.empty((0,))

    def append_chunk(self, chunk):
        self.data = np.concatenate([self.data, chunk])
        # Emit a signal to notify listeners
        self.new_chunk_appended.emit(chunk)
