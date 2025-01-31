class SignalData:
    def __init__(self, sample_rate=100, num_channels=1):
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.samples = []  # or a NumPy array

    def append_samples(self, new_samples):
        # new_samples could be a list or np.array of shape (num_channels, chunk_size)
        self.samples.append(new_samples)

    def clear(self):
        self.samples = []

    def export_wfdb(self, file_prefix: str):
        """
        Convert 'samples' into .dat + .hea format.
        Could use a library like wfdb to handle it or manual writing if you prefer.
        """
        pass

    def export_csv(self, filename: str):
        """
        Write samples to a CSV for quick debugging or user convenience.
        """
        pass
