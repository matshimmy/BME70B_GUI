from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem,
    QSizePolicy, QLabel, QSpinBox
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine
from models.model import Model


class RunningSimulationWidget(QWidget):
    def __init__(self, model: Model, state_machine: StateMachine, device_controller: DeviceController):
        super().__init__()
        self.device_controller = device_controller
        self.state_machine = state_machine
        self.model = model

        self.disconnecting = False

        self._build_ui()
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

        self._build_main_plot(main_layout)

        self._build_time_window_selector(main_layout)

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

    def _build_main_plot(self, parent_layout: QVBoxLayout):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Amplitude', units='A')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.curve = self.plot_widget.plot([], [], pen='b')
        parent_layout.addWidget(self.plot_widget, stretch=1)

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

        # Clear the main plot
        self.curve.setData([], [])
        self.plot_widget.setXRange(0, 5)

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
        else:
            self.simulation_button.setText("Resume Simulation")
            self.simulation_status_label.setText("Signal")
            self.simulation_button.setObjectName("greenButton")
            self.back_button.setEnabled(True)

        self._update_button_style(self.simulation_button)

    def update_graph(self):
        pass


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
