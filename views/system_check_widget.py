from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize

import qtawesome as qta

class SystemCheckWidget(QWidget):
    def __init__(self):
        super().__init__()

        # The model will be set later via setModel(...)
        self.model = None

        # Green check icon (reusable)
        self.green_check_icon = qta.icon('mdi.check-bold', color='#34b233')

        # For each row, we’ll store a separate spinner + spin animation
        # so they can spin independently.
        self.spin_anim_conn = None
        self.spin_icon_conn = None

        self.spin_anim_power = None
        self.spin_icon_power = None

        self.spin_anim_trans = None
        self.spin_icon_trans = None

        # Main vertical layout for the middle content
        middle_layout = QVBoxLayout()
        middle_layout.setAlignment(Qt.AlignCenter)

        # Spacer to push content to the vertical center
        middle_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Top label
        self.top_label = QLabel("System Check in progress...")
        self.top_label.setAlignment(Qt.AlignCenter)
        middle_layout.addWidget(self.top_label)

        # ---------------------------
        # Row for "Connection"
        # ---------------------------
        row_connection = QHBoxLayout()
        row_connection.setAlignment(Qt.AlignCenter)

        self.label_connection = QLabel("Connection")
        self.label_connection.setAlignment(Qt.AlignCenter)
        row_connection.addWidget(self.label_connection)

        # The IconWidget for the "Connection" row
        self.spinner_connection = qta.IconWidget(size=QSize(50, 50))
        row_connection.addWidget(self.spinner_connection)
        middle_layout.addLayout(row_connection)

        # ---------------------------
        # Row for "Power Level"
        # ---------------------------
        row_power = QHBoxLayout()
        row_power.setAlignment(Qt.AlignCenter)

        self.label_power = QLabel("Power Level")
        self.label_power.setAlignment(Qt.AlignCenter)
        row_power.addWidget(self.label_power)

        self.spinner_power = qta.IconWidget(size=QSize(50, 50))
        row_power.addWidget(self.spinner_power)
        middle_layout.addLayout(row_power)

        # ---------------------------
        # Row for "Transmission Testing"
        # ---------------------------
        row_transmission = QHBoxLayout()
        row_transmission.setAlignment(Qt.AlignCenter)

        self.label_transmission = QLabel("Transmission Testing")
        self.label_transmission.setAlignment(Qt.AlignCenter)
        row_transmission.addWidget(self.label_transmission)

        self.spinner_transmission = qta.IconWidget(size=QSize(50, 50))
        row_transmission.addWidget(self.spinner_transmission)
        middle_layout.addLayout(row_transmission)

        # Spacer to keep content centered
        middle_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom layout for the Abort Button
        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignLeft)

        self.abort_button = QPushButton("Abort")
        self.abort_button.setObjectName("amberButton")  # Style defined in stylesheet
        bottom_layout.addWidget(self.abort_button)

        # Outer layout to combine middle content and bottom button
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(middle_layout)
        outer_layout.addLayout(bottom_layout)

        self.setLayout(outer_layout)

        # Initialize spinner icons for each row
        self.reset_spinners()

    def setModel(self, model):
        """
        Assign the model and connect signals.
        """
        self.model = model
        # Whenever the model changes, call self.update_ui
        self.model.model_changed.connect(self.update_ui)

    def reset_spinners(self):
        """
        Re-initialize all spinners (e.g., after an abort or going back to idle).
        """
        # 1) Connection spinner
        self.spin_anim_conn = qta.Spin(self.spinner_connection, autostart=True)
        self.spin_icon_conn = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_conn
        )
        self.spinner_connection.setIcon(self.spin_icon_conn)
        self.label_connection.setText("Connection")

        # 2) Power spinner
        self.spin_anim_power = qta.Spin(self.spinner_power, autostart=True)
        self.spin_icon_power = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_power
        )
        self.spinner_power.setIcon(self.spin_icon_power)
        self.label_power.setText("Power Level")

        # 3) Transmission spinner
        self.spin_anim_trans = qta.Spin(self.spinner_transmission, autostart=True)
        self.spin_icon_trans = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_trans
        )
        self.spinner_transmission.setIcon(self.spin_icon_trans)
        self.label_transmission.setText("Transmission Testing")

        # Top label can also revert
        self.top_label.setText("System Check in progress...")

    def update_ui(self):
        """
        Slot that updates the widget based on the model's current state.
        Called automatically whenever the model emits model_changed.
        """
        if not self.model:
            return

        # ---------------------------
        # Connection
        # ---------------------------
        if self.model.is_connected:
            self.label_connection.setText(f"Connection: {self.model.connection_type}")
            # Replace spinner with a check
            self.spinner_connection.setIcon(self.green_check_icon)
        else:
            # If the user disconnected or wasn't connected
            self.label_connection.setText("Connection: NOT CONNECTED")
            # Optionally revert to spinner icon:
            self.spinner_connection.setIcon(self.spin_icon_conn)

        # ---------------------------
        # Power
        # ---------------------------
        # If you store power_level = -1 (or some sentinel) for "unchecked," use that logic:
        if self.model.power_level == -1:
            self.label_power.setText("Power Level: Unknown")
            self.spinner_power.setIcon(self.spin_icon_power)
        else:
            self.label_power.setText(f"Power Level: {self.model.power_level}%")
            self.spinner_power.setIcon(self.green_check_icon)

        # ---------------------------
        # Transmission
        # ---------------------------
        if self.model.transmission_ok:
            self.label_transmission.setText("Transmission: OK")
            self.spinner_transmission.setIcon(self.green_check_icon)
        else:
            self.label_transmission.setText("Transmission: NOT TESTED")
            self.spinner_transmission.setIcon(self.spin_icon_trans)
