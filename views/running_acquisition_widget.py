from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QFileDialog, QSpinBox
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
        
        self._build_ui()
        self._connect_signals()
        self.reset_ui()  # Set dynamic state to initial values

    def _build_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Top row: Back button and label
        back_button_layout = QHBoxLayout()
        self.back_button = QPushButton(" ← ")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.back)
        back_button_layout.addWidget(self.back_button)

        # Add an expanding spacer to push the button to the left
        back_button_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Title label
        self.label = QLabel("Acquisition In Progress...")
        back_button_layout.addWidget(self.label)
        # Another expanding spacer so label is centered
        back_button_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(back_button_layout)
        
        # PyQtGraph Plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Amplitude', units='A')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.curve = self.plot_widget.plot([], [], pen='b')
        main_layout.addWidget(self.plot_widget, stretch=1)

        # Time window spinbox row
        x_range_layout = QHBoxLayout()
        self.x_range_label = QLabel("Time window (s):")
        x_range_layout.addWidget(self.x_range_label)

        self.x_range_spinbox = QSpinBox()
        self.x_range_spinbox.setRange(5, 60)
        self.x_range_spinbox.valueChanged.connect(self.update_graph)
        x_range_layout.addWidget(self.x_range_spinbox)

        x_range_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(x_range_layout)

        # Acquisition control (pause/resume) button
        self.acquisition_button = QPushButton("Pause Acquisition")
        self.acquisition_button.setObjectName("amberButton")
        self.acquisition_button.clicked.connect(self.toggle_acquisition)
        main_layout.addWidget(self.acquisition_button)
        
        # Bottom layout for Disconnect and Save Data buttons
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
        
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)
        
    def _connect_signals(self):
        self.state_machine.acquisition_chunk_received.connect(self.update_graph)
        self.device_controller.acquisitionThread.finished.connect(self._disconnect_acquisition_stopped)
        
    def reset_ui(self):
        self.disconnecting = False
        self.x_range_window = 5
        self.x_range_spinbox.setValue(self.x_range_window)
        self.back_button.setEnabled(False)

        self.curve.setData([], [])
        self.plot_widget.setXRange(0, self.x_range_window)

        self.label.setText("Acquisition In Progress...")

        self.acquisition_button.setEnabled(True)
        self.acquisition_button.setText("Pause Acquisition")
        self.acquisition_button.setObjectName("amberButton")
        self._update_button_style(self.acquisition_button)

        self.disconnect_button.setEnabled(True)
        self.disconnect_button.setText("Disconnect")

        self.save_data_button.setEnabled(True)
        self.save_data_button.setObjectName("amberButton")
        self._update_button_style(self.save_data_button)
        
    def _update_button_style(self, button: QPushButton):
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()
        
    def save_data(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "*.csv")
        if filename:
            self.state_machine.model.signal_data.export_csv(filename)
    
    def toggle_acquisition(self):
        self.state_machine.toggle_acquisition()
        if self.model.acquisition_running:
            self.acquisition_button.setText("Pause Acquisition")
            self.label.setText("Acquisition In Progress...")
            self.acquisition_button.setObjectName("amberButton")
            self.back_button.setEnabled(False)
        else:
            self.acquisition_button.setText("Resume Acquisition")
            self.label.setText("Acquisition Paused")
            self.acquisition_button.setObjectName("greenButton")
            self.back_button.setEnabled(True)
        self._update_button_style(self.acquisition_button)
    
    def update_graph(self):
        data = self.state_machine.model.signal_data.data
        sample_rate = self.state_machine.model.signal_data.sample_rate
        total_points = len(data)

        time_window = self.x_range_spinbox.value()
        visible_points = int(time_window * sample_rate)

        if total_points > visible_points:
            data_visible = data[-visible_points:]
            t_visible = np.linspace(
                (total_points - visible_points) / sample_rate,
                total_points / sample_rate,
                visible_points,
                endpoint=False
            )
        else:
            data_visible = data
            t_visible = np.linspace(0, total_points / sample_rate, total_points, endpoint=False)

        self.curve.setData(t_visible, data_visible)
        current_time = total_points / sample_rate
        if current_time < time_window:
            self.plot_widget.setXRange(0, time_window)
        else:
            self.plot_widget.setXRange(current_time - time_window, current_time)
    
    def disconnect(self):
        self.disconnecting = True
        self.acquisition_button.setObjectName("greyButton")
        self._update_button_style(self.acquisition_button)
        self.acquisition_button.setEnabled(False)
        self.label.setText("Stopping Acquisition...")

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

    def back(self):
        self.device_controller.stop_acquisition()
        self.state_machine.transition_to_acquisition_options()
        self.reset_ui()
