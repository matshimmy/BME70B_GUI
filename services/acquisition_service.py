import time
import os
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import serial

import wfdb
from scipy.signal import resample

from models.model import Model

class AcquisitionService(QObject):
    chunk_received = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, model: Model):
        super().__init__()
        self.model = model
        self._running = False
        self.chunk_buffer = []
        
        # Arduino setup
        self.arduino = serial.Serial(port='COM3', baudrate=9600)

    def send_command(self, command):
        self.arduino.write((command + "\n").encode())
        while self.arduino.in_waiting:
            response = self.arduino.readline().decode().strip()
            print("Arduino:", response)
            return response

    def load_data(self):
        # Configure Arduino
        sampFreq = str(self.model.sampling_rate)
        response = self.send_command(f"SET SAMPLE {sampFreq}")
        # Wait for acknowledgment that contains "Sampling freq"
        
        response = self.send_command("SET FREQ 1")
        # Wait for acknowledgment that contains "Signal freq"
        
        response = self.send_command("START")
        # Wait for "Streaming started" message

    def run_acquisition(self):
        self.load_data()
        self._running = True
        chunk_size = 30

        while self._running:
            if QThread.currentThread().isInterruptionRequested():
                self._running = False
                break

            if self.arduino.in_waiting:
                try:
                    data = float(self.arduino.readline().decode().strip())
                    self.chunk_buffer.append(data)
                    
                    # When we have enough data, emit the chunk
                    if len(self.chunk_buffer) >= chunk_size:
                        chunk = np.array(self.chunk_buffer[:chunk_size])
                        self.chunk_received.emit(chunk)
                        # Keep any remaining data
                        self.chunk_buffer = self.chunk_buffer[chunk_size:]
                except ValueError:
                    print("Received invalid data from Arduino")

        # Clean up
        self.arduino.close()
        self.finished.emit()