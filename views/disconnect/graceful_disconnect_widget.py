import qtawesome as qta
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QSize

from views.common.base_widget import BaseWidget

class GracefulDisconnectWidget(BaseWidget):
    # Default label strings
    DEFAULT_TOP_LABEL = "Graceful Disconnect in progress..."
    DEFAULT_CONNECTION_LABEL = "Ending Connection"
    DEFAULT_POWER_LABEL = "Shutting Off Power"
    DEFAULT_TRANSMISSION_LABEL = "Ending Transmission"

    def _setup_ui(self):
        # Connect to model_changed so we can update check marks/spinners
        self.model.model_changed.connect(self.update_ui)

        # A green check icon to reuse once each step is done
        self.green_check_icon = qta.icon('mdi.check-bold', color='#34b233')

        # We'll keep references to the spinner animations so we can revert if needed
        self.spin_anim_conn = None
        self.spin_icon_conn = None
        self.spin_anim_power = None
        self.spin_icon_power = None
        self.spin_anim_trans = None
        self.spin_icon_trans = None

        # Main layout for the center portion
        middle_layout = QVBoxLayout()
        middle_layout.setAlignment(Qt.AlignCenter)

        # Spacer at the top (pushes content vertically centered)
        middle_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Top label
        self.top_label = QLabel(self.DEFAULT_TOP_LABEL)
        self.top_label.setAlignment(Qt.AlignCenter)
        middle_layout.addWidget(self.top_label)

        # ---------------------------
        # Row for "Ending Connection"
        # ---------------------------
        row_connection = QHBoxLayout()
        row_connection.setAlignment(Qt.AlignCenter)

        self.label_connection = QLabel(self.DEFAULT_CONNECTION_LABEL)
        self.label_connection.setAlignment(Qt.AlignCenter)
        row_connection.addWidget(self.label_connection)

        self.spinner_connection = qta.IconWidget(size=QSize(50, 50))
        row_connection.addWidget(self.spinner_connection)
        middle_layout.addLayout(row_connection)

        # ---------------------------
        # Row for "Shutting Off Power"
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
        # Row for "Ending Transmission"
        # ---------------------------
        row_transmission = QHBoxLayout()
        row_transmission.setAlignment(Qt.AlignCenter)

        self.label_transmission = QLabel(self.DEFAULT_TRANSMISSION_LABEL)
        self.label_transmission.setAlignment(Qt.AlignCenter)
        row_transmission.addWidget(self.label_transmission)

        self.spinner_transmission = qta.IconWidget(size=QSize(50, 50))
        row_transmission.addWidget(self.spinner_transmission)
        middle_layout.addLayout(row_transmission)

        # Spacer at the bottom
        middle_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignLeft)

        self.force_button = QPushButton("Force Disconnect")
        self.force_button.setObjectName("redButton")
        self.force_button.clicked.connect(self.device_controller.force_disconnect)
        bottom_layout.addWidget(self.force_button)

        # Combine middle and bottom
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(middle_layout)
        outer_layout.addLayout(bottom_layout)
        self.setLayout(outer_layout)

        self.reset_ui()

    def update_ui(self):
        # If the Worker updates these fields in the Model, we can do:
        if self.model.disconnect_conn_done:
            # Step 1 done -> show check mark
            self.spinner_connection.setIcon(self.green_check_icon)
            self.label_connection.setText("Connection Ended")

        else:
            # not done -> revert spinner
            self.spinner_connection.setIcon(self.spin_icon_conn)
            self.label_connection.setText("Ending Connection")

        if self.model.disconnect_power_done:
            self.spinner_power.setIcon(self.green_check_icon)
            self.label_power.setText("Power Off")
        else:
            self.spinner_power.setIcon(self.spin_icon_power)
            self.label_power.setText("Shutting Off Power")

        if self.model.disconnect_trans_done:
            self.spinner_transmission.setIcon(self.green_check_icon)
            self.label_transmission.setText("Transmission Ended")
        else:
            self.spinner_transmission.setIcon(self.spin_icon_trans)
            self.label_transmission.setText("Ending Transmission")

    def reset_ui(self):
        self.reset_spinners()
        self.label_connection.setText(self.DEFAULT_CONNECTION_LABEL)
        self.label_power.setText(self.DEFAULT_POWER_LABEL)
        self.label_transmission.setText(self.DEFAULT_TRANSMISSION_LABEL)
        self.top_label.setText(self.DEFAULT_TOP_LABEL)

    def reset_spinners(self):
        # Connection
        self.spin_anim_conn = qta.Spin(self.spinner_connection, autostart=True)
        self.spin_icon_conn = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_conn
        )
        self.spinner_connection.setIcon(self.spin_icon_conn)

        # Power
        self.spin_anim_power = qta.Spin(self.spinner_power, autostart=True)
        self.spin_icon_power = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_power
        )
        self.spinner_power.setIcon(self.spin_icon_power)

        # Transmission
        self.spin_anim_trans = qta.Spin(self.spinner_transmission, autostart=True)
        self.spin_icon_trans = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_trans
        )
        self.spinner_transmission.setIcon(self.spin_icon_trans)
