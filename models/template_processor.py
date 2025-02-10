import os
import re
import numpy as np

import pandas as pd
import wfdb

class TemplateProcessor:
    def __init__(
        self,
        sample_rate: float = 100.0,
        look_back_time_s: float = 4.0,
        update_interval_s: float = 4.0,
        min_template_length_s: float = 0.2
    ):
        """
        :param sample_rate: Samples per second of incoming data.
        :param look_back_time_s: How many seconds of data to accumulate
                                 before the first template computation.
        :param update_interval_s: How often to (re-)compute the template.
        :param min_template_length_s: Minimum length of the template in seconds.
        """
        self.sample_rate = sample_rate
        self.look_back_time = look_back_time_s
        self.update_interval_s = update_interval_s
        self.min_template_length = min_template_length_s

        self.buffer = np.array([], dtype=np.float64)
        self.last_update_time = 0.0
        self.current_template = None
        self.estimated_period = None

    def append_data(self, new_data: np.ndarray):
        self.buffer = np.concatenate([self.buffer, new_data])

        # Compute how many seconds of data we have so far
        current_buffer_time = len(self.buffer) / self.sample_rate

        # If we haven't reached the required initial wait time, do nothing
        if current_buffer_time < self.look_back_time:
            return

        # Check if it's time to update the template
        if (current_buffer_time - self.last_update_time) >= self.update_interval_s:
            self._compute_template()
            self.last_update_time = current_buffer_time

    def _compute_template(self):
        """
        1. Take the last 'samples_to_analyze' samples from the buffer.
        2. Remove DC offset (mean).
        3. Apply a window (Hanning) to reduce edge artifacts.
        4. Compute the full autocorrelation of that windowed data.
        5. Find the first peak in the positive-lag region beyond
           'min_template_length_s'.
        6. Use that as the estimated period for creating a template.
        7. Average across multiple cycles of that period to form the final template.
        """

        # Determine how many samples we will analyze
        samples_to_analyze = int(self.look_back_time * self.sample_rate)
        if len(self.buffer) < samples_to_analyze:
            # Not enough data to do anything
            return

        # Take the last 'samples_to_analyze' samples
        data_chunk = self.buffer[-samples_to_analyze:]

        # 1) Remove DC offset
        data_chunk = data_chunk - np.mean(data_chunk)

        # 2) Window the data to reduce edge effects
        w = np.hanning(len(data_chunk))
        data_windowed = data_chunk * w

        # 3) Compute full autocorrelation
        autocorr = np.correlate(data_windowed, data_windowed, mode='full')

        # The autocorrelation array is length 2*len(data_chunk)-1
        # 'mid_point' is the index in 'autocorr' corresponding to zero-lag
        mid_point = len(data_chunk) - 1

        # 4) Skip up to 'min_lag_offset' to avoid too-small lags
        min_lag_offset = int(self.min_template_length * self.sample_rate)

        # Region: from mid_point+1+min_lag_offset to the end
        ac_half_plus_min = autocorr[mid_point + 1 + min_lag_offset :]

        # 5) Find local peak in that subarray
        peak_lag_local = np.argmax(ac_half_plus_min)

        # Convert that local index into an absolute lag in samples
        peak_lag_abs = peak_lag_local + min_lag_offset + 1

        # Store as the estimated period
        self.estimated_period = peak_lag_abs

        if self.estimated_period <= 0:
            return

        # 6) Figure out how many full periods fit into 'data_chunk'
        num_full_periods = len(data_chunk) // self.estimated_period
        if num_full_periods < 1:
            # Not even one full period
            return

        # We'll only keep data that covers an integer multiple of the period
        valid_length = num_full_periods * self.estimated_period

        # Extract that many samples from the end of the chunk
        valid_data = data_chunk[-valid_length:]

        # 7) Reshape so each row is one period
        reshaped = valid_data.reshape(num_full_periods, self.estimated_period)

        # Average across all rows to form the template
        template = reshaped.mean(axis=0)
        self.current_template = template

    def get_template(self) -> np.ndarray:
        if self.current_template is None:
            return np.array([])
        return self.current_template

    # -------------------------------------------------------------------------
    #  Save CSV & Save WFDB
    # -------------------------------------------------------------------------
    def save_csv(self, filename: str, channel_label="Template"):
        template = self.get_template()
        if template.size == 0:
            print("No template to save.")
            return

        n_points = len(template)
        # Build a time axis for the template
        times = np.linspace(0, (n_points - 1) / self.sample_rate, n_points)

        df = pd.DataFrame({
            "Time_s": times,
            channel_label: template
        })
        df.to_csv(filename, index=False)
        print(f"Template saved as CSV to {filename}")

    def save_wfdb(self, filename: str, channel_label="Template"):
        template = self.get_template()
        if template.size == 0:
            print("No template to save.")
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
        p_signal = template.reshape(-1, 1)

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
        
        print(f"Template saved as WFDB: {os.path.join(dir_name, record_name)}.dat + .hea")
