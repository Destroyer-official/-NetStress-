#!/usr/bin/env python3
"""
Destroyer-DoS CLI Entry Point
Executable script for command-line interface
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import and run the main CLI
if __name__ == '__main__':
    from src.destroyer_dos.core.interfaces.cli import CLIInterface

    cli = CLIInterface()
    sys.exit(cli.run(sys.argv[1:]))
