#!/usr/bin/env python3
"""
Destroyer-DoS GUI Entry Point
Executable script for graphical interface
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import and run the GUI
if __name__ == '__main__':
    try:
        from src.destroyer_dos.core.interfaces.web_gui import WebGUI
        gui = WebGUI()
        sys.exit(gui.run())
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)
