# 🏎️ Red-Beetle: Autonomous & Teleoperated 4WD Robotic Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Arduino](https://img.shields.io/badge/Arduino-Compatible-00979D.svg?logo=arduino&logoColor=white)](https://www.arduino.cc/)
[![Raspberry Pi](https://img.shields.io/badge/Platform-Raspberry%20Pi-C51A4A.svg?logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)
[![Flask](https://img.shields.io/badge/Web%20GUI-Flask%20%2B%20Socket.IO-000000.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/Vision-OpenCV-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)

**Red-Beetle** is an open-source, dual-tiered 4-wheel-drive (4WD) robotic rover combining the precision of stepper-motor skid steering with high-level onboard intelligence. Powered by a **Raspberry Pi** supervisory computer and an **Arduino Uno CNC Shield** motion controller, Red-Beetle delivers real-time joystick teleoperation, path recording with autonomous A-to-B dead-reckoning playback, low-latency live camera streaming, and a futuristic glassmorphic Web Telemetry GUI.

---

## 📸 System Architecture

```
                                  +-----------------------+
                                  |    User Gamepad       |
                                  | (USB / Bluetooth / RF)|
                                  +-----------+-----------+
                                              |
                                              v (Pygame Events)
+------------------------+        +-----------+-----------+        +------------------------+
|  Web Browser Client    | <----> |     Raspberry Pi      | ---->  |   USB / CSI Camera     |
| (Live Stream + Canvas) | Socket |  (Supervisory Node)   | OpenCV | (640x480 @ 30 FPS)     |
+------------------------+   IO   +-----------+-----------+        +------------------------+
                                              |
                                              | USB Serial (115200 Baud)
                                              v
                                  +-----------+-----------+
                                  |   Arduino CNC Shield  |
                                  |  (AccelStepper Core)  |
                                  +-----------+-----------+
                                              |
                   +-------------+------------+------------+-------------+
                   |             |                         |             |
                   v             v                         v             v
             [Front-Right]  [Back-Right]              [Front-Left]  [Back-Left]
             Stepper Motor  Stepper Motor             Stepper Motor Stepper Motor
```

---

## ✨ Key Features

- **🎯 Precision Stepper Skid-Steer (4WD):** Uses 4 independent stepper motors driven by A4988/DRV8825 drivers on a CNC Shield v3 with smooth acceleration ramping (`AccelStepper`).
- **🎮 Gamepad Teleoperation:** Low-latency dual-analog thumbstick and trigger controls (tank/differential steering mix) with deadzone compensation via Pygame.
- **🔄 A-to-B Path Recording & Auto-Pilot Replay:**
  - Mark **Point A** and drive freely to **Point B**; the system records every movement delta.
  - Mark **Point B** to lock the trajectory.
  - Trigger one-touch autonomous navigation back to A or back to B with cumulative drift compensation (`path_extra.txt`).
- **🌐 Glassmorphic Real-Time Web Telemetry:**
  - Modern, responsive cyber-themed dark UI built with HTML5 Canvas, CSS Backdrop-Filter, and WebSockets (`Socket.IO`).
  - **Live Odometry Visualizer:** Shows the rover’s calculated 2D coordinates, heading angle, animated direction arrow, and breadcrumb path trail.
  - **Live MJPEG Video Stream:** Real-time video feed piped directly from onboard camera via OpenCV.
  - **Interactive Calibration:** Sliders for rotation sensitivity, dead-reckoning scaling, and canvas zoom with persistent JSON storage.
- **🛡️ Built-in System Recovery & Power Management:**
  - D-Pad triggers for instant script restarts, system reboots, and safe shutdown with motor torque disable.
  - Automated bash lifecycle scripts (`start.sh`, `stop.sh`) with dependency checking and process monitoring.
- **🛠️ 3D CAD Enclosure & Custom Wheels:** Includes native Autodesk Fusion 360 (`.f3d`) design models for the custom chassis assembly and traction wheels.

---

## 🧰 Hardware Requirements & Pinout

### 1. Hardware Bill of Materials (BOM)
| Component | Description |
| :--- | :--- |
| **High-Level Computer** | Raspberry Pi 4B / 3B+ (Running Raspberry Pi OS) |
| **Low-Level Controller** | Arduino Uno R3 with **CNC Shield V3** |
| **Stepper Drivers** | 4x A4988 or DRV8825 stepper motor drivers |
| **Motors** | 4x NEMA 17 (or compatible) stepper motors |
| **Camera** | USB Web Camera or Raspberry Pi Camera (V4L2) |
| **Controller** | Xbox, PlayStation, or generic USB/Bluetooth Gamepad |
| **Power Supply** | Dual power: 12V LiPo/DC for motors + 5V/3A Power Bank for Raspberry Pi |
| **Chassis & Wheels** | 3D printed components from `Next Gen.f3d` & `GIC wheels.f3d` |

### 2. CNC Shield v3 Pin Mapping (Arduino Uno)
| Motor Channel | Axis on Shield | Step Pin | Direction Pin | Role |
| :--- | :---: | :---: | :---: | :--- |
| **Motor FR** | X | `Pin 2` | `Pin 5` | Front Right Wheel |
| **Motor BR** | Y | `Pin 3` | `Pin 6` | Back Right Wheel |
| **Motor FL** | Z | `Pin 4` | `Pin 7` | Front Left Wheel |
| **Motor BL** | A | `Pin 12` | `Pin 13` | Back Left Wheel |
| **Enable Pin** | EN | `Pin 8` | — | Stepper Enable (Active LOW) |

---

## 🎮 Gamepad Controls Cheat Sheet

| Input | Action | Description |
| :---: | :--- | :--- |
| **Left Stick (Y-axis)** / **Triggers** | **Throttle** | Forward / Reverse drive |
| **Right Stick (X-axis)** | **Steering** | Differential / Tank steering (Left / Right) |
| **Button A** | **Mark Point A / Navigate to A** | Sets origin; in Auto-Pilot returns to Point A |
| **Button B** | **Mark Point B / Navigate to B** | Sets destination; in Auto-Pilot navigates to Point B |
| **Button Y** | **Full System Reset** | Clears path memory, resets position to (0,0), stops motors |
| **D-Pad Left** | **Restart Software** | Restarts Python controller process |
| **D-Pad Up** | **Reboot System** | Triggers `sudo reboot` on Raspberry Pi |
| **D-Pad Down** | **Safe Shutdown** | Disables motor coils and executes `sudo shutdown -h now` |

---

## 📁 Repository Structure

```text
Red-Beetles/
├── GIC wheels.f3d                 # Autodesk Fusion 360 CAD model for wheels
├── Next Gen.f3d                   # Autodesk Fusion 360 CAD model for chassis
├── README.md                      # Project documentation
│
├── arduino_control_code/
│   └── arduino_control_code.ino   # Arduino firmware (AccelStepper, serial protocol)
│
└── Raspberry pi code/
    ├── index.html                 # Modern Glassmorphic Web Dashboard
    ├── picar_controller_integrated.py # Gamepad reader, state machine & path recorder
    ├── web_gui.py                 # Flask + Socket.IO server & OpenCV streamer
    ├── requirements.txt           # Python dependencies
    ├── start.sh                   # System launcher with self-test & monitoring
    └── stop.sh                    # Graceful shutdown script
```

---

## 🚀 Getting Started

### Step 1: Flash the Arduino Firmware
1. Open the Arduino IDE.
2. Install the **AccelStepper** library:
   - Go to `Sketch` -> `Include Library` -> `Manage Libraries...`
   - Search for `AccelStepper` by Mike McCauley and click **Install**.
3. Open `arduino_control_code/arduino_control_code.ino`.
4. Connect the Arduino Uno via USB, select your board and COM port, and click **Upload**.

> [!NOTE]
> Ensure all microstepping jumpers beneath the A4988/DRV8825 drivers on your CNC shield are configured consistently (e.g., 1/16 microstepping recommended for smooth motion).

---

### Step 2: Raspberry Pi Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/Red-Beetles.git
   cd Red-Beetles/"Raspberry pi code"
   ```

2. **Prepare template directory:**
   Flask looks for `index.html` inside a `templates` folder by default. Create the folder and move or link `index.html`:
   ```bash
   mkdir -p templates
   cp index.html templates/
   ```

3. **Install Python Dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```
   *(Or let `start.sh` install missing packages automatically on first boot).*

4. **Grant Execution Permissions:**
   ```bash
   chmod +x start.sh stop.sh
   ```

---

### Step 3: Launching Red-Beetle

1. Ensure your gamepad is connected and the Arduino is plugged in via USB.
2. Run the startup script:
   ```bash
   ./start.sh
   ```
3. The terminal will display:
   ```text
   ======================================
      Raspberry Pi Car Control System
   ======================================
   ✅ All required files found
   ✅ Dependencies OK
   📡 Network Information:
      Local:   http://localhost:5000
      Network: http://192.168.x.x:5000
   🚀 Starting Web GUI Server...
   🎮 Starting Car Controller...
   🎉 SYSTEM READY!
   ```
4. Open `http://<your-pi-ip>:5000` in any web browser on your phone, tablet, or laptop connected to the same Wi-Fi network.

### Step 4: Stopping the System
Press `Ctrl+C` in the running terminal, or run:
```bash
./stop.sh
```

---

## ⚙️ Software Architecture & Communication

### Serial Protocol (Pi ➔ Arduino)
The Raspberry Pi sends ASCII packets over Serial (`115200` baud) every 50ms:
- `targetL,targetR\n`: Floating point motor velocities for left and right tracks (e.g., `450,-450\n`).
- `DISABLE\n`: Pulls CNC Shield `ENABLE_PIN` (Pin 8) HIGH to cut power to motor coils during idle/shutdown to prevent heating.

### Dead-Reckoning & Visual Odometry
`web_gui.py` maintains an internal kinematic model:
```python
avg_speed = (left_speed + right_speed) / 2.0
speed_diff = (right_speed - left_speed)

# Visual heading update
rotation_amount = speed_diff * settings["rotation_calibration"] * settings["turning_speed_multiplier"] * 0.01
current_position["angle"] = (current_position["angle"] + rotation_amount) % 360

# 2D coordinate displacement
movement = avg_speed * 0.05
current_position["x"] += movement * math.cos(math.radians(current_position["angle"]))
current_position["y"] += movement * math.sin(math.radians(current_position["angle"]))
```
Parameters can be tuned dynamically via the UI sliders and are persisted in `gui_settings.json`.

---

## 🗺️ Future Roadmap
- [ ] Closed-loop wheel encoder integration to supplement dead-reckoning with ground-truth odometry.
- [ ] Computer Vision line-tracking and AprilTag visual docking.
- [ ] Autonomous obstacle avoidance via ultrasonic (HC-SR04) or LiDAR sensors.
- [ ] Mobile touch controls embedded in the Web GUI for controller-free teleoperation.

---

## 🤝 Contributing & License
Contributions, issues, and feature requests are welcome! Feel free to open a pull request or submit an issue on GitHub.

This project is licensed under the [MIT License](LICENSE).

