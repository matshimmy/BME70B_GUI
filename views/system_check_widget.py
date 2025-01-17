from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout
)
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt


class SystemCheckWidget(QWidget):
    def __init__(self):
        super().__init__()

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

        # Spinner for Connection
        self.spinner_connection = QLabel()
        # Load a GIF spinner (replace with an actual path in your project)
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

        # Spinner for Power Level
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

        # Spinner for Transmission Testing
        self.spinner_transmission = QLabel()
        movie_trans = QMovie("resources/spinner.gif")
        self.spinner_transmission.setMovie(movie_trans)
        movie_trans.start()
        row_transmission.addWidget(self.spinner_transmission)

        main_layout.addLayout(row_transmission)

        # Set the main layout
        self.setLayout(main_layout)
