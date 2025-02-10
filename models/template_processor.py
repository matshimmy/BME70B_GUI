import numpy as np

class TemplateProcessor:
    def __init__(
        self,
        sample_rate: float = 100.0,
        init_wait_time_s: float = 20.0,
        update_interval_s: float = 1.0,
        min_template_length_s: float = 0.1
    ):
        """
        :param sample_rate: Samples per second of incoming data.
        :param init_wait_time_s: How many seconds of data to accumulate
                                 before the first template computation.
        :param update_interval_s: How often to (re-)compute the template.
        :param min_template_length_s: Minimum length of the template in seconds.
        """
        self.sample_rate = sample_rate
        self.init_wait_time = init_wait_time_s
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
        if current_buffer_time < self.init_wait_time:
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
        samples_to_analyze = int(self.init_wait_time * self.sample_rate)
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

        # The autocorrelation array is of length 2*len(data_chunk)-1
        # 'mid_point' is the index in 'autocorr' corresponding to zero-lag
        mid_point = len(data_chunk) - 1

        # 4) Skip up to 'mid_lag_offset' to avoid too-small lags
        min_lag_offset = int(self.min_template_length * self.sample_rate)

        # We look for the peak in the region: from mid_point+1+min_lag_offset to the end
        ac_half_plus_min = autocorr[mid_point + 1 + min_lag_offset :]

        # 5) Find local peak in that subarray
        peak_lag_local = np.argmax(ac_half_plus_min)

        # Convert that local index into an absolute lag in samples
        peak_lag_abs = peak_lag_local + min_lag_offset + 1

        # Store as the estimated period
        self.estimated_period = peak_lag_abs

        # Edge case check: if estimated_period is zero or nonsensical, abort
        if self.estimated_period <= 0:
            return

        # 6) Figure out how many full periods fit into 'data_chunk'
        num_full_periods = len(data_chunk) // self.estimated_period
        if num_full_periods < 1:
            # If not even one full period fits, we can't form a repeating pattern
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
