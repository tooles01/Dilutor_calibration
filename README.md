# Flow Sensor Diagnostics

PyQt5 application for calibration of Honeywell 3000/5000 series flow sensors via serial communication with an Arduino.

---

## Overview

`flow_sensor_diagnostics.py` provides a graphical interface for:
- Connecting to a Honeywell flow sensor over a serial (COM) port
- Reading and displaying live flow sensor data
- Running timed calibration sessions and saving results to file

This is a modified standalone version of `flow_sensor_driver.py` ([OlfaControl_GUI](https://github.com/tooles01/OlfaControl_GUI/tree/shannon-branch)), with utility
functions copied in so it can run independently.

---

## Hardware Requirements

- **Flow Sensor:** Honeywell 3000/5000 series
- **Arduino:** Running `readHoneywell5100V.ino`
- **Power/Wiring**: 8-12V power for flow sensor, wiring between flow sensor and Arduino

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/tooles01/Dilutor_calibration.git
cd flow-sensor-diagnostics
```

### 2. Install dependencies
```bash
pip install PyQt5 pyserial numpy
```
### 3. Run the application
```bash
python flow_sensor_diagnostics.py
```

---

## Usage

### Connect to Flow Sensor
1. Plug in your Arduino via USB
2. Click **Refresh** to scan for available COM ports
3. Select the correct port from the dropdown
4. Click **Connect**

### Reading Live Data
Once connected, incoming flow sensor values will appear in the
**Data Received** panel, displaying raw integer values.

### Running a New Calibration
1. Connect to the sensor
2. In the **New Calibration** panel, enter:
   - **File name** for the new calibration table
   - **Duration (s):** how long to collect data per setpoint
   - **MFC value (SCCM):** the known flow rate being applied
3. Click **Create File** to initialize a new `.csv` calibration file
4. Click **Start** to begin collecting values
5. Click **Write to File** to save the result
6. Repeat for each flow setpoint
7. Click **End & Save File** when finished

---

## Calibration Table Format

Calibration files are `.csv` files stored to the `/calibration_tables/` directory within your current folder.

**Expected format:**
```
Honeywell_3100V, 12:00:00.000
SCCM, int
1000, 950.2
900, 855.4
800, 760.1
...
```

---

## Known Limitations

- Calibration files must use `.txt` extension
- File path separators use `\\` which may cause issues on macOS/Linux