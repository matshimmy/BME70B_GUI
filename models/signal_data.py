import numpy as np

class SignalData:
    def __init__(self, sample_rate=100):
        self.reset(sample_rate)

    def reset(self, sample_rate):
        self.sample_rate = sample_rate
        self.data = np.empty((0,))

    def append_chunck(self, chunck):
        self.data = np.concatenate([self.data, chunck])

    def export_wfdb(self, file_prefix: str):
        """
        Convert 'data' into .dat + .hea format.
        Could use a library like wfdb to handle it or manual writing if you prefer.
        """
        pass

    def export_csv(self, filename: str):
        """
        Write data to a CSV for quick debugging or user convenience.
        """
        pass
