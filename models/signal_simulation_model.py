import numpy as np
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
import time

class DataGenerationThread(QThread):
    data_ready = pyqtSignal(float)  # Signal for sending data to device
    buffer_ready = pyqtSignal()     # Signal for updating visualization
    
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self._running = False
        self._transmission_rate = 100  # Hz
        self._buffer_size = self._transmission_rate
        self._time_data = np.array([])
        self._signal_data = np.array([])
        self._current_index = 0
        self._template_mode = False
        self._template_data = None
        self._last_send_time = 0
        self._last_buffer_time = 0
        self._device_controller = None
        self._paused = True
        self._model = model  # Store the main model reference

    def set_data(self, time_data, signal_data, template_mode=False, template_data=None):
        self._time_data = time_data
        self._signal_data = signal_data
        self._template_mode = template_mode
        self._template_data = template_data
        self._current_index = 0
        self._last_send_time = time.time()

    def set_transmission_rate(self, rate):
        self._transmission_rate = rate
        self._buffer_size = rate

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def run(self):
        self._running = True
        # Wait for model's simulation_running to be True before starting the loop
        while self._running and not self._model.simulation_running:
            time.sleep(0.01)  # Small sleep while waiting
            
        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue

            current_time = time.time()
            elapsed = current_time - self._last_send_time
            interval = 1.0 / self._transmission_rate

            if elapsed >= interval:
                if self._template_mode:
                    value = self._signal_data[self._current_index % len(self._signal_data)]
                else:
                    if self._current_index >= len(self._signal_data):
                        self._running = False
                        break
                    value = self._signal_data[self._current_index]

                # Send data point directly to device if controller is available
                if self._device_controller:
                    self._device_controller.send_simulation_data(value)
                
                # Update visualization buffer
                if self._current_index % self._buffer_size == 0:
                    self.buffer_ready.emit()

                self._current_index += 1
                self._last_send_time = current_time

            time.sleep(0.01)

    def stop(self):
        self._running = False
        self._paused = True

class SignalSimulationModel(QObject):
    simulation_chunk_ready = pyqtSignal()

    def __init__(self, model=None):
        super().__init__()
        self._transmission_rate = 100  # Hz
        self._buffer_size = self._transmission_rate
        self._time_data = np.array([])
        self._signal_data = np.array([])
        self._signal_transferred_data = np.array([])
        self._time_transferred_data = np.array([])
        self._current_transfer_index = 0
        
        # Data generation thread
        self._generation_thread = DataGenerationThread(self, model)  # Pass the model to the thread
        self._generation_thread.buffer_ready.connect(self._handle_buffer_ready)
        
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
        self._generation_thread.resume()
        self._generation_thread.start()

    def pause_simulation(self):
        self._generation_thread.pause()

    def resume_simulation(self):
        self._generation_thread.resume()

    def reset(self):
        self._time_data = np.zeros(self._buffer_size)
        self._signal_data = np.zeros(self._buffer_size)
        self._signal_transferred_data = np.array([])
        self._time_transferred_data = np.array([])
        self._current_transfer_index = 0
        self._generation_thread.stop()
        self._generation_thread.wait()
        self._template_mode = False
        self._template_data = None

    def set_device_controller(self, controller):
        self._generation_thread._device_controller = controller

    def set_artifacts(self, muscle: bool, random_movement: bool, sixty_hz: bool):
        """Set which artifacts to include in the simulation"""
        self._muscle_artifact = muscle
        self._random_movement_artifact = random_movement
        self._sixty_hz_artifact = sixty_hz

    def set_template_data(self, template_data: np.ndarray, template_duration: float):
        """Set up template mode with the given template data"""
        self.reset()
        self._template_mode = True
        self._template_data = template_data
        self._buffer_size = len(template_data)
        
        # Create time array for one template cycle
        self._time_data = np.linspace(0, template_duration, len(template_data))
        self._signal_data = template_data
        self._generation_thread.set_data(self._time_data, self._signal_data, True, template_data)

    def load_csv_data(self, file_path: str, transmission_rate: int):
        """Load signal data from a CSV file"""
        self.reset()
        self._transmission_rate = transmission_rate
        data = pd.read_csv(file_path)
        self._time_data = data['Time_s'].values
        self._signal_data = data['Signal'].values

        self._resample_signal(self._time_data, self._signal_data)
        self._generation_thread.set_data(self._time_data, self._signal_data)
        self._generation_thread.set_transmission_rate(transmission_rate)

    def _resample_signal(self, time_data: np.ndarray, signal_data: np.ndarray):
        """Resample the signal to match the desired transmission rate"""
        # Calculate original sampling rate
        original_sampling_rate = 1 / np.mean(np.diff(time_data))
        
        # Calculate number of points needed for new sampling rate
        num_points = int(len(time_data) * (self._transmission_rate / original_sampling_rate))
        
        # Create new time array with desired transmission rate
        new_time_data = np.linspace(time_data[0], time_data[-1], num_points)
        
        # Interpolate signal to new sampling rate
        self._signal_data = np.interp(new_time_data, time_data, signal_data)
        self._time_data = new_time_data

    def _handle_buffer_ready(self):
        """Handle buffer ready for visualization"""
        if self._template_mode:
            cycle_duration = self._time_data[-1] - self._time_data[0]
            current_cycle = self._current_transfer_index // len(self._signal_data)
            new_time = self._time_data + (cycle_duration * current_cycle)
            new_signal = self._signal_data.copy()
        else:
            buffer_size = self._generation_thread._buffer_size
            start_time = self._current_transfer_index / self._transmission_rate
            end_time = (self._current_transfer_index + buffer_size) / self._transmission_rate
            new_time = np.linspace(start_time, end_time, buffer_size)
            
            start_idx = self._current_transfer_index
            end_idx = start_idx + buffer_size
            if end_idx > len(self._signal_data):
                end_idx = len(self._signal_data)
            new_signal = self._signal_data[start_idx:end_idx].copy()
            
            if len(new_signal) < buffer_size:
                new_signal = np.pad(new_signal, (0, buffer_size - len(new_signal)))

        # Add artifacts
        chunk_size = len(new_signal)
        new_signal += self._generate_muscle_artifact(chunk_size)
        new_signal += self._generate_random_movement_artifact(chunk_size)
        new_signal += self._generate_sixty_hz_artifact(new_time)
        
        if len(self._signal_transferred_data) == 0:
            self._signal_transferred_data = new_signal
            self._time_transferred_data = new_time
        else:
            self._signal_transferred_data = np.append(self._signal_transferred_data, new_signal)
            self._time_transferred_data = np.append(self._time_transferred_data, new_time)

        self._current_transfer_index += self._generation_thread._buffer_size
        self.simulation_chunk_ready.emit()

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
