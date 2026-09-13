# Red-Beetle

Red-Beetle is a 4-wheel-drive stepper-driven rover controlled by a Raspberry Pi and an Arduino Uno CNC Shield, featuring gamepad teleoperation, open-loop A-to-B path recording/replay, MJPEG video streaming, and a browser-based canvas visualizer.

<!-- Visual Proof of Life: Replace with photo of your wired rover chassis or a 5-second demo GIF -->
<!-- ![Red-Beetle Hardware Chassis](docs/chassis.jpg) -->

---

## System Architecture

```
[ Gamepad (USB/BT) ]
        |
        v (Pygame Events)
+--------------------------------------------------------------------+
| Raspberry Pi (High-Level Controller)                               |
|                                                                    |
|  picar_controller_integrated.py           web_gui.py               |
|  - Reads gamepad inputs                   - OpenCV VideoCapture    |
|  - Differential steering mixer            - MJPEG Stream (/video)  |
|  - Path logger (path_main / path_extra)   - Dead-reckoning math    |
|  - Auto-pilot command playback            - Socket.IO server:5000  |
+--------------------------------------------------------------------+
        |                                        |
        | UART over USB (115200 baud, 8-N-1)     | WebSocket
        | "targetL,targetR\n" or "DISABLE\n"     |
        v                                        v
+------------------------------------+  +----------------------------+
| Arduino Uno + CNC Shield V3        |  | Browser Client (Port 5000) |
| - AccelStepper pulse generator     |  | - Live camera feed         |
| - Velocity smoothing (RAMP = 0.05) |  | - HTML5 Canvas path trail  |
+------------------------------------+  | - Kinematic sliders        |
        |                               +----------------------------+
        +---> [FR Step 2 / Dir 5]  [FL Step 4  / Dir 7]
        +---> [BR Step 3 / Dir 6]  [BL Step 12 / Dir 13]
              Enable Pin 8 (Active LOW)
```

---

## Technical Specifications & Pinouts

### Hardware Stack
- **Single-Board Computer:** Raspberry Pi 3B+ / 4B running Raspberry Pi OS (Python 3.9+)
- **Microcontroller:** Arduino Uno R3 running `arduino_control_code.ino`
- **Motor Driver Shield:** CNC Shield V3 with 4x A4988 / DRV8825 stepper drivers (1/16 microstepping jumpers installed)
- **Motors:** 4x NEMA 17 stepper motors (skid-steer 4WD configuration)
- **Power Delivery:** 12V DC / LiPo for motor shield rail; 5V / 3A regulated USB-C for Raspberry Pi
- **Vision:** USB Web Camera (UVC) or Pi Camera via V4L2 (`/dev/video0`)
- **Input:** Standard USB or Bluetooth Gamepad (SDL2 / Pygame compatible)
- **CAD Source Files:** Autodesk Fusion 360 models included (`Next Gen.f3d` chassis, `GIC wheels.f3d` wheels)

### CNC Shield V3 Pin Mapping
| Motor Channel | CNC Shield Axis | Step Pin | Direction Pin | Controlled Side |
| :--- | :---: | :---: | :---: | :--- |
| `motorFR` | X | Pin 2 | Pin 5 | Front Right |
| `motorBR` | Y | Pin 3 | Pin 6 | Back Right |
| `motorFL` | Z | Pin 4 | Pin 7 | Front Left |
| `motorBL` | A | Pin 12 | Pin 13 | Back Left |
| **Shield Enable** | EN | Pin 8 | — | Driver output enable (Active LOW) |

### Serial Protocol
- **Baud Rate:** 115200 baud, 8 data bits, no parity, 1 stop bit
- **Interval:** 50 ms loop cycle
- **Payload Format:** ASCII string `"<left_speed>,<right_speed>\n"` (e.g. `450,-450\n`), or `"DISABLE\n"` to de-energize coils.

---

## Gamepad Controls

| Input | Function | Action |
| :--- | :--- | :--- |
| **Left Stick Y** / **Triggers** | Throttle | Forward / Reverse motion |
| **Right Stick X** | Steering | Skid-steer rotation mixing |
| **Button A** | Mark Point A / Auto-return | First press starts recording path; subsequent returns to A |
| **Button B** | Mark Point B / Auto-drive | Locks recorded path; subsequent navigates to B |
| **Button Y** | Full System Reset | Halts motors, clears recorded path files, resets coordinates |
| **D-Pad Left** | Process Restart | Restarts `picar_controller_integrated.py` via `os.execv` |
| **D-Pad Up** | System Reboot | Executes `sudo reboot` |
| **D-Pad Down** | Safe Shutdown | Sends `DISABLE\n` to release motor coils, executes `sudo shutdown -h now` |

---

## Setup & Execution

### 1. Flash the Arduino
1. Install the `AccelStepper` library in the Arduino IDE (`Sketch -> Include Library -> Manage Libraries`).
2. Open `arduino_control_code/arduino_control_code.ino`.
3. Select board **Arduino Uno**, choose its serial port, and flash the sketch.

### 2. Configure the Raspberry Pi
```bash
cd "Raspberry pi code"

# Ensure Flask template directory structure exists
mkdir -p templates
cp index.html templates/

# Install dependencies
pip3 install -r requirements.txt

# Make scripts executable
chmod +x start.sh stop.sh
```

### 3. Run
```bash
./start.sh
```
The startup script launches `web_gui.py` and `picar_controller_integrated.py` in background processes, logs outputs to `logs/`, and outputs your local IP address:
```
Open in browser: http://<pi-ip-address>:5000
```

To stop all processes cleanly:
```bash
./stop.sh
```

---

## Engineering Trade-offs

- **Stepper Motors over DC Motors with Encoders:**
  Stepper motors provide deterministic open-loop angular displacement at low speeds without needing an encoder read loop or PID tuning. The trade-off is higher continuous power consumption (steppers draw holding current continuously) and a hard limit on top speed before torque collapses.
- **Hardware Step Generation vs. Raspberry Pi GPIO:**
  Generating 4 concurrent microsecond pulse trains in user-space Linux causes severe step jitter due to OS task scheduling. Offloading step generation to the Arduino Uno (`AccelStepper`) isolates real-time pulse timing from network and camera workloads.
- **Software Acceleration Ramping (`RAMP = 0.05`):**
  Stepper motors cannot handle instantaneous velocity step jumps without stalling. An exponential filter (`current += (target - current) * RAMP`) inside the Arduino `loop()` buffers raw joystick inputs before setting motor speeds.
- **File-Based Path Recording (`path_main.txt`, `path_extra.txt`):**
  Movement sequences are logged directly as comma-separated step velocities sampled every 50ms. Playback runs the queue forward or reversed, and manual corrections made after reaching a point are stored in `path_extra.txt` to unwind drift before the next playback run.

---

## Known Limitations & Edge Cases

1. **Dead-Reckoning Drift:** Because path replay and the canvas visualizer rely strictly on open-loop motor commands without wheel encoders or an IMU, physical drift accumulates over time from wheel slippage, carpet resistance, and battery voltage fluctuation. Calibration sliders (Rotation Calibration and Turn Speed) in the web UI must be adjusted manually to match your floor surface.
2. **Template Directory Structure:** Flask's `render_template('index.html')` expects `index.html` inside a `templates/` folder. The provided `start.sh` will fail if `templates/index.html` does not exist.
3. **Serial Port Discovery:** `find_arduino()` in `picar_controller_integrated.py` matches any port containing `USB` or `ACM`. If multiple USB serial devices are connected to the Pi, it may bind to the wrong interface. Hardcode the port name (e.g. `/dev/ttyACM0`) if conflicts occur.
4. **Motor Coil Heating:** Stepper drivers keep coils energized while stationary unless `DISABLE\n` is sent (D-Pad Down). Ensure A4988/DRV8825 current limit pots (VREF) are calibrated before extended bench testing to avoid thermal shutdown.


