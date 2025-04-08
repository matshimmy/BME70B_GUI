import numpy as np
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time

class DataGenerationThread(QThread):
    data_ready = pyqtSignal(float)  # Signal for sending data to device
    buffer_ready = pyqtSignal(np.ndarray, np.ndarray)  # Signal for updating visualization with time and signal data
    
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
        
        # Artifact parameters
        self._muscle_artifact = False
        self._random_movement_artifact = False
        self._sixty_hz_artifact = False
        self._muscle_amplitude = 0.2
        self._random_movement_amplitude = 0.1
        self._sixty_hz_amplitude = 0.15
        self._current_movement = 0.0
        self._movement_duration = 0
        self._movement_counter = 0
        
        # Buffer for visualization
        self._buffer_time = np.array([])
        self._buffer_signal = np.array([])
        
        # Add value and time_point as instance variables
        self._current_value = 0.0
        self._current_time_point = 0.0

    def reset(self):
        """Reset all buffers and counters in the thread"""
        self._current_index = 0
        self._buffer_time = np.array([])
        self._buffer_signal = np.array([])
        self._current_movement = 0.0
        self._movement_duration = 0
        self._movement_counter = 0
        self._last_send_time = 0
        self._last_buffer_time = 0
        self._paused = True
        # Reset the current value and time point too
        self._current_value = 0.0
        self._current_time_point = 0.0
        # Reset template cycle tracking
        self._current_cycle = 0
        self._cycles_completed = 0

    def set_data(self, time_data, signal_data, template_mode=False, template_data=None):
        self.reset()  # Reset buffers when new data is set
        self._time_data = time_data
        self._signal_data = signal_data
        self._template_mode = template_mode
        self._template_data = template_data
        self._current_index = 0
        self._last_send_time = time.time()
        if template_mode:
            self._buffer_size = len(template_data)
        else:
            self._buffer_size = self._transmission_rate

    def set_transmission_rate(self, rate):
        self._transmission_rate = rate
        self._buffer_size = rate

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def set_artifacts(self, muscle: bool, random_movement: bool, sixty_hz: bool):
        """Set which artifacts to include in the simulation"""
        self._muscle_artifact = muscle
        self._random_movement_artifact = random_movement
        self._sixty_hz_artifact = sixty_hz

    def _generate_muscle_artifact(self) -> float:
        if not self._muscle_artifact:
            return 0.0
        
        # Generate single point of EMG-like noise
        noise = np.random.normal(0, 1)
        envelope = abs(np.random.normal(0, 1))
        return noise * envelope * self._muscle_amplitude

    def _generate_random_movement_artifact(self) -> float:
        if not self._random_movement_artifact:
            return 0.0
        
        # If no current movement and 10% chance, start new movement
        if self._movement_duration == 0 and np.random.random() < 0.1:
            self._movement_duration = int(self._transmission_rate * 0.5)  # ~0.5 second movement
            self._current_movement = np.random.normal(0, self._random_movement_amplitude)
            self._movement_counter = 0
        
        if self._movement_duration > 0:
            # Create smooth transition using half a sine wave
            movement = self._current_movement * np.sin(np.pi * self._movement_counter / self._movement_duration)
            self._movement_counter += 1
            if self._movement_counter >= self._movement_duration:
                self._movement_duration = 0
            return movement
        
        return 0.0

    def _generate_sixty_hz_artifact(self, time_point: float) -> float:
        if not self._sixty_hz_artifact:
            return 0.0
        return self._sixty_hz_amplitude * np.sin(2 * np.pi * 60 * time_point)

    def run(self):
        self._running = True
        
        # Wait for model's simulation_running to be True before starting the loop
        while self._running and not self._model.simulation_running:
            time.sleep(0.01)  # Small sleep while waiting
            
        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue

            if self._template_mode:
                # Calculate correct time point with cycle tracking
                cycle_duration = self._time_data[-1] - self._time_data[0]
                template_index = self._current_index % len(self._signal_data)
                
                # If we've completed a full cycle
                if template_index == 0 and self._current_index > 0:
                    self._cycles_completed += 1
                
                # Get value from the template at the current position
                self._current_value = self._signal_data[template_index]
                
                # Calculate time with proper cycle offset
                base_time_point = self._time_data[template_index]
                cycle_offset = self._cycles_completed * cycle_duration
                self._current_time_point = base_time_point + cycle_offset
            else:
                if self._current_index >= len(self._signal_data):
                    self._running = False
                    break
                self._current_value = self._signal_data[self._current_index]
                self._current_time_point = self._time_data[self._current_index]

            # Add artifacts to the value
            self._current_value += self._generate_muscle_artifact()
            self._current_value += self._generate_random_movement_artifact()
            self._current_value += self._generate_sixty_hz_artifact(self._current_time_point)

            # Store in buffer
            self._buffer_time = np.append(self._buffer_time, self._current_time_point)
            self._buffer_signal = np.append(self._buffer_signal, self._current_value)

            # Send data point directly to device if controller is available
            if self._device_controller:
                self._device_controller.send_simulation_data(self._current_value)
            
            # Update visualization buffer when full
            if len(self._buffer_signal) >= self._buffer_size:
                self.buffer_ready.emit(self._buffer_time, self._buffer_signal)
                self._buffer_time = np.array([])
                self._buffer_signal = np.array([])

            self._current_index += 1
            
            # Sleep for exactly the interval needed for the desired transmission rate
            time.sleep(1.0 / self._transmission_rate)

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
        self._generation_thread.reset()  # Reset thread buffers
        self._generation_thread.stop()
        self._generation_thread.wait()
        self._template_mode = False
        self._template_data = None

    def set_transmission_rate(self, rate):
        self._transmission_rate = rate
        self._buffer_size = rate
        self._generation_thread.set_transmission_rate(rate)

    def set_device_controller(self, controller):
        self._generation_thread._device_controller = controller

    def set_artifacts(self, muscle: bool, random_movement: bool, sixty_hz: bool):
        """Set which artifacts to include in the simulation"""
        self._muscle_artifact = muscle
        self._random_movement_artifact = random_movement
        self._sixty_hz_artifact = sixty_hz
        # Pass artifact settings to generation thread
        self._generation_thread.set_artifacts(muscle, random_movement, sixty_hz)

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

    def _handle_buffer_ready(self, time_data: np.ndarray, signal_data: np.ndarray):
        """Handle buffer ready for visualization"""
        if len(self._signal_transferred_data) == 0:
            self._signal_transferred_data = signal_data
            self._time_transferred_data = time_data
        else:
            self._signal_transferred_data = np.append(self._signal_transferred_data, signal_data)
            self._time_transferred_data = np.append(self._time_transferred_data, time_data)

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
