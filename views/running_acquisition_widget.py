from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem,
    QSizePolicy, QLabel, QFileDialog, QSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine
from models.model import Model


class RunningAcquisitionWidget(QWidget):
    def __init__(self, model: Model, state_machine: StateMachine, device_controller: DeviceController):
        super().__init__()
        self.device_controller = device_controller
        self.state_machine = state_machine
        self.model = model

        self.disconnecting = False

        self._build_ui()
        self._connect_signals()
        self.reset_ui()

    # -------------------------------------------------------------------------
    #  Build UI
    # -------------------------------------------------------------------------
    def _build_ui(self):
        """Build and organize all UI components."""
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        top_row_layout = self._build_top_row()
        main_layout.addLayout(top_row_layout)

        # Template Plot
        self._build_template_plot(main_layout)

        # Status label
        self.acquisition_status_label = QLabel("Acquisition In Progress...")
        main_layout.addWidget(self.acquisition_status_label)

        # Main data plot
        self._build_main_plot(main_layout)

        # Time window row
        self._build_time_window_selector(main_layout)

        # Pause/Resume button
        self._build_acquisition_button(main_layout)

        # Disconnect / Save Data row
        self._build_bottom_controls(main_layout)

        self.setLayout(main_layout)

    def _build_top_row(self) -> QHBoxLayout:
        """Creates the top row with Back button and 'Template' label."""
        layout = QHBoxLayout()

        # Back button
        self.back_button = QPushButton(" ← ")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.back)
        layout.addWidget(self.back_button)

        # Spacer for centering
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.template_label = QLabel("Template")
        layout.addWidget(self.template_label)

        # Another expanding spacer
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        return layout

    def _build_template_plot(self, parent_layout: QVBoxLayout):
        """Add the template plot widget."""
        self.template_plot_widget = pg.PlotWidget()
        self.template_plot_widget.setBackground('w')
        self.template_plot_widget.setLabel('left', 'Amplitude', units='A')
        self.template_plot_widget.setLabel('bottom', 'Time', units='s')
        # Create an empty curve for the template
        self.template_curve = self.template_plot_widget.plot([], [], pen='r')

        # Add widget to parent layout
        parent_layout.addWidget(self.template_plot_widget, stretch=1)

    def _build_main_plot(self, parent_layout: QVBoxLayout):
        """Add the main acquisition plot widget."""
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Amplitude', units='A')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        # Create an empty curve for the main data
        self.curve = self.plot_widget.plot([], [], pen='b')
        parent_layout.addWidget(self.plot_widget, stretch=1)

    def _build_time_window_selector(self, parent_layout: QVBoxLayout):
        """Add the spinbox and line edit to control/view the main plot range."""
        x_range_layout = QHBoxLayout()
        self.x_range_label = QLabel("Time window (s):")
        x_range_layout.addWidget(self.x_range_label)

        self.x_range_spinbox = QSpinBox()
        self.x_range_spinbox.setRange(5, 60)
        self.x_range_spinbox.valueChanged.connect(self.update_graph)
        x_range_layout.addWidget(self.x_range_spinbox)

        # Spacer for alignment
        x_range_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.hey_text_box = QLineEdit()
        self.hey_text_box.setReadOnly(True)
        x_range_layout.addWidget(self.hey_text_box)

        parent_layout.addLayout(x_range_layout)

    def _build_acquisition_button(self, parent_layout: QVBoxLayout):
        """Add the Pause/Resume acquisition button."""
        self.acquisition_button = QPushButton("Pause Acquisition")
        self.acquisition_button.setObjectName("amberButton")
        self.acquisition_button.clicked.connect(self.toggle_acquisition)
        parent_layout.addWidget(self.acquisition_button)

    def _build_bottom_controls(self, parent_layout: QVBoxLayout):
        """Add the bottom row with 'Disconnect' and 'Save Data' buttons."""
        bottom_layout = QHBoxLayout()
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("redButton")
        self.disconnect_button.clicked.connect(self.disconnect)
        bottom_layout.addWidget(self.disconnect_button)

        # Spacer to push the Save Data button to the right
        bottom_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.save_data_button = QPushButton("Save Data")
        self.save_data_button.setObjectName("amberButton")
        self.save_data_button.clicked.connect(self.save_data)
        bottom_layout.addWidget(self.save_data_button)

        parent_layout.addLayout(bottom_layout)

    # -------------------------------------------------------------------------
    #  Signals & Reset
    # -------------------------------------------------------------------------
    def _connect_signals(self):
        """Connect PyQt signals/slots."""
        self.state_machine.acquisition_chunk_received.connect(self.update_graph)
        self.device_controller.acquisitionThread.finished.connect(self._disconnect_acquisition_stopped)

    def reset_ui(self):
        """Reset the UI to its initial state."""
        self.disconnecting = False
        self.back_button.setEnabled(False)

        # Default time window
        self.x_range_spinbox.setValue(5)

        # Clear the main plot
        self.curve.setData([], [])
        self.plot_widget.setXRange(0, 5)

        # Acquisition status
        self.acquisition_status_label.setText("Acquisition In Progress...")

        # Acquisition button
        self.acquisition_button.setEnabled(True)
        self.acquisition_button.setText("Pause Acquisition")
        self.acquisition_button.setObjectName("amberButton")
        self._update_button_style(self.acquisition_button)

        # Disconnect button
        self.disconnect_button.setEnabled(True)
        self.disconnect_button.setText("Disconnect")

        # Save data button
        self.save_data_button.setEnabled(True)
        self.save_data_button.setObjectName("amberButton")
        self._update_button_style(self.save_data_button)

        # Template plot
        self.template_curve.setData([], [])

    def _update_button_style(self, button: QPushButton):
        """Force a style refresh for a button that changes objectName."""
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    # -------------------------------------------------------------------------
    #  Slots: Save, Pause/Resume, Update Graph, Disconnect, etc.
    # -------------------------------------------------------------------------
    def save_data(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "*.csv")
        if filename:
            self.state_machine.model.signal_data.export_csv(filename)

    def toggle_acquisition(self):
        self.state_machine.toggle_acquisition()
        if self.model.acquisition_running:
            self.acquisition_button.setText("Pause Acquisition")
            self.acquisition_status_label.setText("Acquisition In Progress...")
            self.acquisition_button.setObjectName("amberButton")
            self.back_button.setEnabled(False)
        else:
            self.acquisition_button.setText("Resume Acquisition")
            self.acquisition_status_label.setText("Acquisition Paused")
            self.acquisition_button.setObjectName("greenButton")
            self.back_button.setEnabled(True)
        self._update_button_style(self.acquisition_button)

    def update_graph(self):
        """Main slot that updates both the main plot and the template plot."""
        data = self.state_machine.model.signal_data.data
        sample_rate = self.state_machine.model.signal_data.sample_rate

        # 1) Figure out which portion of the data is visible
        t_visible, data_visible = self._prepare_visible_data(data, sample_rate)

        # 2) Update the main (acquisition) plot
        self._update_main_plot(t_visible, data_visible)

        # 3) Update the template plot
        template = self.model.template_processor.get_template()
        self._update_template_plot(template)

    # -------------------------------------------------------------------------
    #  Helper methods for update_graph
    # -------------------------------------------------------------------------
    def _prepare_visible_data(self, data: np.ndarray, sample_rate: float):
        """
        From the full data array, compute which portion is 'visible' based on
        the time window spinbox.
        """
        total_points = len(data)
        time_window = self.x_range_spinbox.value()
        visible_points = int(time_window * sample_rate)

        if total_points > visible_points:
            data_visible = data[-visible_points:]
            t_start = (total_points - visible_points) / sample_rate
            t_end = total_points / sample_rate
            t_visible = np.linspace(t_start, t_end, visible_points, endpoint=False)
        else:
            data_visible = data
            t_visible = np.linspace(0, total_points / sample_rate, total_points, endpoint=False)

        return t_visible, data_visible

    def _update_main_plot(self, t_visible: np.ndarray, data_visible: np.ndarray):
        """Update the main plot curve and autoscale if necessary."""
        self.curve.setData(t_visible, data_visible)

        # X-axis range
        time_window = self.x_range_spinbox.value()
        current_time = t_visible[-1] if len(t_visible) else 0
        if current_time < time_window:
            self.plot_widget.setXRange(0, time_window)
        else:
            self.plot_widget.setXRange(current_time - time_window, current_time)

        # Y-axis autoscale only if acquisition is running
        if self.model.acquisition_running and len(data_visible) > 0:
            y_min, y_max = self._compute_y_range(data_visible)
            self.plot_widget.setYRange(y_min, y_max)

        # Update the "hey text box" with the current Y range
        y_range = self.plot_widget.viewRange()[1]  # [1] => Y range
        self.hey_text_box.setText(f"{y_range[0]:.2f} to {y_range[1]:.2f}")

    def _update_template_plot(self, template: np.ndarray):
        """Update the template plot (curve + auto-scaling)."""
        if len(template) > 0:
            # Build time axis for template
            sample_rate = self.model.template_processor.sample_rate
            x_axis = np.linspace(0, len(template)/sample_rate, len(template))

            self.template_curve.setData(x_axis, template)

            # Auto-scale X-range
            x_end = x_axis[-1] if len(x_axis) > 0 else 1
            if x_end <= 0:
                x_end = 1
            self.template_plot_widget.setXRange(0, x_end)

            # Auto-scale Y-range
            y_min, y_max = self._compute_y_range(template)
            self.template_plot_widget.setYRange(y_min, y_max)

        else:
            # If empty, clear and reset
            self.template_curve.setData([], [])
            self.template_plot_widget.setXRange(0, 1)
            self.template_plot_widget.setYRange(-1, 1)

    def _compute_y_range(self, data: np.ndarray, margin_ratio: float = 0.05):
        """
        Compute a y-axis min & max with optional margin. If the data is flat,
        produce a small band around that flat value.
        """
        min_val = np.min(data)
        max_val = np.max(data)

        if min_val == max_val:
            # If all points are the same, pick ±1
            return (min_val - 1, max_val + 1)
        else:
            margin = margin_ratio * (max_val - min_val)
            return (min_val - margin, max_val + margin)

    # -------------------------------------------------------------------------
    #  Disconnect Logic
    # -------------------------------------------------------------------------
    def disconnect(self):
        self.disconnecting = True
        self.acquisition_button.setObjectName("greyButton")
        self._update_button_style(self.acquisition_button)
        self.acquisition_button.setEnabled(False)
        self.acquisition_status_label.setText("Stopping Acquisition...")

        self.disconnect_button.setEnabled(False)
        self.disconnect_button.setText("Disconnecting...")

        self.save_data_button.setEnabled(False)
        self.save_data_button.setObjectName("greyButton")
        self._update_button_style(self.save_data_button)
        self.back_button.setEnabled(False)

        self.device_controller.stop_acquisition()

    def _disconnect_acquisition_stopped(self):
        if self.disconnecting:
            self.device_controller.start_graceful_disconnect()
            self.reset_ui()

    # -------------------------------------------------------------------------
    #  Navigation
    # -------------------------------------------------------------------------
    def back(self):
        self.device_controller.stop_acquisition()
        self.state_machine.transition_to_acquisition_options()
        self.reset_ui()
