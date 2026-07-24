# Flow Sensor Driver

PyQt5 app for calibrating Honeywell 3000/5000 series flow sensors via Arduino.

---

## Setup

### Hardware Requirements:
- Honeywell 3000/5000 flow sensor
- Arduino/Teensy running `read_flow_sensor.ino`
- 8-12V power supply

### Software Installation:
1. Open the command prompt and navigate to the directory you want this to be in 
2. Clone the repository and navigate into it

   ```bash
   git clone https://github.com/tooles01/Dilutor_calibration.git
   cd Dilutor_calibration
   ```

3. Create & activate a virtual environment
   ```bash
   python -m venv <environment_name>
   environment_name\scripts\activate.bat
4. Install dependencies
   ```bash
   pip install PyQt5 pyserial numpy pyqtgraph
   ```

5. Run the application
   ```bash
   python run_olfa.py
   ```
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