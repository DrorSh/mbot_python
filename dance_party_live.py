#!/usr/bin/env python3
"""
ROBOT DANCE PARTY -- live over Bluetooth!  🤖💃

This drives the mBot2 from the PC in real time (no mBlock, no uploading).
Run it, then type a number to make the robot dance:

    py dance_party_live.py

    1 = Wiggle Boogie
    2 = Spin & Sparkle
    q = Quit

KIDS: try changing things!
  - The 3 numbers in led(...) are colors: (Red, Green, Blue), each 0-255.
  - The number in forward()/turn_left() is the SPEED.
  - tone(800, 0.2) -> bigger first number = higher beep.
  - Give the robot floor space so it can dance!
"""

import asyncio
from mbot2_live import MBot2Live


async def beep(bot, freq, secs=0.2):
    await bot.tone(freq, secs)
    await asyncio.sleep(secs + 0.05)


# ---- Dance #1: The Wiggle Boogie ------------------------------------------
async def wiggle_boogie(bot):
    print("  Wiggle Boogie!")
    await bot.script("cyberpi.led.play(name='rainbow')")   # built-in rainbow show

    for _ in range(4):                       # wiggle side to side
        await bot.led(255, 0, 0)
        await bot.turn_left(70, 0.25);   await asyncio.sleep(0.3)
        await bot.led(0, 0, 255)
        await bot.turn_right(70, 0.25);  await asyncio.sleep(0.3)

    await bot.led(0, 255, 0)
    await bot.forward(50, 0.5);   await asyncio.sleep(0.6)   # scoot forward
    await bot.backward(50, 0.5);  await asyncio.sleep(0.6)   # scoot back
    await beep(bot, 880, 0.25)

    await bot.led(255, 255, 0)
    await bot.turn(360);          await asyncio.sleep(2.2)   # one big spin!
    await bot.led_off()
    print("  ...ta-da!")


# ---- Dance #2: Spin & Sparkle ---------------------------------------------
async def spin_and_sparkle(bot):
    print("  Spin & Sparkle!")
    for _ in range(3):
        await bot.led(255, 0, 255)
        await bot.turn(180);   await asyncio.sleep(1.2)      # half spin
        await beep(bot, 1047, 0.15)
        await bot.led(0, 255, 255)
        await bot.turn(-180);  await asyncio.sleep(1.2)      # spin back
        await beep(bot, 784, 0.15)

    await bot.script("cyberpi.led.play(name='firefly')")     # sparkly finish
    await asyncio.sleep(1.0)
    await bot.led_off()
    print("  ...sparkle!")


async def main():
    bot = MBot2Live()
    await bot.connect()
    loop = asyncio.get_event_loop()
    try:
        while True:
            print("\n=== DANCE PARTY ===")
            print("  1 = Wiggle Boogie")
            print("  2 = Spin & Sparkle")
            print("  q = Quit")
            choice = (await loop.run_in_executor(None, input, "Your pick: ")).strip().lower()
            if choice == "1":
                await wiggle_boogie(bot)
            elif choice == "2":
                await spin_and_sparkle(bot)
            elif choice == "q":
                print("Bye! 👋")
                break
            else:
                print("  Type 1, 2, or q")
    finally:
        await bot.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
