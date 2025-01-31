from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QFileDialog
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np

from controllers.device_controller import DeviceController
from controllers.state_machine import StateMachine

class RunningAcquisitionWidget(QWidget):
    def __init__(self, state_machine: StateMachine, device_controller: DeviceController):
        super().__init__()
        self.device_controller = device_controller
        self.state_machine = state_machine
        self.acquisition_paused = False
        
        # ---------------------------
        # Data Arrays for Plotting
        # ---------------------------
        self.x_data = np.array([]) 
        self.y_data = np.array([])
        self.sample_rate = 100.0
        self.current_time = 0.0

        device_controller.acquisitionService.chunk_received.connect(self.on_chunk_received)

        # ---------------------------
        # Main Layout
        # ---------------------------
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Spacer at the top
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Title label
        self.label = QLabel("Acquisition In Progress...")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        # ---------------------------
        # PyQtGraph Plot
        # ---------------------------
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')  # white background
        self.plot_widget.setLabel('left', 'Amplitude', units='mA')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.curve = self.plot_widget.plot([], [], pen='b')
        main_layout.addWidget(self.plot_widget)

        # Acquisition control (pause/resume)
        self.acquisition_button = QPushButton("Pause Acquisition")
        self.acquisition_button.setObjectName("amberButton")
        self.acquisition_button.clicked.connect(self.toggle_acquisition)
        main_layout.addWidget(self.acquisition_button)

        # Spacer below the buttons
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # ---------------------------
        # Bottom Layout
        # ---------------------------
        bottom_layout = QHBoxLayout()

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("redButton")
        self.disconnect_button.clicked.connect(self.device_controller.start_graceful_disconnect)
        bottom_layout.addWidget(self.disconnect_button)

        # Spacer to push the Save button to the right
        bottom_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.save_data_button = QPushButton("Save Data")
        self.save_data_button.setObjectName("amberButton")
        self.save_data_button.clicked.connect(self.save_data)
        bottom_layout.addWidget(self.save_data_button)

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    # ---------------------------
    # Save Data
    # ---------------------------
    def save_data(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "*.csv")
        if filename:
            self.state_machine.model.signal_data.export_csv(filename)

    # ---------------------------
    # Pause / Resume Acquisition
    # ---------------------------
    def toggle_acquisition(self):
        if self.acquisition_paused:
            self.acquisition_button.setText("Pause Acquisition")
            self.label.setText("Acquisition In Progress...")
            self.acquisition_button.setObjectName("amberButton")
            # If you want to resume data from the service, call e.g. device_controller.resume_acquisition()
        else:
            self.acquisition_button.setText("Resume Acquisition")
            self.label.setText("Acquisition Paused")
            self.acquisition_button.setObjectName("greenButton")
            # If you want to pause data from the service, call e.g. device_controller.pause_acquisition()

        self.acquisition_button.style().unpolish(self.acquisition_button)
        self.acquisition_button.style().polish(self.acquisition_button)
        self.acquisition_button.update()

        self.acquisition_paused = not self.acquisition_paused

    # ---------------------------
    # Plot Update Slot
    # ---------------------------
    def on_chunk_received(self, chunk):
        """
        Called whenever a new data chunk arrives from the device/controller.
        'chunk' could be a NumPy array or list of samples.
        We'll append to our x_data / y_data and re-plot.
        """
        if self.acquisition_paused:
            return  # Ignore new data if paused

        chunk_len = len(chunk)
        # Create a time array for this chunk, starting at self.current_time
        t = np.linspace(self.current_time,
                        self.current_time + (chunk_len/self.sample_rate),
                        chunk_len, endpoint=False)
        self.current_time += (chunk_len/self.sample_rate)

        # Append to existing data
        self.x_data = np.concatenate([self.x_data, t])
        self.y_data = np.concatenate([self.y_data, chunk])

        # Update the plot
        self.curve.setData(self.x_data, self.y_data)

        if self.current_time < 5:
            # Before we reach 5s of data, just show the range [0, 5]
            self.plot_widget.setXRange(0, 5)
        else:
            # Once we have more than 5s of data, scroll the window
            self.plot_widget.setXRange(self.current_time - 5, self.current_time)