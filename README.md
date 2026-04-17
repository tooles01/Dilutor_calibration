# Flow Sensor Diagnostics

PyQt5 application for calibration of Honeywell 3000/5000 series flow sensors via serial communication with an Arduino.

---

## Overview

`flow_sensor_diagnostics.py` provides a graphical interface for:
- Connecting to a Honeywell flow sensor over a serial (COM) port
- Reading and displaying live flow sensor data
- Creating and managing calibration tables
- Running timed calibration sessions and saving results to file

This is a modified standalone version of `flow_sensor_driver.py` ([OlfaControl_GUI](https://github.com/tooles01/OlfaControl_GUI/tree/shannon-branch)), with utility
functions copied in so it can run independently.

---

## Hardware Requirements

- **Flow Sensor:** Honeywell 3000/5000 series (e.g., 3100V, 3300V, 5100V)
- **Microcontroller:** Arduino (running `readHoneywell5100V.ino`)
- **Connection:** USB serial connection to the Arduino

---

## Software Requirements

**Python version:** Python 3.x

**Dependencies:**

| Package    | Purpose                              |
|------------|--------------------------------------|
| `PyQt5`    | GUI framework and serial port comms  |
| `pyserial` | Serial port listing                  |
| `numpy`    | Statistical analysis of calibration data |

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

### 3. Set up calibration tables
Create a folder called `calibration_tables` in the same directory as the script.
Place any existing `.txt` calibration files inside it.
The application will create this folder automatically if it does not exist.

### 4. Upload the Arduino sketch
Upload `readHoneywell5100V.ino` to your Arduino before connecting.

### 5. Run the application
```bash
python flow_sensor_diagnostics.py
```

---

## Usage

### Connecting to a Sensor
1. Plug in your Arduino via USB
2. Click **Refresh** to scan for available COM ports
3. Select the correct port from the dropdown
4. Click **Connect**

### Reading Live Data
Once connected, incoming flow sensor values will appear in the
**Data Received** panel, displaying both raw integer values and
converted SCCM values.

### Selecting a Calibration Table
1. Select a calibration table from the **Calibration Table** panel
2. Click **Set Calibration Table** to apply it

### Running a New Calibration
1. Connect to the sensor
2. In the **New Calibration** panel, enter:
   - **File name** for the new calibration table
   - **Duration (s):** how long to collect data per setpoint
   - **MFC value (SCCM):** the known flow rate being applied
3. Click **Create File** to initialize a new `.csv` calibration file
4. Click **Start** to begin collecting values
5. Review the statistics (median, mean, range) after collection ends
6. Click **Write to File** to save the result
7. Repeat for each flow setpoint
8. Click **End & Save File** when finished

---

## Calibration Table Format

Calibration files are `.txt` files (CSV format) stored in the
`calibration_tables/` directory.

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

## File Structure

```
flow-sensor-diagnostics/
│
├── flow_sensor_diagnostics.py    # Main application
├── readHoneywell5100V.ino        # Arduino sketch (upload to Arduino)
├── calibration_tables/           # Folder for calibration .txt files
│   ├── Honeywell_3100V.txt
│   └── Honeywell_3300V.txt
└── README.md
```

---

## Known Limitations

- Calibration files must use `.txt` extension
- File path separators use `\\` which may cause issues on macOS/Linux