#!/usr/bin/env python3
"""
mbot2_live.py - Control the mBot2 / CyberPi from the PC over Bluetooth, in pure
Python, with NO mBlock.

How it works (reverse-engineered "Live Mode"):
  The CyberPi speaks a binary "f3/f4" framing protocol over its BLE serial pipe.
  Each frame carries a snippet of Python (e.g. "mbot2.forward(50)"). The robot
  evaluates it live and can return a JSON result. We:
    1. connect over BLE, subscribe to notify char ffe2, write to ffe3
    2. send the "enter live mode" frame
    3. send a sensor-read until the robot answers (handshake)
    4. stream Python commands -> robot runs them instantly

Protocol credit: the f3/f4 frame format was documented by the open-source
project github.com/Hulupeep/mbot_ruvector (derived from Makeblock's own
"makeblock" pip package). This file is an independent Python/bleak driver.

Run a safe self-test (LED + beep, no movement):
    py mbot2_live.py --test
"""

import asyncio
import sys
from bleak import BleakScanner, BleakClient

# --- BLE addresses on the CyberPi -------------------------------------------
WRITE_UUID  = "0000ffe3-0000-1000-8000-00805f9b34fb"   # we write here
NOTIFY_UUID = "0000ffe2-0000-1000-8000-00805f9b34fb"   # robot notifies here
NAME_HINTS  = ("makeblock", "cyberpi", "mbot", "bluefi")

# --- f3/f4 protocol constants -----------------------------------------------
HEADER, FOOTER = 0xF3, 0xF4
TYPE_SCRIPT = 0x28
MODE_NO_RESPONSE   = 0x00
MODE_WITH_RESPONSE = 0x01
ONLINE_MODE_FRAME = bytes([0xF3, 0xF6, 0x03, 0x00, 0x0D, 0x00, 0x01, 0x0E, 0xF4])

BLE_CHUNK = 20   # write the frame in 20-byte BLE packets (classic ffe-module size)


def build_script_frame(script: str, idx: int, mode: int) -> bytes:
    """Wrap a Python snippet in an f3/f4 frame (mirrors mbot_ruvector protocol.rs)."""
    sb = script.encode("utf-8")
    data = bytes([len(sb) & 0xFF, (len(sb) >> 8) & 0xFF]) + sb
    idx_lo, idx_hi = idx & 0xFF, (idx >> 8) & 0xFF
    datalen = len(data) + 4                       # type + mode + idx_lo + idx_hi
    hdr_check = (((datalen >> 8) & 0xFF) + (datalen & 0xFF) + 0xF3) & 0xFF
    head = bytes([HEADER, hdr_check, datalen & 0xFF, (datalen >> 8) & 0xFF,
                  TYPE_SCRIPT, mode, idx_lo, idx_hi])
    cksum = (TYPE_SCRIPT + mode + idx_lo + idx_hi + sum(data)) & 0xFF
    return head + data + bytes([cksum, FOOTER])


class MBot2Live:
    def __init__(self):
        self.client = None
        self._idx = 1
        self._got_reply = False

    def _next_idx(self):
        i = self._idx
        self._idx = (self._idx % 0xFFFF) + 1
        return i

    def _on_notify(self, _char, data: bytearray):
        if HEADER in bytes(data):
            self._got_reply = True

    async def connect(self):
        print("Scanning for the robot...")
        device = await BleakScanner.find_device_by_filter(
            lambda d, adv: any(h in ((adv.local_name or d.name or "").lower())
                               for h in NAME_HINTS),
            timeout=15.0,
        )
        if not device:
            raise RuntimeError("Robot not found. Is it ON and not connected elsewhere?")
        print(f"Connecting to {device.name or device.address} ...")
        self.client = BleakClient(device)
        await self.client.connect()
        await self.client.start_notify(NOTIFY_UUID, self._on_notify)
        print("Connected. Entering Live Mode...")
        await self._handshake()
        print("Live Mode ready! The robot is taking commands.\n")

    async def _write(self, frame: bytes):
        for i in range(0, len(frame), BLE_CHUNK):
            await self.client.write_gatt_char(WRITE_UUID, frame[i:i + BLE_CHUNK],
                                              response=False)
            await asyncio.sleep(0.01)

    async def _handshake(self):
        await self._write(ONLINE_MODE_FRAME)
        await asyncio.sleep(0.5)
        for attempt in range(10):
            self._got_reply = False
            frame = build_script_frame("cyberpi.get_bri()", self._next_idx(),
                                       MODE_WITH_RESPONSE)
            await self._write(frame)
            await asyncio.sleep(0.5)
            if self._got_reply:
                self._idx = 1
                return
        print("  (warning: robot didn't acknowledge, but continuing anyway)")
        self._idx = 1

    async def script(self, code: str, wait_response=False):
        """Send a Python snippet for the robot to run."""
        mode = MODE_WITH_RESPONSE if wait_response else MODE_NO_RESPONSE
        await self._write(build_script_frame(code, self._next_idx(), mode))

    # --- convenience commands (all run on the robot via Live Mode) ----------
    # Pass secs to make the robot move for that long then auto-stop ON ITS OWN
    # (safer: it stops even if a later Bluetooth packet is dropped).
    @staticmethod
    def _mv(fn, speed, secs):
        return f"mbot2.{fn}({speed})" if secs is None else f"mbot2.{fn}({speed},{secs})"

    async def forward(self, speed=50, secs=None):   await self.script(self._mv("forward", speed, secs))
    async def backward(self, speed=50, secs=None):  await self.script(self._mv("backward", speed, secs))
    async def turn_left(self, speed=50, secs=None): await self.script(self._mv("turn_left", speed, secs))
    async def turn_right(self, speed=50, secs=None):await self.script(self._mv("turn_right", speed, secs))
    async def turn(self, angle):            await self.script(f"mbot2.turn({angle})")   # gyro turn, degrees
    async def stop(self):                   await self.script("mbot2.EM_stop()")
    async def led(self, r, g, b):           await self.script(f"cyberpi.led.on({r},{g},{b})")
    async def led_off(self):                await self.script("cyberpi.led.on(0,0,0)")
    async def tone(self, freq, secs=0.5):   await self.script(f"cyberpi.audio.play_tone({freq},{secs})")
    async def say(self, text):              await self.script(f"cyberpi.display.show_label('{text}',24,'center')")

    async def disconnect(self):
        if self.client and self.client.is_connected:
            try:
                await self.stop()
            except Exception:
                pass
            await self.client.disconnect()
            print("Disconnected.")


async def self_test():
    """Safe test: light + sound only. The robot does NOT move."""
    bot = MBot2Live()
    try:
        await bot.connect()
        print(">> Green light")
        await bot.led(0, 255, 0);   await asyncio.sleep(1)
        print(">> Beep")
        await bot.tone(784, 0.4);   await asyncio.sleep(0.6)
        print(">> Red light")
        await bot.led(255, 0, 0);   await asyncio.sleep(1)
        print(">> Higher beep")
        await bot.tone(1047, 0.4);  await asyncio.sleep(0.6)
        print(">> Lights off")
        await bot.led_off();        await asyncio.sleep(0.5)
        print("\nIf the robot lit up and beeped: WE HAVE CONTROL. ")
    finally:
        await bot.disconnect()


async def move_test():
    """Gentle movement test. Each move is time-limited so the robot self-stops."""
    bot = MBot2Live()
    try:
        await bot.connect()
        print("Make sure the robot has room to move!\n")
        await bot.led(0, 0, 255)
        print(">> forward");    await bot.forward(40, 0.6);    await asyncio.sleep(1.1)
        print(">> backward");   await bot.backward(40, 0.6);   await asyncio.sleep(1.1)
        print(">> spin left");  await bot.turn_left(40, 0.5);  await asyncio.sleep(1.0)
        print(">> spin right"); await bot.turn_right(40, 0.5); await asyncio.sleep(1.0)
        await bot.stop()
        await bot.led_off()
        print("\nIf it drove and spun: full motion control confirmed!")
    finally:
        await bot.disconnect()


if __name__ == "__main__":
    if "--test" in sys.argv:
        asyncio.run(self_test())
    elif "--move" in sys.argv:
        asyncio.run(move_test())
    else:
        print("Usage:")
        print("  py mbot2_live.py --test   (safe light + sound, no movement)")
        print("  py mbot2_live.py --move   (gentle drive + spin -- give it floor space!)")
