from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem,
    QSizePolicy, QLabel, QSpinBox
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine
from enums.simulation_type import SimulationType
from views.simulation.template_editor import TemplateEditor

class RunningSimulationWidget(QWidget):
    def __init__(self, state_machine: StateMachine, device_controller: DeviceController):
        super().__init__()
        self.device_controller = device_controller
        self.state_machine = state_machine
        self.model = state_machine.model
        self.signal_simulation = state_machine.model.signal_simulation
        self.template_model = state_machine.model.template_model

        self.disconnecting = False

        # Connect to simulation model's signal
        self.signal_simulation.simulation_chunk_ready.connect(self.update_graph)

        self._build_ui()
        self.reset_ui()

        # Listen for changes to the model
        self.model.model_changed.connect(self.on_model_changed)

    # -------------------------------------------------------------------------
    #  Build UI
    # -------------------------------------------------------------------------
    def _build_ui(self):
        """Build and organize all UI components."""
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        top_row_layout = self._build_top_row()
        main_layout.addLayout(top_row_layout)

        self._build_signal_plot(main_layout)

        self._build_time_window_selector(main_layout)

        self._build_template(main_layout)
        self._build_bottom_controls(main_layout)

        self.setLayout(main_layout)

    def _build_top_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        # Back button
        self.back_button = QPushButton(" ← ")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.back)
        layout.addWidget(self.back_button)

        # Spacer for centering
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.simulation_status_label = QLabel("Signal")
        layout.addWidget(self.simulation_status_label)

        # Another expanding spacer
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        return layout

    def _build_signal_plot(self, parent_layout: QVBoxLayout):
        self.signal_plot = pg.PlotWidget()
        self.signal_plot.setBackground('w')
        self.signal_plot.setLabel('left', 'Amplitude', units='A')
        self.signal_plot.setLabel('bottom', 'Time', units='s')
        self.curve = self.signal_plot.plot(pen='b')

        parent_layout.addWidget(self.signal_plot, stretch=1)

    def _build_time_window_selector(self, parent_layout: QVBoxLayout):
        x_range_layout = QHBoxLayout()
        self.x_range_label = QLabel("Time window (s):")
        x_range_layout.addWidget(self.x_range_label)

        self.x_range_spinbox = QSpinBox()
        self.x_range_spinbox.setRange(5, 60)
        self.x_range_spinbox.valueChanged.connect(self.update_graph)
        x_range_layout.addWidget(self.x_range_spinbox)

        # Spacer for alignment
        x_range_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        parent_layout.addLayout(x_range_layout)

    def _build_template(self, parent_layout: QVBoxLayout):
        self.template_editor = TemplateEditor(self.model.template_model)
        parent_layout.addWidget(self.template_editor, stretch=1)

    def _build_bottom_controls(self, parent_layout: QVBoxLayout):
        bottom_layout = QHBoxLayout()
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("redButton")
        self.disconnect_button.clicked.connect(self.disconnect)
        bottom_layout.addWidget(self.disconnect_button)

        bottom_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.simulation_button = QPushButton("Start Simulation")
        self.simulation_button.setObjectName("greenButton")
        self.simulation_button.clicked.connect(self.toggle_simulation)
        bottom_layout.addWidget(self.simulation_button)

        parent_layout.addLayout(bottom_layout)

    # -------------------------------------------------------------------------
    #  Reset
    # -------------------------------------------------------------------------
    def reset_ui(self):
        """Reset the UI to its initial state."""
        self.disconnecting = False
        self.back_button.setEnabled(True)

        # Default time window
        self.x_range_spinbox.setValue(5)
        self.update_graph()

        # Clear the main plot
        self.curve.setData([], [])

        # Simulation status
        self.simulation_status_label.setText("Signal")

        # Simulation button
        self.simulation_button.setEnabled(True)
        self.simulation_button.setText("Start Simulation")
        self.simulation_button.setObjectName("greenButton")
        self._update_button_style(self.simulation_button)

        # Disconnect button
        self.disconnect_button.setEnabled(True)
        self.disconnect_button.setText("Disconnect")

    def _update_button_style(self, button: QPushButton):
        """Force a style refresh for a button that changes objectName."""
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    # -------------------------------------------------------------------------
    #  Slots: Pause/Resume, Update Graph, Disconnect, etc.
    # -------------------------------------------------------------------------
    def toggle_simulation(self):
        self.state_machine.toggle_simulation()
        if self.model.simulation_running:
            self.simulation_button.setText("Pause Simulation")
            self.simulation_status_label.setText("Transferring...")
            self.simulation_button.setObjectName("amberButton")
            self.back_button.setEnabled(False)
            if self.model.simulation_type == SimulationType.TEMPLATE:
                self.template_editor.enable_editing(False)
                template_data = self.template_model.get_template_data()
                template_duration = self.template_model._duration
                self.signal_simulation.set_template_data(template_data, template_duration)
                
            self.signal_simulation.start_simulation()
        else:
            self.simulation_button.setText("Resume Simulation")
            self.simulation_status_label.setText("Signal")
            self.simulation_button.setObjectName("greenButton")
            self.back_button.setEnabled(True)
            if self.model.simulation_type == SimulationType.TEMPLATE:
                self.template_editor.enable_editing(True)
            self.signal_simulation.pause_simulation()

        self._update_button_style(self.simulation_button)

    def update_graph(self):
        # Get the transferred data from signal simulation
        time_data = self.signal_simulation._time_transferred_data
        signal_data = self.signal_simulation._signal_transferred_data
        # Update the plot with all transferred data
        self.curve.setData(time_data, signal_data)

        # Update x-axis range
        time_window = self.x_range_spinbox.value()
        current_time = time_data[-1] if len(time_data) > 0 else 0
        if current_time < time_window:
            self.signal_plot.setXRange(0, time_window)
        else:
            self.signal_plot.setXRange(current_time - time_window, current_time)

        # Auto-scale y-axis
        visible_start = max(0, len(signal_data) - int(time_window * self.signal_simulation._transmission_rate))
        visible_data = signal_data[visible_start:]
        if len(visible_data) > 0:
            y_min = np.min(visible_data)
            y_max = np.max(visible_data)
            margin = 0.05 * (y_max - y_min)
            self.signal_plot.setYRange(y_min - margin, y_max + margin)

    # -------------------------------------------------------------------------
    #  Disconnect Logic
    # -------------------------------------------------------------------------
    def disconnect(self):
        self.disconnecting = True
        self.simulation_button.setObjectName("greyButton")
        self._update_button_style(self.simulation_button)
        self.simulation_button.setEnabled(False)
        self.simulation_status_label.setText("Stopping Simulation...")

        self.disconnect_button.setEnabled(False)
        self.disconnect_button.setText("Disconnecting...")

        self.back_button.setEnabled(False)

        self.device_controller.stop_simulation()
        self.device_controller.start_graceful_disconnect()
        self.reset_ui()

    # -------------------------------------------------------------------------
    #  Navigation
    # -------------------------------------------------------------------------
    def back(self):
        self.device_controller.stop_simulation()
        self.state_machine.transition_to_simulation_options()
        self.reset_ui()

    # -------------------------------------------------------------------------
    #  Reacting to Model Changes
    # -------------------------------------------------------------------------
    def on_model_changed(self):
        if self.model.simulation_type == SimulationType.TEMPLATE:
            self.template_editor.show()
        else:
            self.template_editor.hide()
