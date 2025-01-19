from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout
)
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt

class SystemCheckWidget(QWidget):
    def __init__(self):
        super().__init__()

        # We will set this later via setModel(...)
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

        self.spinner_connection = QLabel()
        movie_conn = QMovie("resources/spinner.gif")
        self.spinner_connection.setMovie(movie_conn)
        movie_conn.start()
        row_connection.addWidget(self.spinner_connection)
        main_layout.addLayout(row_connection)

        # Create row for "Power Level" with spinner
        row_power = QHBoxLayout()
        row_power.setAlignment(Qt.AlignCenter)
        self.label_power = QLabel("Power Level")
        self.label_power.setAlignment(Qt.AlignCenter)
        row_power.addWidget(self.label_power)

        self.spinner_power = QLabel()
        movie_power = QMovie("resources/spinner.gif")
        self.spinner_power.setMovie(movie_power)
        movie_power.start()
        row_power.addWidget(self.spinner_power)
        main_layout.addLayout(row_power)

        # Create row for "Transmission Testing" with spinner
        row_transmission = QHBoxLayout()
        row_transmission.setAlignment(Qt.AlignCenter)
        self.label_transmission = QLabel("Transmission Testing")
        self.label_transmission.setAlignment(Qt.AlignCenter)
        row_transmission.addWidget(self.label_transmission)

        self.spinner_transmission = QLabel()
        movie_trans = QMovie("resources/spinner.gif")
        self.spinner_transmission.setMovie(movie_trans)
        movie_trans.start()
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
        else:
            self.label_connection.setText("Connection: NOT CONNECTED")

        # Update "Power Level"
        self.label_power.setText(f"Power Level: {self.model.power_level}%")

        # Update "Transmission Testing"
        if self.model.transmission_ok:
            self.label_transmission.setText("Transmission: OK")
        else:
            self.label_transmission.setText("Transmission: NOT TESTED")
