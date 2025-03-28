from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem,
    QSizePolicy, QLabel, QFileDialog, QSpinBox, QDoubleSpinBox,
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np

from views.common.base_widget import BaseWidget


class RunningAcquisitionWidget(BaseWidget):
    def _setup_ui(self):

        self.disconnecting = False

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        top_row_layout = self._setup_top_row()
        main_layout.addLayout(top_row_layout)

        self._setup_main_plot(main_layout)
        self._setup_time_window_selector(main_layout)
        self._setup_template_plot(main_layout)
        self._setup_template_controls(main_layout)
        self._setup_bottom_controls(main_layout)
        self.setLayout(main_layout)

        self._connect_signals()
        self.reset_ui()


    def _setup_top_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        # Back button
        self.back_button = QPushButton(" ← ")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.back)
        layout.addWidget(self.back_button)

        # Spacer for centering
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.acquisition_status_label = QLabel("Acquisition In Progress...")
        layout.addWidget(self.acquisition_status_label)

        # Another expanding spacer
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # --- Radio buttons: CSV vs. WFDB ---
        self.csv_radio = QRadioButton("CSV")
        self.wfdb_radio = QRadioButton("WFDB")

        # Make sure one is checked by default
        self.csv_radio.setChecked(True)

        # Add them to a button group to ensure mutual exclusivity
        self.format_group = QButtonGroup()
        self.format_group.addButton(self.csv_radio)
        self.format_group.addButton(self.wfdb_radio)

        # Add these radio buttons to the layout
        layout.addWidget(self.csv_radio)
        layout.addWidget(self.wfdb_radio)

        return layout

    def _setup_main_plot(self, parent_layout: QVBoxLayout):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Amplitude', units='A')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.curve = self.plot_widget.plot([], [], pen='b')
        parent_layout.addWidget(self.plot_widget, stretch=1)

    def _setup_time_window_selector(self, parent_layout: QVBoxLayout):
        x_range_layout = QHBoxLayout()
        self.x_range_label = QLabel("Time window (s):")
        x_range_layout.addWidget(self.x_range_label)

        self.x_range_spinbox = QSpinBox()
        self.x_range_spinbox.setRange(1, 60)
        self.x_range_spinbox.valueChanged.connect(self.update_graph)
        x_range_layout.addWidget(self.x_range_spinbox)

        # Spacer for alignment
        x_range_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.save_data_button = QPushButton("Save Data")
        self.save_data_button.setObjectName("greyButton")
        self.save_data_button.clicked.connect(self.save_data)
        x_range_layout.addWidget(self.save_data_button)

        parent_layout.addLayout(x_range_layout)

    def _setup_template_plot(self, parent_layout: QVBoxLayout):
        layout = QHBoxLayout()
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.template_label = QLabel("Template")
        layout.addWidget(self.template_label)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        parent_layout.addLayout(layout)

        self.template_plot_widget = pg.PlotWidget()
        self.template_plot_widget.setBackground('w')
        self.template_plot_widget.setLabel('left', 'Amplitude', units='A')
        self.template_plot_widget.setLabel('bottom', 'Time', units='s')
        # Create an empty curve for the template
        self.template_curve = self.template_plot_widget.plot([], [], pen='r')

        # Add widget to parent layout
        parent_layout.addWidget(self.template_plot_widget, stretch=1)

    def _setup_template_controls(self, parent_layout: QVBoxLayout):
        controls_layout = QHBoxLayout()

        # -- look_back_time_s
        self.look_back_label = QLabel("Look Back (s):")
        controls_layout.addWidget(self.look_back_label)

        self.look_back_spinbox = QDoubleSpinBox()
        self.look_back_spinbox.setRange(0.5, 60.0)
        self.look_back_spinbox.setDecimals(2)
        self.look_back_spinbox.valueChanged.connect(self._on_look_back_changed)
        controls_layout.addWidget(self.look_back_spinbox)

        # -- update_interval_s
        self.update_interval_label = QLabel("Update Interval (s):")
        controls_layout.addWidget(self.update_interval_label)

        self.update_interval_spinbox = QDoubleSpinBox()
        self.update_interval_spinbox.setRange(0.1, 10.0)
        self.update_interval_spinbox.setDecimals(2)
        self.update_interval_spinbox.valueChanged.connect(self._on_update_interval_changed)
        controls_layout.addWidget(self.update_interval_spinbox)

        # Spacer to push "Save Template" button to the right
        controls_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # -- Save Template Button
        self.save_template_button = QPushButton("Save Template")
        self.save_template_button.setObjectName("greyButton")
        self.save_template_button.clicked.connect(self.save_template)
        controls_layout.addWidget(self.save_template_button)

        parent_layout.addLayout(controls_layout)

    def _setup_bottom_controls(self, parent_layout: QVBoxLayout):
        """Add the bottom row with 'Disconnect' and 'Save Data' buttons."""
        bottom_layout = QHBoxLayout()
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("redButton")
        self.disconnect_button.clicked.connect(self.disconnect)
        bottom_layout.addWidget(self.disconnect_button)

        # Spacer to push the Save Data button to the right
        bottom_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.acquisition_button = QPushButton("Pause Acquisition")
        self.acquisition_button.setObjectName("amberButton")
        self.acquisition_button.clicked.connect(self.toggle_acquisition)
        bottom_layout.addWidget(self.acquisition_button)

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

        # Save template button
        self.save_template_button.setEnabled(False)
        self.save_template_button.setObjectName("greyButton")
        self._update_button_style(self.save_template_button)

        # Save data button
        self.save_data_button.setEnabled(False)
        self.save_data_button.setObjectName("greyButton")
        self._update_button_style(self.save_data_button)

        # Template plot
        self.template_curve.setData([], [])

        # Reset spinboxes to match the model's initial values
        self.look_back_spinbox.setValue(self.model.template_processor.look_back_time)
        self.update_interval_spinbox.setValue(self.model.template_processor.update_interval_s)

        # Reset radio buttons
        self.csv_radio.setChecked(True)

        # Show/hide all template-related widgets
        self._update_template_visibility()

    def _update_button_style(self, button: QPushButton):
        """Force a style refresh for a button that changes objectName."""
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def _update_template_visibility(self):
        if self.model.get_template:
            self.template_label.show()
            self.template_plot_widget.show()
            self.look_back_label.show()
            self.look_back_spinbox.show()
            self.update_interval_label.show()
            self.update_interval_spinbox.show()
            self.save_template_button.show()
        else:
            self.template_label.hide()
            self.template_plot_widget.hide()
            self.look_back_label.hide()
            self.look_back_spinbox.hide()
            self.update_interval_label.hide()
            self.update_interval_spinbox.hide()
            self.save_template_button.hide()

    # -------------------------------------------------------------------------
    #  Slots: Save, Pause/Resume, Update Graph, Disconnect, etc.
    # -------------------------------------------------------------------------
    def save_data(self):
        signal_data = self.state_machine.model.signal_data

        file_format = self._get_selected_format()
        if file_format == "csv":
            filter_str = "CSV Files (*.csv)"
        else:
            filter_str = "WFDB Files (*.dat)"

        filename, _ = QFileDialog.getSaveFileName(self, "Save Data", "", filter_str)
        if not filename:
            return

        if file_format == "csv":
            signal_data.save_csv(filename, channel_label="Signal")
        else:
            signal_data.save_wfdb(filename, channel_label="Signal")

    def toggle_acquisition(self):
        self.state_machine.toggle_acquisition()
        if self.model.acquisition_running:
            self.acquisition_button.setText("Pause Acquisition")
            self.acquisition_status_label.setText("Acquisition In Progress...")
            self.acquisition_button.setObjectName("amberButton")
            self.back_button.setEnabled(False)

            self.save_template_button.setEnabled(False)
            self.save_template_button.setObjectName("greyButton")

            self.save_data_button.setEnabled(False)
            self.save_data_button.setObjectName("greyButton")
        else:
            self.acquisition_button.setText("Resume Acquisition")
            self.acquisition_status_label.setText("Acquisition Paused")
            self.acquisition_button.setObjectName("greenButton")
            self.back_button.setEnabled(True)

            self.save_template_button.setEnabled(True)
            self.save_template_button.setObjectName("blueButton")

            self.save_data_button.setEnabled(True)
            self.save_data_button.setObjectName("blueButton")

        self._update_button_style(self.acquisition_button)
        self._update_button_style(self.save_template_button)
        self._update_button_style(self.save_data_button)

    def update_graph(self):
        """Main slot that updates both the main plot and the template plot."""
        data = self.state_machine.model.signal_data.data
        sample_rate = self.state_machine.model.signal_data.sample_rate

        # 1) Figure out which portion of the data is visible
        t_visible, data_visible = self._prepare_visible_data(data, sample_rate)

        # 2) Update the main (acquisition) plot
        self._update_main_plot(t_visible, data_visible)

        # 3) Update the template plot
        if self.model.get_template:
            template = self.model.template_processor.get_template()
            self._update_template_plot(template)

    # -------------------------------------------------------------------------
    #  Helper methods for update_graph
    # -------------------------------------------------------------------------
    def _prepare_visible_data(self, data: np.ndarray, sample_rate: float):
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

    def _update_template_plot(self, template: np.ndarray):
        if len(template) > 0:
            # setup time axis for template
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
        min_val = np.min(data)
        max_val = np.max(data)

        if min_val == max_val:
            return (min_val - 1, max_val + 1)
        else:
            margin = margin_ratio * (max_val - min_val)
            return (min_val - margin, max_val + margin)

    # -------------------------------------------------------------------------
    #  Template Parameter Handlers
    # -------------------------------------------------------------------------
    def _on_look_back_changed(self, value: float):
        self.model.template_processor.look_back_time = value

    def _on_update_interval_changed(self, value: float):
        self.model.template_processor.update_interval_s = value

    # -------------------------------------------------------------------------
    #  Save Template
    # -------------------------------------------------------------------------
    def save_template(self):
        template_processor = self.model.template_processor

        file_format = self._get_selected_format()
        if file_format == "csv":
            filter_str = "CSV Files (*.csv)"
        else:
            filter_str = "WFDB Files (*.dat)"

        filename, _ = QFileDialog.getSaveFileName(self, "Save Template", "", filter_str)
        if not filename:
            return

        if file_format == "csv":
            template_processor.save_csv(filename, channel_label="Template")
        else:
            template_processor.save_wfdb(filename, channel_label="Template")

    def _get_selected_format(self) -> str:
        return "csv" if self.csv_radio.isChecked() else "wfdb"

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

        self.save_template_button.setEnabled(False)
        self.save_template_button.setObjectName("greyButton")
        self._update_button_style(self.save_template_button)
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
