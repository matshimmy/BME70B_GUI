import numpy as np

class TemplateProcessor:
    def __init__(self,
                 sample_rate: float = 100.0,
                 init_wait_time_s: float = 20.0,
                 update_interval_s: float = 1.0):
        """
        :param sample_rate: Samples per second of incoming data.
        :param init_wait_time_s: How many seconds of data to accumulate
                                 before the first template computation.
        :param update_interval_s: How often to (re-)compute the template.
        """
        self.sample_rate = sample_rate
        self.init_wait_time = init_wait_time_s
        self.update_interval_s = update_interval_s

        self.buffer = np.array([], dtype=np.float64)  # raw data storage
        self.last_update_time = 0.0  # track how many seconds have been processed
        self.current_template = None
        self.estimated_period = None # store the detected period (in samples)

    def append_data(self, new_data: np.ndarray):
        self.buffer = np.concatenate([self.buffer, new_data])

        current_buffer_time = len(self.buffer) / self.sample_rate

        if current_buffer_time < self.init_wait_time:
            return

        if (current_buffer_time - self.last_update_time) >= self.update_interval_s:
            self._compute_template()
            self.last_update_time = current_buffer_time

    def _compute_template(self):
        samples_to_analyze = int(self.init_wait_time * self.sample_rate)
        if len(self.buffer) < samples_to_analyze:
            return  # Not enough data to analyze
        data_chunk = self.buffer[-samples_to_analyze:]

        autocorr = np.correlate(data_chunk, data_chunk, mode='full')

        mid_point = len(data_chunk) - 1

        ac_half = autocorr[mid_point+1:]
        peak_lag = np.argmax(ac_half) + 1  # +1 to offset from mid_point

        self.estimated_period = peak_lag

        num_full_periods = len(data_chunk) // peak_lag
        valid_length = num_full_periods * peak_lag

        valid_data = data_chunk[-valid_length:]

        reshaped = valid_data.reshape(num_full_periods, peak_lag)
        template = reshaped.mean(axis=0)

        self.current_template = template

    def get_template(self) -> np.ndarray:
        if self.current_template is None:
            return np.array([])
        return self.current_template
