"""
keyboard_drive.py - drive the robot like a remote control.
Keys:  W = forward   S = back   A = left   D = right   space = stop   Q = quit
Run it:  py examples/keyboard_drive.py    (Windows)

Each key nudges the robot briefly, so it can't run away if you let go.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from mbot2 import MBot2

try:
    import msvcrt  # Windows keyboard input
except ImportError:
    print("This example uses Windows keyboard input (msvcrt).")
    sys.exit(1)

SPEED = 50
BURST = 0.25   # seconds per key press

print(__doc__)

with MBot2() as bot:
    bot.led(0, 0, 255)
    while True:
        key = msvcrt.getch().decode("utf-8", "ignore").lower()
        if key == "q":
            break
        elif key == "w":
            bot.forward(SPEED, BURST)
        elif key == "s":
            bot.backward(SPEED, BURST)
        elif key == "a":
            bot.turn_left(SPEED, BURST)
        elif key == "d":
            bot.turn_right(SPEED, BURST)
        elif key == " ":
            bot.stop()

print("Bye!")
