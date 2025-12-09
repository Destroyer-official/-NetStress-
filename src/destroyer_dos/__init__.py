"""
Destroyer-DoS - Advanced DDoS Testing Framework
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "Destroyer Team"
__license__ = "MIT"

import sys
from pathlib import Path

# Ensure correct path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import main components
from .core.safety import SafetyManager
from .core.networking.socket_factory import ProtocolManager

__all__ = [
    'SafetyManager',
    'ProtocolManager',
]
