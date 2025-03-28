from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time
from services.connection_interface import ConnectionInterface

class GracefulDisconnectService(QObject):
    disconnect_conn_done = pyqtSignal()
    disconnect_power_done = pyqtSignal()
    disconnect_trans_done = pyqtSignal()
    disconnect_finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.connection = None
        
    def set_connection(self, connection: ConnectionInterface):
        """Set the connection to disconnect"""
        self.connection = connection
    
    def run_disconnect(self):
        """
        Perform a graceful disconnect using the active connection.
        """
        if not self.connection:
            self.error.emit("No connection provided for disconnect")
            return
            
        # 1) Gracefully disable commands/features
        if QThread.currentThread().isInterruptionRequested():
            return
            
        try:
            # Send a command to prepare for disconnect, if your protocol supports it
            # self.connection.send_command("PREPARE DISCONNECT")
            self.disconnect_conn_done.emit()
        except Exception as e:
            print(f"Error during connection shutdown: {e}")
            self.disconnect_conn_done.emit()

        # 2) Power down sequence
        if QThread.currentThread().isInterruptionRequested():
            return
        
        try:
            # Send power down command if your protocol supports it
            # self.connection.send_command("POWER DOWN")
            self.disconnect_power_done.emit()
        except Exception as e:
            print(f"Error during power down: {e}")
            self.disconnect_power_done.emit()

        # 3) End transmission
        if QThread.currentThread().isInterruptionRequested():
            return
            
        try:
            # Send end transmission command if your protocol supports it
            # self.connection.send_command("END TRANSMISSION")
            self.disconnect_trans_done.emit()
        except Exception as e:
            print(f"Error during transmission shutdown: {e}")
            self.disconnect_trans_done.emit()
            
        # Final disconnect and cleanup
        if not QThread.currentThread().isInterruptionRequested():
            try:
                self.connection.disconnect()
            except Exception as e:
                print(f"Error during final disconnect: {e}")
            
            # Signal that disconnect is complete
            self.disconnect_finished.emit()
            
    def abort(self):
        """Abort the disconnect process and force disconnect"""
        if self.connection:
            try:
                self.connection.disconnect()
            except Exception as e:
                print(f"Error during abort disconnect: {e}")
            self.connection = None
