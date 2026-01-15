# SENSE-X | Raspberry Pi Hardware Connection Guide

This guide explains how to connect your physical sensors to the Raspberry Pi to work with the SENSE-X Dashboard.

## 1. Required Hardware
*   **Raspberry Pi** (3, 4, or 5)
*   **MPU6050** (Accelerometer & Gyroscope)
*   **SW-420** (Vibration Sensor)
*   **Female-to-Female Jumper Wires**

---

## 2. Pinout Diagram (Connections)

### MPU6050 (Orientation)
The MPU6050 uses the **I2C Protocol**.
| MPU6050 Pin | Raspberry Pi Pin | Physical Pin # |
| :--- | :--- | :--- |
| **VCC** | 3.3V | Pin 1 |
| **GND** | Ground | Pin 6 |
| **SCL** | I2C SCL (GPIO 3) | Pin 5 |
| **SDA** | I2C SDA (GPIO 2) | Pin 3 |

### SW-420 (Vibration)
| SW-420 Pin | Raspberry Pi Pin | Physical Pin # |
| :--- | :--- | :--- |
| **VCC** | 3.3V or 5V | Pin 1 or 2 |
| **GND** | Ground | Pin 9 or 14 |
| **D0 (Signal)** | GPIO 17 | Pin 11 |

---

## 3. Raspberry Pi Software Setup

### Enable I2C Interface
1. Run `sudo raspi-config`
2. Go to **Interface Options** -> **I2C**
3. Select **Yes** to enable it.
4. Reboot the Pi: `sudo reboot`

### Install Required Hardware Libraries
Run these commands on your Pi terminal:
```bash
sudo apt-get update
sudo apt-get install -y python3-smbus i2c-tools python3-rpi.gpio
```

### Verify Connection
Check if the MPU6050 is detected at address `0x68`:
```bash
i2cdetect -y 1
```
*You should see "68" in the table.*

---

## 4. Running the Dashboard on Pi
1. Clone your project to the Pi.
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate`
4. Install requirements: `pip install flask flask-socketio eventlet pyserial smbus RPi.GPIO`
5. Run: `python app.py`

## 5. Troubleshooting
*   **Mode staying OFFLINE:** Check your `SDA/SCL` wiring. If the Pi cannot find the MPU6050 at `0x68`, the dashboard will stay in Offline mode.
*   **No Vibration:** Adjust the small potentiometer (screw) on the SW-420 sensor to change the sensitivity.
*   **I2C Error:** Ensure no other process is using the I2C bus.
