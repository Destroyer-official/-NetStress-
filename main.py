#!/usr/bin/env python3
"""
NetStress - Network Stress Testing Framework
Main Entry Point

For the full attack engine, use ddos.py directly.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point - delegates to ddos.py"""
    try:
        from ddos import main as ddos_main
        ddos_main()
    except ImportError as e:
        print(f"Error importing ddos module: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)

if __name__ == '__main__':
    main()
