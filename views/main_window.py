from PyQt5.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout
from controllers.states import AppState
from controllers.state_machine import StateMachine

from views.idle_widget import IdleWidget
from views.system_check_widget import SystemCheckWidget
from views.mode_selection_widget import ModeSelectionWidget

from worker import SystemCheckWorker
from PyQt5.QtCore import QThread, Qt

windowTitlePrefix = "BME70B App | "

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        ## Simulate the system check worker
        self.thread = QThread(self)
        self.system_check_worker = SystemCheckWorker()
        
        # Move the worker to its own thread
        self.system_check_worker.moveToThread(self.thread)

        # Connect signals
        self.system_check_worker.connection_checked.connect(self.handle_connect_checked)
        self.system_check_worker.power_checked.connect(self.handle_power_checked)
        self.system_check_worker.transmission_checked.connect(self.handle_transmission_checked)
        self.system_check_worker.finished.connect(self.handle_system_check_done)

        # Connect the thread's started signal to the worker's slot that does the check
        self.thread.started.connect(self.system_check_worker.run_system_check)
        ## done simulating the system check worker


        # Create the state machine
        self.state_machine = StateMachine()
        # Listen for state changes
        self.state_machine.state_changed.connect(self.on_state_changed)

        self.setWindowTitle(windowTitlePrefix + self.state_machine.current_state.value)
        self.setGeometry(100, 100, 800, 600)

        # Central widget + stacked widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_widget = QStackedWidget()

        # Create screen widgets
        self.idle_screen = IdleWidget()
        self.system_check_screen = SystemCheckWidget()
        self.mode_selection_screen = ModeSelectionWidget()

        # Provide the same model to the system check widget
        self.system_check_screen.setModel(self.state_machine.model)

        # Add them to the stacked widget
        self.stacked_widget.addWidget(self.idle_screen)         # index 0 (IDLE)
        self.stacked_widget.addWidget(self.system_check_screen) # index 1 (SYSTEM_CHECK)
        self.stacked_widget.addWidget(self.mode_selection_screen) # index 2 (MODE_SELECTION)

        # Connect signals from IdleWidget
        self.idle_screen.usb_button.clicked.connect(lambda: self.handle_connect_mcu('USB'))
        self.idle_screen.bt_button.clicked.connect(lambda: self.handle_connect_mcu('Bluetooth'))

        # Connect signals from SystemCheckWidget
        self.system_check_screen.abort_button.clicked.connect(lambda: self.handle_abort_system_check())

        # Connect signals for ModeSelectionWidget
        self.mode_selection_screen.disconnect_button.clicked.connect(self.handle_disconnect)

        # Layout
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.stacked_widget)

    def on_state_changed(self, new_state):
        """
        Called when the state machine changes state.
        """
        self.setWindowTitle(windowTitlePrefix + new_state.value)
        if new_state == AppState.IDLE:
            self.stacked_widget.setCurrentIndex(0)
        elif new_state == AppState.SYSTEM_CHECK:
            self.stacked_widget.setCurrentIndex(1)
        elif new_state == AppState.MODE_SELECTION:
            self.stacked_widget.setCurrentIndex(2)

    def handle_connect_mcu(self, connection_type):
        """
        Called when user clicks "Connect via USB" or "Connect via Bluetooth."
        """
        self.state_machine.connect_device(connection_type)

        self.thread.start()  # This calls run_system_check in the worker

    def handle_connect_checked(self):
        # update model -> triggers model_changed signal
        self.state_machine.do_system_check_connection()

    def handle_power_checked(self):
        # update model -> triggers model_changed signal
        self.state_machine.do_system_check_power()

    def handle_transmission_checked(self):
        self.state_machine.do_system_test_transmission()

    def handle_system_check_done(self):
        # the worker completed system checks, so maybe transition states
        self.thread.quit()
        self.thread.wait()
        # now do next step or finalize

        self.state_machine.do_system_check_done()

    def handle_disconnect(self):
        self.state_machine.disconnect_device()

    def handle_abort_system_check(self):
        # 1) Request interruption
        self.thread.requestInterruption()

        # 2) Now do your usual disconnect
        self.state_machine.disconnect_device()
        self.system_check_screen.reset_spinners()

        # 3) Quit the thread event loop and wait
        self.thread.quit()
        self.thread.wait()
