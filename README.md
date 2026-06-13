# mBot2 Python 🤖💃

Control a **Makeblock mBot2 (CyberPi)** robot from your PC in **pure Python over Bluetooth** —
no mBlock, no uploading, no special dongle. A learn-to-code project built with my 8-year-old daughter.

The headline feature: a **live dance party** you trigger from the keyboard. Pick a number, the robot
moves, flashes its lights, and beeps — all driven in real time from Python.

## How it works

The CyberPi's Bluetooth pipe speaks Makeblock's private **"f3/f4" framing** (the same "Live Mode"
mBlock uses). Each frame wraps a snippet of Python (e.g. `mbot2.forward(50)`) that the robot
evaluates instantly and can answer with a JSON result. This repo implements that protocol from
scratch on top of [`bleak`](https://github.com/hbldh/bleak):

1. Connect over BLE, subscribe to notify characteristic `ffe2`, write to `ffe3`
2. Send the "enter live mode" frame
3. Spam a sensor read until the robot replies (handshake)
4. Stream Python commands → the robot runs them live

## Setup

```bash
pip install -r requirements.txt
```

Turn the robot **on**, make sure it isn't connected to a phone or mBlock, and you're ready.

## Run it

```bash
# Safe check — lights + sound only, robot does NOT move
py mbot2_live.py --test

# Gentle drive + spin (give it floor space!)
py mbot2_live.py --move

# THE DANCE PARTY (run this one with a kid)
py dance_party_live.py
#   1 = Wiggle Boogie
#   2 = Spin & Sparkle
#   q = Quit
```

## Files

| File | What it is |
| --- | --- |
| `mbot2_live.py` | The driver: `MBot2Live` class (pure-Python BLE control) + `--test` / `--move` |
| `dance_party_live.py` | Interactive dance menu — the fun one |
| `dance_party.py` | The same dances as **onboard** MicroPython (paste into mBlock Upload mode to run untethered) |
| `bluetooth_scan.ps1` | Windows PowerShell scanner that finds the robot over BLE |
| `ble_explore.py` | Lists the robot's Bluetooth services/characteristics |
| `ble_probe.py` | Probes the BLE pipe (used while reverse-engineering the protocol) |
| `mbot2_control.py` | Early attempt using the old mBot1 protocol — kept for history; **superseded by `mbot2_live.py`** |

## For kids — things to change

Open `dance_party_live.py` and try:
- **Colors:** `led(255, 0, 0)` → the numbers are Red, Green, Blue (0–255). Invent a color!
- **Speed:** the number in `forward(50, 0.5)` — try `80`.
- **Beeps:** `beep(bot, 880)` — bigger number = higher note.
- **New dance:** copy the `wiggle_boogie` block, rename it, change the moves.

## Credits

The f3/f4 protocol details were figured out with help from
[Hulupeep/mbot_ruvector](https://github.com/Hulupeep/mbot_ruvector) (which traces back to
Makeblock's own `makeblock` pip package). The Python/`bleak` driver here is an independent
implementation.
