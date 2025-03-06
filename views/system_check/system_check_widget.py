from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize

import qtawesome as qta
from views.common.base_widget import BaseWidget

class SystemCheckWidget(BaseWidget):
    # Default label strings
    DEFAULT_TOP_LABEL = "System Check in progress..."
    DEFAULT_CONNECTION_LABEL = "Connection"
    DEFAULT_POWER_LABEL = "Power Level"
    DEFAULT_TRANSMISSION_LABEL = "Transmission Testing"
    DEFAULT_NOT_CONNECTED = "NOT CONNECTED"
    DEFAULT_POWER_UNKNOWN = "Unknown"
    DEFAULT_TRANSMISSION_NOT_TESTED = "NOT TESTED"
    DEFAULT_TRANSMISSION_OK = "OK"

    def _setup_ui(self):
        # Whenever the model changes, call self.update_ui
        self.model.model_changed.connect(self.update_ui)

        # Green check icon (reusable)
        self.green_check_icon = qta.icon('mdi.check-bold', color='#34b233')

        # For each row, we'll store a separate spinner + spin animation
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
        self.top_label = QLabel(self.DEFAULT_TOP_LABEL)
        self.top_label.setAlignment(Qt.AlignCenter)
        middle_layout.addWidget(self.top_label)

        # ---------------------------
        # Row for "Connection"
        # ---------------------------
        row_connection = QHBoxLayout()
        row_connection.setAlignment(Qt.AlignCenter)

        self.label_connection = QLabel(self.DEFAULT_CONNECTION_LABEL)
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

        self.label_power = QLabel(self.DEFAULT_POWER_LABEL)
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

        self.label_transmission = QLabel(self.DEFAULT_TRANSMISSION_LABEL)
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
        self.abort_button.clicked.connect(self.device_controller.abort_system_check)
        bottom_layout.addWidget(self.abort_button)

        # Outer layout to combine middle content and bottom button
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(middle_layout)
        outer_layout.addLayout(bottom_layout)

        self.setLayout(outer_layout)

        self.reset_ui()

    def update_ui(self):
        # ---------------------------
        # Connection
        # ---------------------------
        if self.model.is_connected:
            self.label_connection.setText(f"{self.DEFAULT_CONNECTION_LABEL}: {self.model.connection_type.value}")
            # Replace spinner with a check
            self.spinner_connection.setIcon(self.green_check_icon)
        else:
            # If the user disconnected or wasn't connected
            self.label_connection.setText(f"{self.DEFAULT_CONNECTION_LABEL}: {self.DEFAULT_NOT_CONNECTED}")
            # Optionally revert to spinner icon:
            self.spinner_connection.setIcon(self.spin_icon_conn)

        # ---------------------------
        # Power
        # ---------------------------
        # If you store power_level = -1 (or some sentinel) for "unchecked," use that logic:
        if self.model.power_level == -1:
            self.label_power.setText(f"{self.DEFAULT_POWER_LABEL}: {self.DEFAULT_POWER_UNKNOWN}")
            self.spinner_power.setIcon(self.spin_icon_power)
        else:
            self.label_power.setText(f"{self.DEFAULT_POWER_LABEL}: {self.model.power_level}%")
            self.spinner_power.setIcon(self.green_check_icon)

        # ---------------------------
        # Transmission
        # ---------------------------
        if self.model.transmission_ok:
            self.label_transmission.setText(f"{self.DEFAULT_TRANSMISSION_LABEL}: {self.DEFAULT_TRANSMISSION_OK}")
            self.spinner_transmission.setIcon(self.green_check_icon)
        else:
            self.label_transmission.setText(f"{self.DEFAULT_TRANSMISSION_LABEL}: {self.DEFAULT_TRANSMISSION_NOT_TESTED}")
            self.spinner_transmission.setIcon(self.spin_icon_trans)

    def reset_ui(self):
        self.reset_spinners()
        self.label_connection.setText(self.DEFAULT_CONNECTION_LABEL)
        self.label_power.setText(self.DEFAULT_POWER_LABEL)
        self.label_transmission.setText(self.DEFAULT_TRANSMISSION_LABEL)
        self.top_label.setText(self.DEFAULT_TOP_LABEL)

    def reset_spinners(self):
        # 1) Connection spinner
        self.spin_anim_conn = qta.Spin(self.spinner_connection, autostart=True)
        self.spin_icon_conn = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_conn
        )
        self.spinner_connection.setIcon(self.spin_icon_conn)

        # 2) Power spinner
        self.spin_anim_power = qta.Spin(self.spinner_power, autostart=True)
        self.spin_icon_power = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_power
        )
        self.spinner_power.setIcon(self.spin_icon_power)

        # 3) Transmission spinner
        self.spin_anim_trans = qta.Spin(self.spinner_transmission, autostart=True)
        self.spin_icon_trans = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_trans
        )
        self.spinner_transmission.setIcon(self.spin_icon_trans)

