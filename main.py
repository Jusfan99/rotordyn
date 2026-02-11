"""GUI entry point for RotorDyn Calculator.

Usage:
    python main.py            # Desktop window (native mode)
    python main.py --browser  # Open in browser instead
"""

import sys

from rotordyn.gui.app import run


def main():
    native = "--browser" not in sys.argv
    run(native=native)


if __name__ == "__main__":
    main()
