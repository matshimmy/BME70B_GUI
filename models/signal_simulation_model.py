import numpy as np
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class SignalSimulationModel(QObject):
    simulation_chunk_ready = pyqtSignal()  # Signal when new data is ready

    def __init__(self):
        super().__init__()
        self._transmission_rate = 100  # Hz
        self._buffer_size = 100  # points
        self._time_data = np.array([])
        self._signal_data = np.array([])
        self._signal_transferred_data = np.array([])
        self._time_transferred_data = np.array([])
        self._current_transfer_index = 0
        
        # Simulation timer
        self._simulation_timer = QTimer()
        self._simulation_timer.timeout.connect(self._transfer_next_chunk)
        
        # Artifact parameters
        self._muscle_artifact = False
        self._random_movement_artifact = False
        self._sixty_hz_artifact = False
        
        # Artifact generation parameters
        self._muscle_amplitude = 0.2
        self._random_movement_amplitude = 0.1
        self._sixty_hz_amplitude = 0.15
        
        self.reset()

    def start_simulation(self):
        # Calculate timer interval based on buffer size and transmission rate
        interval_ms = int((self._buffer_size / self._transmission_rate) * 1000)
        self._simulation_timer.setInterval(interval_ms)
        self._simulation_timer.start()

    def pause_simulation(self):
        self._simulation_timer.stop()

    def reset(self):
        self._time_data = np.zeros(self._buffer_size)
        self._signal_data = np.zeros(self._buffer_size)
        self._signal_transferred_data = np.array([])
        self._time_transferred_data = np.array([])
        self._current_transfer_index = 0
        self._simulation_timer.stop()
        self._template_mode = False
        self._template_data = None

    def set_template_data(self, template_data: np.ndarray, template_duration: float):
        self.reset()
        self._template_mode = True
        self._template_data = template_data
        self._buffer_size = len(template_data)
        
        # Create time array for one template cycle
        self._time_data = np.linspace(0, template_duration, len(template_data))
        self._signal_data = template_data

    def _transfer_next_chunk(self):
        if len(self._signal_data) == 0:
            return

        start_idx = self._current_transfer_index
        end_idx = start_idx + self._buffer_size

        if end_idx >= len(self._signal_data) and not self._template_mode:
            self._simulation_timer.stop()
            return
        
        if self._template_mode:
            cycle_duration = self._time_data[-1] - self._time_data[0]
            current_cycle = self._current_transfer_index // len(self._signal_data)
            new_time = self._time_data + (cycle_duration * current_cycle)
            new_signal = self._signal_data.copy()
        else:
            new_time = self._time_data[start_idx:end_idx]
            new_signal = self._signal_data[start_idx:end_idx].copy()

        # Add artifacts to the new chunk
        chunk_size = len(new_signal)
        new_signal += self._generate_muscle_artifact(chunk_size)
        new_signal += self._generate_random_movement_artifact(chunk_size)
        new_signal += self._generate_sixty_hz_artifact(new_time)
        
        # Store the data with artifacts
        if len(self._signal_transferred_data) == 0:
            self._signal_transferred_data = new_signal
            self._time_transferred_data = new_time
        else:
            self._signal_transferred_data = np.append(self._signal_transferred_data, new_signal)
            self._time_transferred_data = np.append(self._time_transferred_data, new_time)

        self._current_transfer_index += self._buffer_size
        self.simulation_chunk_ready.emit()

    def set_artifacts(self, muscle: bool, random_movement: bool, sixty_hz: bool):
        self._muscle_artifact = muscle
        self._random_movement_artifact = random_movement
        self._sixty_hz_artifact = sixty_hz

    def _generate_muscle_artifact(self, num_points: int) -> np.ndarray:
        if not self._muscle_artifact:
            return np.zeros(num_points)
        
        # Generate high-frequency noise (EMG-like)
        noise = np.random.normal(0, 1, num_points)
        # Apply bandpass-like filtering using moving average
        window_size = 5
        filtered_noise = np.convolve(noise, np.ones(window_size)/window_size, mode='same')
        # Add some random amplitude modulation to make it more realistic
        envelope = np.abs(np.random.normal(0, 1, num_points))
        envelope = np.convolve(envelope, np.ones(20)/20, mode='same')  # Smooth the envelope
        return filtered_noise * envelope * self._muscle_amplitude

    def _generate_random_movement_artifact(self, num_points: int) -> np.ndarray:
        if not self._random_movement_artifact:
            return np.zeros(num_points)
        
        # Only generate movement artifact occasionally (10% chance per chunk)
        if np.random.random() > 0.1:
            return np.zeros(num_points)
        
        # Generate a smooth, random baseline wander
        movement = np.zeros(num_points)
        # Random direction and amplitude
        amplitude = np.random.normal(0, self._random_movement_amplitude)
        # Create smooth transition using half a sine wave
        duration = min(num_points, int(self._transmission_rate * 0.5))  # ~0.5 second movement
        movement[:duration] = amplitude * np.sin(np.linspace(0, np.pi, duration))
        return movement

    def _generate_sixty_hz_artifact(self, time_points: np.ndarray) -> np.ndarray:
        if not self._sixty_hz_artifact:
            return np.zeros_like(time_points)

        return self._sixty_hz_amplitude * np.sin(2 * np.pi * 60 * time_points)
    
    def load_csv_data(self, file_path: str, transmission_rate: int):
        self.reset()
        self._transmission_rate = transmission_rate
        data = pd.read_csv(file_path)
        self._time_data = data['Time_s'].values
        self._signal_data = data['Signal'].values

        self._resample_signal(self._time_data, self._signal_data)

    def _resample_signal(self, time_data: np.ndarray, signal_data: np.ndarray):
        # Calculate original sampling rate
        original_sampling_rate = 1 / np.mean(np.diff(time_data))
        
        # Calculate number of points needed for new sampling rate
        num_points = int(len(time_data) * (self._transmission_rate / original_sampling_rate))
        
        # Create new time array with desired transmission rate
        new_time_data = np.linspace(time_data[0], time_data[-1], num_points)
        
        # Interpolate signal to new sampling rate
        self._signal_data = np.interp(new_time_data, time_data, signal_data)
        self._time_data = new_time_data
