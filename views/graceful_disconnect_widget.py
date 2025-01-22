import qtawesome as qta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize

class GracefulDisconnectWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.spin_anim_conn = None
        self.spin_icon_conn = None

        self.spin_anim_power = None
        self.spin_icon_power = None

        self.spin_anim_trans = None
        self.spin_icon_trans = None

        # Main vertical layout
        middle_layout = QVBoxLayout()
        middle_layout.setAlignment(Qt.AlignCenter)

        # Spacer to push content to vertical center
        middle_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Top label
        self.top_label = QLabel("Graceful Disconnect in progress...")
        self.top_label.setAlignment(Qt.AlignCenter)
        middle_layout.addWidget(self.top_label)

        # Connection row
        row_connection = QHBoxLayout()
        row_connection.setAlignment(Qt.AlignCenter)
        self.label_connection = QLabel("Ending Connection")
        self.label_connection.setAlignment(Qt.AlignCenter)
        row_connection.addWidget(self.label_connection)

        self.spinner_connection = qta.IconWidget(size=QSize(50, 50))
        row_connection.addWidget(self.spinner_connection)
        middle_layout.addLayout(row_connection)

        # Power row
        row_power = QHBoxLayout()
        row_power.setAlignment(Qt.AlignCenter)
        self.label_power = QLabel("Shutting off Power")
        self.label_power.setAlignment(Qt.AlignCenter)
        row_power.addWidget(self.label_power)

        self.spinner_power = qta.IconWidget(size=QSize(50, 50))
        row_power.addWidget(self.spinner_power)
        middle_layout.addLayout(row_power)

        # Transmission row
        row_transmission = QHBoxLayout()
        row_transmission.setAlignment(Qt.AlignCenter)
        self.label_transmission = QLabel("Ending Transmission")
        self.label_transmission.setAlignment(Qt.AlignCenter)
        row_transmission.addWidget(self.label_transmission)

        self.spinner_transmission = qta.IconWidget(size=QSize(50, 50))
        row_transmission.addWidget(self.spinner_transmission)
        middle_layout.addLayout(row_transmission)

        # Spacer to keep content centered
        middle_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Outer layout to hold everything
        self.setLayout(middle_layout)

        self.reset_spinners()

    def reset_spinners(self):
        """
        Re-initialize all spinners.
        """
        # Connection
        self.spin_anim_conn = qta.Spin(self.spinner_connection, autostart=True)
        self.spin_icon_conn = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_conn
        )
        self.spinner_connection.setIcon(self.spin_icon_conn)
        self.label_connection.setText("Ending Connection")

        # Power
        self.spin_anim_power = qta.Spin(self.spinner_power, autostart=True)
        self.spin_icon_power = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_power
        )
        self.spinner_power.setIcon(self.spin_icon_power)
        self.label_power.setText("Shutting off Power")

        # Transmission
        self.spin_anim_trans = qta.Spin(self.spinner_transmission, autostart=True)
        self.spin_icon_trans = qta.icon(
            'mdi.loading', color='#90D5FF', animation=self.spin_anim_trans
        )
        self.spinner_transmission.setIcon(self.spin_icon_trans)
        self.label_transmission.setText("Ending Transmission")

        # Top label
        self.top_label.setText("Graceful Disconnect in progress...")
