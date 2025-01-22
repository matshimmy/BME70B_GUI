from enum import Enum

class AppState(Enum):
    IDLE = "Idle"
    SYSTEM_CHECK = "System Check"
    MODE_SELECTION = "Mode Selection"
    ACQUISITION_OPTIONS = "Acquisition Options"
    SIMULATION_OPTIONS = "Simulation Options"
    STIMULATION_OPTIONS = "Stimulation Options"
    RUNNING_ACQUISITION = "Running Acquisition"
    RUNNING_SIMULATION = "Running Simulation"
    RUNNING_STIMULATION = "Running Stimulation"
    GRACEFUL_DISCONNECT = "Graceful Disconnect"
