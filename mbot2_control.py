#!/usr/bin/env python3
"""
mbot2 Bluetooth Control Script
A simple script to control your mbot2 robot via Bluetooth!
Perfect for learning robotics with kids.
"""

import asyncio
from bleak import BleakScanner, BleakClient

# mbot2 BLE UUIDs (CyberPi)
MBOT2_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
MBOT2_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"


class Mbot2:
    def __init__(self):
        self.client = None
        self.device = None

    async def find_robot(self):
        """Search for mbot2 robot nearby"""
        print("Looking for your mbot2 robot...")
        print("Make sure your robot is turned ON!")

        devices = await BleakScanner.discover(timeout=10.0)

        for device in devices:
            name = device.name or ""
            if "mbot" in name.lower() or "cyberpi" in name.lower() or "makeblock" in name.lower():
                print(f"Found robot: {device.name} ({device.address})")
                self.device = device
                return True

        print("\nCouldn't find mbot2. Available Bluetooth devices:")
        for device in devices:
            if device.name:
                print(f"  - {device.name} ({device.address})")

        return False

    async def connect(self):
        """Connect to the robot"""
        if not self.device:
            if not await self.find_robot():
                return False

        print(f"Connecting to {self.device.name}...")
        self.client = BleakClient(self.device.address)
        await self.client.connect()
        print("Connected!")
        return True

    async def disconnect(self):
        """Disconnect from the robot"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("Disconnected from robot")

    def _build_motor_command(self, left_speed, right_speed):
        """
        Build a motor control command for mbot2
        Speeds range from -100 to 100
        """
        # Makeblock protocol for motor control
        # Format: [0xff, 0x55, len, 0x00, action, device, port, data...]

        # Clamp speeds to valid range
        left_speed = max(-100, min(100, int(left_speed)))
        right_speed = max(-100, min(100, int(right_speed)))

        # Simple motor command format for CyberPi/mbot2
        cmd = bytearray([
            0xff, 0x55,  # Header
            0x08,        # Length
            0x00,        # Index
            0x02,        # Action: run
            0x3d,        # Device: encoder motor
            0x00,        # Port
            left_speed & 0xff if left_speed >= 0 else (256 + left_speed),
            right_speed & 0xff if right_speed >= 0 else (256 + right_speed),
        ])
        return bytes(cmd)

    async def send_command(self, command):
        """Send a command to the robot"""
        if self.client and self.client.is_connected:
            try:
                await self.client.write_gatt_char(MBOT2_CHAR_UUID, command)
            except Exception as e:
                print(f"Error sending command: {e}")

    async def move_forward(self, speed=50):
        """Move the robot forward"""
        print(f"Moving forward (speed: {speed})")
        cmd = self._build_motor_command(speed, speed)
        await self.send_command(cmd)

    async def move_backward(self, speed=50):
        """Move the robot backward"""
        print(f"Moving backward (speed: {speed})")
        cmd = self._build_motor_command(-speed, -speed)
        await self.send_command(cmd)

    async def turn_left(self, speed=40):
        """Turn the robot left"""
        print("Turning left")
        cmd = self._build_motor_command(-speed, speed)
        await self.send_command(cmd)

    async def turn_right(self, speed=40):
        """Turn the robot right"""
        print("Turning right")
        cmd = self._build_motor_command(speed, -speed)
        await self.send_command(cmd)

    async def stop(self):
        """Stop the robot"""
        print("Stopping")
        cmd = self._build_motor_command(0, 0)
        await self.send_command(cmd)


async def main():
    """Main function - control your robot!"""
    robot = Mbot2()

    try:
        # Connect to the robot
        if not await robot.connect():
            print("Failed to connect. Please check that:")
            print("  1. Your mbot2 is turned ON")
            print("  2. Bluetooth is enabled on your computer")
            print("  3. The robot is not connected to another device")
            return

        print("\n" + "="*50)
        print("   ROBOT CONTROL - Use keyboard to control!")
        print("="*50)
        print("\nCommands:")
        print("  w = Forward")
        print("  s = Backward")
        print("  a = Turn Left")
        print("  d = Turn Right")
        print("  x = Stop")
        print("  q = Quit")
        print()

        # Simple command loop
        while True:
            try:
                cmd = input("Enter command (w/a/s/d/x/q): ").strip().lower()

                if cmd == 'w':
                    await robot.move_forward()
                    await asyncio.sleep(0.5)
                    await robot.stop()
                elif cmd == 's':
                    await robot.move_backward()
                    await asyncio.sleep(0.5)
                    await robot.stop()
                elif cmd == 'a':
                    await robot.turn_left()
                    await asyncio.sleep(0.3)
                    await robot.stop()
                elif cmd == 'd':
                    await robot.turn_right()
                    await asyncio.sleep(0.3)
                    await robot.stop()
                elif cmd == 'x':
                    await robot.stop()
                elif cmd == 'q':
                    print("Goodbye!")
                    break
                else:
                    print("Unknown command. Use w/a/s/d/x/q")

            except KeyboardInterrupt:
                break

    finally:
        await robot.disconnect()


if __name__ == "__main__":
    print("mbot2 Robot Controller")
    print("="*50)
    asyncio.run(main())
