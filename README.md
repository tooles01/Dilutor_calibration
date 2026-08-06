# Dilutor calibration

PyQt5 app for calibrating dilutors using Honeywell 3000/5000 series flow sensors

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
   python run_calibration.py
   ```

---

## Calibrating

Follow calibration procedure found [here](docs/Calibration_procedure.md)