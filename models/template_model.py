import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal

class TemplateModel(QObject):
    duration_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._duration = 0.7  # Default duration in seconds
        self._transmission_rate = 200  # Default 200 Hz
        self._template_data = None
        self._x_axis = None
        self._control_points = []
        self._y_range = (-1.5, 1.5)
        self._update_x_axis()
        self._initialize_template()

    def _update_x_axis(self):
        num_points = self.get_num_points()
        self._x_axis = np.linspace(0, self._duration, num_points)
        
        if self._template_data is not None:
            self._interpolate_template()

    def _initialize_template(self):
        num_points = self.get_num_points()
        self._template_data = np.zeros(num_points)
        
        # Initialize with two control points at the ends (in seconds)
        self._control_points = [
            (0, 0),          # Start point
            (self._duration, 0)  # End point
        ]
        self._update_template_from_control_points()

    def _interpolate_template(self):
        if self._template_data is not None:
            old_x = np.linspace(0, self._duration, len(self._template_data))
            self._template_data = np.interp(self._x_axis, old_x, self._template_data)

    def _update_template_from_control_points(self):
        if len(self._control_points) >= 2:
            x = np.array([p[0] for p in self._control_points])
            y = np.array([p[1] for p in self._control_points])
            
            # Interpolate control points to x-axis
            smooth_y = np.interp(self._x_axis, x, y)
            self._template_data = smooth_y

    def add_control_point(self, x: float, y: float):
        x = np.clip(x, 0, self._duration)
        y = np.clip(y, self._y_range[0], self._y_range[1])
        
        self._control_points.append((x, y))
        self._sort_control_points()
        self._update_template_from_control_points()

    def update_control_point(self, index: int, x: float, y: float):
        if 0 <= index < len(self._control_points):
            x = np.clip(x, 0, self._duration)
            y = np.clip(y, self._y_range[0], self._y_range[1])
            
            self._control_points[index] = (x, y)
            self._sort_control_points()
            self._update_template_from_control_points()

    def remove_control_point(self, index: int):
        if 0 < index < len(self._control_points) - 1:
            self._control_points.pop(index)
            self._update_template_from_control_points()

    def _sort_control_points(self):
        self._control_points.sort(key=lambda p: p[0])

    # Getters and setters
    def get_num_points(self):
        return int(self._duration * self._transmission_rate)

    def get_x_axis(self):
        return self._x_axis

    def get_template_data(self):
        return self._template_data

    def get_control_points(self):
        return self._control_points.copy()

    def set_duration_ms(self, duration_ms: float):
        self._duration = round(duration_ms / 1000.0, 3)  # Convert to seconds with 3 decimal places
        self._update_x_axis()
        self._initialize_template()
        self.duration_changed.emit(duration_ms)

    def set_transmission_rate(self, rate: float):
        self._transmission_rate = rate
        self._update_x_axis()

    def update_template_point(self, index: int, value: float):
        if 0 <= index < len(self._template_data):
            self._template_data[index] = np.clip(value, self._y_range[0], self._y_range[1])
