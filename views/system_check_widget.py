from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt, QSize

import qtawesome as qta

class SystemCheckWidget(QWidget):
    def __init__(self):
        super().__init__()

        # set later via setModel(...)
        self.model = None

        # Main vertical layout for the entire widget
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        # Top label
        self.top_label = QLabel("System Check in progress...")
        self.top_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.top_label)

        # Create row for "Connection" with spinner
        row_connection = QHBoxLayout()
        row_connection.setAlignment(Qt.AlignCenter)
        self.label_connection = QLabel("Connection")
        self.label_connection.setAlignment(Qt.AlignCenter)
        row_connection.addWidget(self.label_connection)

        self.spinner_connection = qta.IconWidget(size=QSize(50, 50))
        spin_anim_conn = qta.Spin(self.spinner_connection, autostart=True)
        spin_icon_conn = qta.icon('mdi.loading', color='#90D5FF', animation=spin_anim_conn)
        self.spinner_connection.setIcon(spin_icon_conn)
        row_connection.addWidget(self.spinner_connection)
        main_layout.addLayout(row_connection)

        # Create row for "Power Level" with spinner
        row_power = QHBoxLayout()
        row_power.setAlignment(Qt.AlignCenter)
        self.label_power = QLabel("Power Level")
        self.label_power.setAlignment(Qt.AlignCenter)
        row_power.addWidget(self.label_power)

        self.spinner_power = qta.IconWidget(size=QSize(50, 50))
        spin_anim_power = qta.Spin(self.spinner_power, autostart=True)
        spin_icon_power = qta.icon('mdi.loading', color='#90D5FF', animation=spin_anim_power)
        self.spinner_power.setIcon(spin_icon_power)
        row_power.addWidget(self.spinner_power)
        main_layout.addLayout(row_power)

        # Create row for "Transmission Testing" with spinner
        row_transmission = QHBoxLayout()
        row_transmission.setAlignment(Qt.AlignCenter)
        self.label_transmission = QLabel("Transmission Testing")
        self.label_transmission.setAlignment(Qt.AlignCenter)
        row_transmission.addWidget(self.label_transmission)

        self.spinner_transmission = qta.IconWidget(size=QSize(50, 50))
        spin_anim_trans = qta.Spin(self.spinner_transmission, autostart=True)
        spin_icon_trans = qta.icon('mdi.loading', color='#90D5FF', animation=spin_anim_trans)
        self.spinner_transmission.setIcon(spin_icon_trans)
        row_transmission.addWidget(self.spinner_transmission)
        main_layout.addLayout(row_transmission)

        self.setLayout(main_layout)

    def setModel(self, model):
        """
        Assign the model and connect signals.
        """
        self.model = model
        # Whenever the model changes, call self.update_ui
        self.model.model_changed.connect(self.update_ui)

    def update_ui(self):
        """
        Slot that updates the widget based on the model's current state.
        Called automatically whenever the model emits model_changed.
        """
        if not self.model:
            return

        # Update "Connection"
        if self.model.is_connected:
            self.label_connection.setText(f"Connection: {self.model.connection_type}")
            self.spinner_connection.setIcon(qta.icon('mdi.check-bold', color='#34b233'))
        else:
            self.label_connection.setText("Connection: NOT CONNECTED")

        # Update "Power Level"
        if self.model.power_level != -1:
            self.label_power.setText(f"Power Level: {self.model.power_level}%")
            self.spinner_power.setIcon(qta.icon('mdi.check-bold', color='#34b233'))

        # Update "Transmission Testing"
        if self.model.transmission_ok:
            self.label_transmission.setText("Transmission: OK")
            self.spinner_transmission.setIcon(qta.icon('mdi.check-bold', color='#34b233'))
        else:
            self.label_transmission.setText("Transmission: NOT TESTED")
