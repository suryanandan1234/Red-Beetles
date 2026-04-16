import serial
import serial.tools.list_ports
import pygame
import time
import os
import sys
import threading
from socketio import SimpleClient

# --- CONFIG ---
BAUD_RATE = 115200
MAX_SPEED = 850          
STEER_SENSITIVITY = 0.6  
MAIN_PATH = "path_main.txt"
EXTRA_PATH = "path_extra.txt"
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Web GUI connection
gui_client = None
gui_connected = False

def connect_to_gui():
    """Connect to web GUI server for real-time updates"""
    global gui_client, gui_connected
    try:
        gui_client = SimpleClient()
        gui_client.connect('http://localhost:5000')
        gui_connected = True
        print("Connected to Web GUI")
    except Exception as e:
        print(f"Web GUI not available: {e}")
        gui_connected = False

def send_gui_update(data):
    """Send motor state update to web GUI"""
    global gui_client, gui_connected
    if gui_connected and gui_client:
        try:
            gui_client.emit('update_motor_state', data)
        except:
            gui_connected = False

def send_point_marker(point_name):
    """Mark A or B point in GUI"""
    global gui_client, gui_connected
    if gui_connected and gui_client:
        try:
            gui_client.emit('mark_point', {'point': point_name})
        except:
            pass

def send_reset_signal():
    """Tell GUI to reset path and position"""
    global gui_client, gui_connected
    if gui_connected and gui_client:
        try:
            gui_client.emit('reset_all', {})
        except:
            pass

def find_arduino():
    for p in serial.tools.list_ports.comports():
        if any(x in p.description or x in p.device for x in ['USB', 'ACM']):
            return p.device
    return None

# 1. INITIALIZE ARDUINO
port = find_arduino()
if not port:
    print("Error: No Arduino found.")
    sys.exit()
ser = serial.Serial(port, BAUD_RATE, timeout=0.01)

# 2. WAIT FOR CONTROLLER
pygame.init()
pygame.joystick.init()

print("Waiting for controller...")
while pygame.joystick.get_count() == 0:
    pygame.joystick.quit()
    pygame.joystick.init()
    time.sleep(1)

js = pygame.joystick.Joystick(0)
js.init()
print(f"Controller Connected: {js.get_name()}")

# 3. CONNECT TO WEB GUI (non-blocking)
threading.Thread(target=connect_to_gui, daemon=True).start()

# --- STATE VARIABLES ---
STATE = "IDLE" 
playback_queue = []
at_point = "A" 
halted = False 

def clear_files(all=True):
    files = [MAIN_PATH, EXTRA_PATH] if all else [EXTRA_PATH]
    for f_name in files:
        if os.path.exists(f_name):
            os.remove(f_name)
        open(f_name, 'w').close()

def save_move(f_name, l, r):
    with open(f_name, 'a') as f:
        f.write(f"{l},{r}\n")

def load_path(f_name, reverse=False):
    data = []
    if os.path.exists(f_name):
        with open(f_name, 'r') as f:
            for line in f:
                if "," in line:
                    parts = line.strip().split(',')
                    data.append((int(parts[0]), int(parts[1])))
    return data[::-1] if reverse else data

print("\n--- SYSTEM READY ---")
print("A/B: Points | Y: Reset All | D-Pad: L=Restart, R=Unused, U=Reboot, D=Shutdown")
print("Web GUI: http://localhost:5000 (or http://<pi-ip>:5000)")

try:
    clear_files(all=True)
    while True:
        pygame.event.pump()
        
        btn_a = js.get_button(0)  # A button
        btn_b = js.get_button(1)  # B button
        btn_y = js.get_button(3)  # Y button
        hat = js.get_hat(0)

        # 1. DPAD SYSTEM COMMANDS
        if hat != (0, 0):
            if hat == (-1, 0):  # D-Pad Left: RESTART CODE
                print(">>> RESTARTING CODE...")
                ser.write(b"0,0\n")
                time.sleep(0.1)
                os.execv(sys.executable, ['python3'] + sys.argv)
            
            elif hat == (1, 0):  # D-Pad Right: UNUSED
                pass

            elif hat == (0, 1):  # D-Pad Up: REBOOT
                print("!!! REBOOTING !!!")
                os.system("sudo reboot")
                sys.exit()

            elif hat == (0, -1):  # D-Pad Down: SHUTDOWN
                print("!!! SHUTTING DOWN !!!")
                ser.write(b"DISABLE\n")
                os.system("sudo shutdown -h now")
                sys.exit()

        # 2. RESET ALL (Y Button) - Clear tracking, points, reset position to 0,0
        if btn_y:
            halted = False
            STATE = "IDLE"
            at_point = "A"
            clear_files(all=True)
            print(">>> FULL RESET: Cleared path tracking, removed points, reset to origin.")
            ser.write(b"0,0\n")
            send_reset_signal()  # Tell GUI to reset everything
            time.sleep(0.5)
            continue

        if halted:
            continue

        l, r, auto_mode = 0, 0, False

        # 3. RECORDING / NAVIGATION LOGIC
        if STATE == "IDLE" and btn_a:
            STATE = "RECORDING_TO_B"
            at_point = "A"
            clear_files(all=True)
            print(">>> Point A marked. Recording to B...")
            send_point_marker("A")
            time.sleep(0.5)

        elif STATE == "RECORDING_TO_B" and btn_b:
            STATE = "AT_POINT"
            at_point = "B"
            clear_files(all=False)  # Clear only extra movements
            print(">>> Point B marked. Ready to navigate.")
            send_point_marker("B")
            time.sleep(0.5)

        elif STATE == "AT_POINT":
            if btn_a and at_point != "A":
                # Go back to A: undo extra movements, then reverse main path
                extra = load_path(EXTRA_PATH, reverse=True)
                undo_extra = [(-x, -y) for x, y in extra]
                main_rev = load_path(MAIN_PATH, reverse=True)
                undo_main = [(-x, -y) for x, y in main_rev]
                playback_queue = undo_extra + undo_main
                STATE = "AUTO_PILOT"
                at_point = "A"
                print(">>> Navigating to A...")
                time.sleep(0.5)
            
            elif btn_a and at_point == "A":
                # Already at A, just undo any extra movements
                extra = load_path(EXTRA_PATH, reverse=True)
                if extra:
                    undo_extra = [(-x, -y) for x, y in extra]
                    playback_queue = undo_extra
                    STATE = "AUTO_PILOT"
                    print(">>> Returning to exact A position...")
                    time.sleep(0.5)
            
            elif btn_b and at_point != "B":
                # Go to B: undo extra movements, then follow main path
                extra = load_path(EXTRA_PATH, reverse=True)
                undo_extra = [(-x, -y) for x, y in extra]
                main_fwd = load_path(MAIN_PATH, reverse=False)
                playback_queue = undo_extra + main_fwd
                STATE = "AUTO_PILOT"
                at_point = "B"
                print(">>> Navigating to B...")
                time.sleep(0.5)
            
            elif btn_b and at_point == "B":
                # Already at B, just undo any extra movements
                extra = load_path(EXTRA_PATH, reverse=True)
                if extra:
                    undo_extra = [(-x, -y) for x, y in extra]
                    playback_queue = undo_extra
                    STATE = "AUTO_PILOT"
                    print(">>> Returning to exact B position...")
                    time.sleep(0.5)

        # 4. AUTO-DRIVE EXECUTION
        if STATE == "AUTO_PILOT":
            if playback_queue:
                l, r = playback_queue.pop(0)
                auto_mode = True
            else:
                STATE = "AT_POINT"
                clear_files(all=False)  # Clear extra movements after arriving
                print(f">>> Arrived at {at_point}.")
                ser.write(b"0,0\n")

        # 5. MANUAL DRIVE
        if not auto_mode:
            stk_thr = -js.get_axis(1)
            trig_thr = ((js.get_axis(5)+1)/2.0) - ((js.get_axis(2)+1)/2.0)
            throttle = stk_thr if abs(stk_thr) > abs(trig_thr) else trig_thr
            steering = js.get_axis(0) if abs(js.get_axis(0)) > abs(js.get_axis(3)) else js.get_axis(3)

            if abs(throttle) < 0.15: throttle = 0
            if abs(steering) < 0.15: steering = 0

            l = int(max(min(throttle + (steering * STEER_SENSITIVITY), 1), -1) * MAX_SPEED)
            r = int(max(min(throttle - (steering * STEER_SENSITIVITY), 1), -1) * MAX_SPEED)

            # Record movements based on state
            if STATE == "RECORDING_TO_B":
                save_move(MAIN_PATH, l, r)
            elif STATE == "AT_POINT" and (l != 0 or r != 0):
                save_move(EXTRA_PATH, l, r)

        # 6. SEND TO ARDUINO & GUI
        ser.write(f"{l},{r}\n".encode('utf-8'))
        
        # Update web GUI
        send_gui_update({
            'mode': STATE,
            'at_point': at_point,
            'halted': halted,
            'left_motor': l,
            'right_motor': r
        })
        
        time.sleep(0.05)

except KeyboardInterrupt:
    ser.write(b"0,0\n")
    pygame.quit()
    if gui_connected and gui_client:
        gui_client.disconnect()
