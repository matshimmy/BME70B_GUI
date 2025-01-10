from enum import Enum

class AppState(Enum):
    IDLE = "Idle"
    SYSTEM_CHECK = "System Check"
    MODE_SELECTION = "Mode Selection"
    OPTIONS = "Options"
    RUNNING = "Running"
