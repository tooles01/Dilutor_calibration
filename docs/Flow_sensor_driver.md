# Flow Sensor Driver

PyQt5 app for calibrating Honeywell 3000/5000 series flow sensors via Arduino.

** to be edited **

---

## Usage

1. Plug in Teensy via USB
2. Click **Refresh** → select COM port → click **Connect**
3. Live sensor values will appear in the **Data Received** panel

### Calibration

1. Connect to the sensor
2. In the **New Calibration** panel, enter:
   - **File name** for the new calibration table
   - **Duration (s):** how long to collect data per setpoint
   - **MFC value (SCCM):** the known flow rate being applied
3. Click **Create File** to create a new `.csv` calibration file
4. Click **Start** to begin collecting values
5. When the timer ends, Click **Write to File** to save the result
6. Repeat for each flow setpoint
7. Click **End & Save File** when done

Calibration files are saved as `.csv` in `/calibration_tables/`.

## Known Limitations

- Calibration files must use `.txt` extension
- File paths may cause issues on macOS/Linux