import os
import re
import pandas as pd
import wfdb
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal

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
        self.new_chunk_appended.emit(chunk)

    def save_csv(self, filename: str, channel_label="Signal"):
        n_points = len(self.data)
        if n_points == 0:
            # No data to save
            return

        times = np.linspace(0, (n_points - 1)/self.sample_rate, n_points)
        df = pd.DataFrame({
            "Time_s": times,
            channel_label: self.data
        })
        df.to_csv(filename, index=False)
        print(f"Data saved as CSV to {filename}")

    def save_wfdb(self, filename: str, channel_label="Signal"):
        n_points = len(self.data)
        if n_points == 0:
            return

        # Extract directory and base filename
        dir_name = os.path.dirname(filename)  # e.g., "C:\Users\Your Name\Documents"
        base_name = os.path.basename(filename)  # e.g., "my_template.dat"
        
        # Remove the .dat extension from base_name
        record_name, _ = os.path.splitext(base_name)  # "my_template"
        
        # If necessary, sanitize record_name to remove spaces or other chars
        # (WFDB only allows letters, numbers, and hyphens)
        record_name = re.sub(r'[^A-Za-z0-9-]+', '-', record_name)
        
        # Reshape template
        p_signal = self.data.reshape(-1, 1)
        wfdb.wrsamp(
            record_name=record_name,
            fs=self.sample_rate,
            sig_name=[channel_label],
            units=["V"],
            p_signal=p_signal,
            fmt=["212"],
            adc_gain=[200],
            baseline=[0],
            write_dir=dir_name
        )
        print(f"WFDB record saved as {record_name}.dat + {record_name}.hea")
