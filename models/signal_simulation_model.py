import numpy as np
import pandas as pd

class SignalSimulationModel():
    def __init__(self):
        self._transmission_rate = 100  # Hz
        self._buffer_size = 10000  # points
        self._time_data = np.array([])
        self._signal_data = np.array([])
        
        # Artifact parameters
        self._muscle_artifact = False
        self._random_artifact = False
        self._sixty_hz_artifact = False
        
        # Artifact generation parameters
        self._muscle_amplitude = 0.2
        self._random_amplitude = 0.1
        self._sixty_hz_amplitude = 0.15
        
        self.reset()

    def reset(self):
        self._time_data = np.zeros(self._buffer_size)
        self._signal_data = np.zeros(self._buffer_size)
        self._current_index = 0

    def set_transmission_rate(self, rate: float):
        self._transmission_rate = rate
        self.reset()

    def set_artifacts(self, muscle: bool, random: bool, sixty_hz: bool):
        self._muscle_artifact = muscle
        self._random_artifact = random
        self._sixty_hz_artifact = sixty_hz

    def _generate_muscle_artifact(self, num_points: int) -> np.ndarray:
        if not self._muscle_artifact:
            return np.zeros(num_points)
        
        # Simulate muscle artifact as filtered noise
        noise = np.random.normal(0, 1, num_points)
        # Apply simple moving average as a basic low-pass filter
        window_size = 5
        filtered_noise = np.convolve(noise, np.ones(window_size)/window_size, mode='same')
        return filtered_noise * self._muscle_amplitude

    def _generate_random_artifact(self, num_points: int) -> np.ndarray:
        if not self._random_artifact:
            return np.zeros(num_points)
        
        return np.random.normal(0, self._random_amplitude, num_points)

    def _generate_sixty_hz_artifact(self, time_points: np.ndarray) -> np.ndarray:
        if not self._sixty_hz_artifact:
            return np.zeros_like(time_points)
        
        return self._sixty_hz_amplitude * np.sin(2 * np.pi * 60 * time_points)
    
    def load_csv_data(self, file_path: str):
        data = pd.read_csv(file_path)
        self._time_data = data['Time_s'].values
        self._signal_data = data['Signal'].values
