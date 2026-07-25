# Sensors in depth 👀

The mBot2's fun really starts when it can *sense* the world and react. This page goes
deeper than the [command reference](commands.md) on the two headline sensors — the
**ultrasonic distance sensor** (the robot's "eyes") and the **line-follower** (its
"eyes on the floor") — how they work, what they can and can't do, and how to read them
from Python.

> **Which sensors is this about?** The mBot2 kit ships with two *mBuild* sensors:
> the **Ultrasonic Sensor 2** and the **Quad RGB Sensor** (line + color). They work on
> exactly the same physical principles as the classic mBot "Me" sensors, so the
> explanations below apply to both — only a few numbers and the code calls differ.
> Spec numbers marked *(Me sensor)* come from Makeblock's own docs, linked at the
> [bottom of this page](#where-these-numbers-come-from).

---

## 📏 Ultrasonic distance sensor — the robot's "eyes"

The two round "eyes" on the front are an **ultrasonic sensor**. It measures how far away
the nearest thing is — perfect for "don't crash into the wall" and "stop at the edge"
programs.

### How it works — like a bat 🦇

One eye is a tiny speaker, the other a tiny microphone. The speaker sends out a burst of
sound *too high for people to hear* (about **42 kHz** — way above the ~20 kHz limit of
human hearing) and a timer starts. The sound flies out, bounces off an object, and comes
back to the microphone, which stops the timer.

Sound travels at about **340 metres per second**, so the robot works out the distance
with:

```
distance = 340 m/s × time ÷ 2      (÷2 because the sound goes there AND back)
```

This is the same trick bats and submarines (sonar) use.

### What to expect (specs)

| Thing | Value | Kid translation |
| --- | --- | --- |
| Range | **3 cm – ~300 cm** on this mBot2 *(Me sensor: 3–400 cm, error < 1 cm)* | From "almost touching" to "across the room" |
| Beam angle | **less than 30°** | It only "sees" a narrow cone straight ahead |
| Sound frequency | **42 kHz** | A super-high squeak we can't hear |
| Power | 5 V | Comes from the robot |

> ✅ **Verified on a real mBot2** (firmware 44.01.013): `bot.distance()` returns a live value
> in cm, and reads **300** when nothing is in range. Held a hand ~13 cm away and it read
> `13.4`.

### Reading it in Python

```python
from mbot2 import MBot2

with MBot2() as bot:
    cm = bot.distance()          # how far is the nearest thing, in centimetres
    print("Nearest object:", cm, "cm")
```

`bot.distance()` is a wrapper for `cyberpi.ultrasonic2.get(1)`. When nothing is in range
it reads **300** (the sensor's max on this mBot2), so `bot.distance()` returning `300.0`
means "the coast is clear."

**A "don't crash" loop** — drive forward, but stop and turn when something gets close:

```python
from mbot2 import MBot2

with MBot2() as bot:
    while True:
        if bot.distance() < 15:      # something within 15 cm
            bot.stop()
            bot.led(255, 0, 0)       # red = "wall!"
            bot.turn(90)             # turn away
        else:
            bot.led(0, 255, 0)       # green = "all clear"
            bot.forward(30)          # keep rolling (no secs = until we change it)
        bot.sleep(0.1)               # check ~10 times a second
```

### The glowing "eyes" 💡

On the mBot2's Ultrasonic Sensor 2, the ring around each eye is a set of programmable blue
LEDs — and the firmware has built-in **emotion animations** for them, so the robot's "eyes"
can look happy, wink, get dizzy, glance around, and more:

```python
bot.run("cyberpi.ultrasonic2.happy_effect()")     # 😊
bot.run("cyberpi.ultrasonic2.wink_effect()")      # 😉
bot.run("cyberpi.ultrasonic2.dizzy_effect()")     # 😵
bot.run("cyberpi.ultrasonic2.look_left_effect()") # 👀
bot.run("cyberpi.ultrasonic2.set_bri(50)")        # plain brightness 0–100
```

See the full list (verified on firmware 44.01.013) with
`print(bot.eval("dir(cyberpi.ultrasonic2)"))` — others include `naughty_effect`,
`thinking_effect`, `standby_effect`, and `show_led_emotion`.

### Tips & gotchas ⚠️

- **Too close is blind.** Closer than ~**3 cm** the echo comes back before the sensor is
  listening, so readings get unreliable. Keep a little gap.
- **Soft things swallow the sound.** Curtains, cushions, jumpers, a fluffy pet — soft
  surfaces absorb the ultrasonic "ping" instead of bouncing it back, so the robot may
  report a *too-far* number or nothing at all.
- **Angled surfaces bounce it away.** If a wall is slanted, the echo ricochets off to the
  side instead of straight back — the robot "misses" it. Sensors like walls it can hit
  head-on.
- **It only sees a narrow cone (<30°).** A thin chair leg off to the side can be invisible.
- **Sometimes you get a weird number.** A single bad reading happens. If your robot acts
  jumpy, take a few readings and use the smallest, or average them.

---

## 🐜 Line-follower — the robot's "eyes on the floor"

Point the robot down a track and it can **follow a black line all by itself**. The
downward-facing sensor board under the robot is the **line-follower** (on the mBot2, the
**Quad RGB Sensor**).

### How it works — black hides, white shines ✨

Each probe has a tiny **infrared (IR) light** and an **IR detector** sitting side by side,
both pointing at the floor:

- Over **white** paper, the IR light bounces straight back up → the detector sees lots of
  reflection → reads **"white" (1)**.
- Over a **black** line, the black ink *absorbs* the IR → almost nothing bounces back →
  reads **"black" (0)**.

By watching which probes are over black and which are over white, the robot knows if the
line is drifting left or right, and steers to stay centred. (IR is invisible to us, but
it's the same kind of light a TV remote uses.)

### Two probes vs four

- The **classic Me Line Follower** has **2 probes** (left + right) → 4 possible states.
- The mBot2's **Quad RGB Sensor** has **4 probes** in a row, so it senses the line's
  position much more precisely — and it can even read **colors**, not just black/white.

### What to expect (specs)

| Thing | Value | Kid translation |
| --- | --- | --- |
| Sensing height | **1–2 cm** *(Me sensor)* | Mount it a finger's width above the floor |
| Reads | black vs white (mBot2: also color) | "line" vs "no line" |
| Weakness | affected by room light | Bright sun / big shadows can fool it |

### Reading it in Python

There's no friendly wrapper for this one yet, so use `bot.eval(...)` to call the sensor
directly. These calls are all **verified working on a real mBot2** (firmware 44.01.013):

```python
from mbot2 import MBot2

with MBot2() as bot:
    # Which probes see the line, as a 4-bit pattern 0..15 (all four = 15)
    print(bot.eval("cyberpi.quad_rgb_sensor.get_line_sta()"))

    # How far off-centre the line is, roughly -100 (far left) .. +100 (far right)
    print(bot.eval("cyberpi.quad_rgb_sensor.get_offset_track()"))

    # Ask one probe (1–4) directly
    print(bot.eval("cyberpi.quad_rgb_sensor.is_line(1)"))          # 1 = over the line
    print(bot.eval("[cyberpi.quad_rgb_sensor.get_gray(i) for i in (1,2,3,4)]"))  # 0–100 each
```

> 💡 Other handy methods on the sensor: `study()` (calibrate to *your* black & white),
> `get_red/green/blue(i)`, `set_led(...)`, and `get_color_sta()`. See them all with
> `print(bot.eval("dir(cyberpi.quad_rgb_sensor)"))`, or run `py tools/introspect.py`.

**A simple follow-the-line loop** using the "offset" (how far the line has drifted):

```python
from mbot2 import MBot2

with MBot2() as bot:
    while True:
        offset = bot.eval("cyberpi.quad_rgb_sensor.get_offset_track()")
        # Steer toward the line: nudge the wheel speeds by the offset
        left  = 25 + offset * 0.3
        right = 25 - offset * 0.3
        bot.drive(left, right)
        bot.sleep(0.02)
```

### Building a good track & tips 🏁

- **High contrast wins.** A **matte black line on a white background** (or the reverse)
  works best. Shiny/glossy tape can reflect IR and confuse it.
- **Line width ~1.5–2 cm** suits the sensor spacing — about the width of electrical tape.
- **Even lighting.** The IR detector is *sensitive to room light*, so avoid direct sun,
  flickering lamps, or a track half in shadow. A steady, evenly-lit floor is ideal.
- **Mount it low.** Keep the sensor about **1 cm** off the floor — too high and the
  reflection is too weak to tell black from white.
- **Go smooth, not fast.** Gentle speeds let the robot correct before it loses the line.
- **Calibrate if it's fussy.** The Quad RGB Sensor can be "shown" your black and white so
  it knows the difference on your exact track — see the effects/calibration methods in
  `dir(cyberpi.quad_rgb_sensor)`.

---

## The other sensors

The mBot2's brain (CyberPi) has *lots* more built in — light, sound, a gyro/tilt sensor,
buttons and a joystick — plus dozens of plug-in mBuild modules. The friendly wrappers
(`bot.brightness()`, `bot.loudness()`, `bot.roll()`, `bot.button("a")`, …) and the full
list live in the **[command reference](commands.md#sensors--motion-cyberpi)**.

To discover exactly what any sensor can do on *your* robot:

```python
from mbot2 import MBot2
with MBot2() as bot:
    print(bot.eval("dir(cyberpi.ultrasonic2)"))
    print(bot.eval("dir(cyberpi.quad_rgb_sensor)"))
```

---

## Where these numbers come from

The physical specs above are from Makeblock's official sensor pages (for the classic mBot
"Me" versions — same working principle as the mBot2 modules):

- **Me Ultrasonic Sensor** — range 3–400 cm, detection angle < 30°, 42 kHz:
  <https://support.makeblock.com/hc/en-us/articles/12797662557719-About-Me-Ultrasonic-Sensor-for-mBot>
- **Me Line Follower** — detection range 1–2 cm, IR reflection, black = 0 / white = 1,
  susceptible to natural light:
  <https://support.makeblock.com/hc/en-us/articles/12797544445847-About-Me-Line-Follower-for-mBot>
