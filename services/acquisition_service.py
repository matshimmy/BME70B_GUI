import time
import os
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QThread

import wfdb
from scipy.signal import resample

from models.model import Model

class AcquisitionService(QObject):
    chunk_received = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, model: Model):
        super().__init__()
        self.model = model

        # Internal flags and buffers
        self._running = False
        self.resampled_signals = None
        self.new_fs = None
        self.current_index = 0

    def load_data(self, record_name=os.path.join('services', '426')):
        signals, fields = wfdb.rdsamp(record_name)
        original_fs = fields['fs']

        desired_fs = self.model.sampling_rate

        if not np.isclose(desired_fs, original_fs):
            # Number of original samples
            num_orig_samples = signals.shape[0]
            # Duration in seconds of the entire signal
            duration_sec = num_orig_samples / original_fs
            # Number of new samples to match desired_fs
            num_new_samples = int(np.round(duration_sec * desired_fs))
            # This resamples the entire multi-channel array along axis=0.
            signals = resample(signals, num_new_samples, axis=0)

            self.new_fs = desired_fs
        else:
            # No resampling needed
            self.new_fs = original_fs

        self.resampled_signals = signals
        self.current_index = 0

    def run_acquisition(self):
        self.load_data()

        # extract channel 1
        self.signal = self.resampled_signals[:, 0]

        self._running = True

        # How many samples to emit at a time
        chunk_size = 30

        # The time interval for each sample at the new sampling rate
        sample_interval = 1.0 / self.new_fs

        while self._running:
            # Check if the parent thread requested interruption
            if QThread.currentThread().isInterruptionRequested():
                self._running = False
                break

            start_idx = self.current_index
            end_idx = self.current_index + chunk_size

            if end_idx > self.signal.shape[0]:
                # loop forever
                end_idx = end_idx % self.signal.shape[0]
                self.current_index = 0

            # Extract this chunk
            chunk = self.signal[start_idx:end_idx]
            self.current_index += chunk_size

            self.chunk_received.emit(chunk)

            time.sleep(chunk_size * sample_interval)

        self.finished.emit()
