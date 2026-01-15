import time
import threading
import random
import math
import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Hardware imports (wrapped in try-except for dev environment compatibility)
try:
    import serial
    import smbus
    import RPi.GPIO as GPIO
    hardware_available = True
except ImportError:
    hardware_available = False
    print("Hardware libraries not found. Running in MOCK MODE.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

bus = None
if hardware_available:
    try:
        bus = smbus.SMBus(1)
    except:
        pass

thread = None
thread_lock = threading.Lock()
data_counter = 0

# Trackers to prevent redundant spam
last_ax = 0
last_ay = 0
last_vibration = 0
last_emit_time = 0

# =========================
# CONFIGURATION
# =========================
ALERT_NUMBER = "+254743894130"
TILT_THRESHOLD = 1.5
VIBRATION_PIN = 17
IMU_ADDR = 0x68

# =========================
# HARDWARE HELPERS
# =========================
def read_raw_data(addr):
    if not bus: return 0
    try:
        high = bus.read_byte_data(IMU_ADDR, addr)
        low = bus.read_byte_data(IMU_ADDR, addr+1)
        value = ((high << 8) | low)
        if(value > 32768):
            value = value - 65536
        return value
    except:
        return 0

def read_imu():
    if not hardware_available: return 0.0, 0.0
    acc_x = read_raw_data(0x3B)
    acc_y = read_raw_data(0x3D)
    return acc_x / 16384.0, acc_y / 16384.0

def get_gsm_location():
    return -1.286389, 36.817223

def init_hardware():
    global hardware_available, bus
    if not hardware_available: return False
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(VIBRATION_PIN, GPIO.IN)
        if bus: bus.write_byte_data(IMU_ADDR, 0x6B, 0)
        return True
    except Exception as e:
        print(f"Hardware initialization failed: {e}")
        return False

# =========================
# BACKGROUND MONITORING
# =========================
def sensor_loop():
    print("Monitoring thread started...")
    global data_counter, last_ax, last_ay, last_vibration, last_emit_time
    is_hw_active = init_hardware()
    
    # Simulation state
    sim_ax = 0.0
    sim_ay = 0.0

    while True:
        try:
            if not is_hw_active:
                # If hardware isn't active, don't simulate. 
                # Just wait and try to re-init occasionally or stay idle.
                socketio.emit('sensor_data', {
                    'mode': 'OFFLINE',
                    'id': -1,
                    'ax': 0, 'ay': 0, 'vibration': 0,
                    'lat': 0, 'lon': 0,
                    'timestamp': time.strftime("%H:%M:%S"),
                    'gforce': 0, 'alert': False
                })
                socketio.sleep(5)
                is_hw_active = init_hardware()
                continue

            # Real Hardware Logic
            try:
                vibration = 1 if GPIO.input(VIBRATION_PIN) else 0
                ax, ay = read_imu()
            except Exception as e:
                print(f"Hardware Reading Error: {e}")
                is_hw_active = False
                continue

            mode = "HARDWARE"
            time_now = time.time()
            
            # Check for significant change or heartbeat (2 seconds)
            significant_change = (
                abs(ax - last_ax) > 0.05 or 
                abs(ay - last_ay) > 0.05 or 
                vibration != last_vibration or
                (time_now - last_emit_time) > 2.0
            )

            if significant_change:
                data_counter += 1
                lat, lon = get_gsm_location()
                
                payload = {
                    'id': data_counter,
                    'ax': round(ax, 2),
                    'ay': round(ay, 2),
                    'vibration': vibration,
                    'lat': lat,
                    'lon': lon,
                    'timestamp': time.strftime("%H:%M:%S") + ":" + str(int(time_now * 1000) % 1000).zfill(3),
                    'mode': mode,
                    'gforce': round(math.sqrt(ax**2 + ay**2), 2),
                    'alert': (vibration == 1 or abs(ax) > TILT_THRESHOLD or abs(ay) > TILT_THRESHOLD)
                }
                
                # CRITICAL: We broadcast=True here but manually check for duplicates on frontend
                # Using a slightly slower 1Hz update for stability
                socketio.emit('sensor_data', payload)
                last_ax, last_ay, last_vibration = ax, ay, vibration
                last_emit_time = time_now
            
            socketio.sleep(1.0) # Slow, stable 1Hz updates
            
        except Exception as e:
            print(f"Loop Error: {e}")
            socketio.sleep(2)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None or not thread.is_alive():
            print("Client connected. Starting SINGLE background monitoring thread...")
            # Use 'threading' instead of 'socketio.start_background_task' 
            # for more explicit process control
            thread = threading.Thread(target=sensor_loop, daemon=True)
            thread.start()

if __name__ == '__main__':
    # Force single-threaded mode in debug to stop recursion
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False)
