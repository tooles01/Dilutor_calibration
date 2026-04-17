'''
flow_sensor_diagnostics.py

Description:
  Diagnostic and calibration tool for Honeywell 3000/5000 series flow sensors.
  Provides a PyQt5-based GUI for connecting to, reading from, and calibrating
  Honeywell flow sensors via serial communication.

Hardware:
  Compatible with Honeywell 3000/5000 series flow sensors
  Designed for use with Arduino sketch: readHoneywell5100V.ino

Dependencies:
  - PyQt5        : GUI framework and serial port communication
  - pyserial     : Serial port listing (serial.tools.list_ports)
  - numpy        : Statistical analysis of calibration data

Notes:
  - Modified version of flow_sensor_driver.py
  - Utility functions have been copied into this file for standalone operation
  - Calibration tables are stored as .txt files in the 'calibration_tables'
    directory located in the current working directory
  - Baud rate: 9600

Usage:
  Run directly as a standalone application:
      python flow_sensor_diagnostics.py

  Or import the flowSensor class into a parent application:
      from flow_sensor_diagnostics import flowSensor

Author:         Shannon Toole
Created:        4/10/2026
Last Modified:  4/16/2026
'''

import os, sys, logging, csv
from PyQt5 import QtCore, QtSerialPort
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from serial.tools import list_ports
import numpy as np
from datetime import datetime, timedelta


noPortMsg = ' ~ No COM ports detected ~'

flowSens_baud = 9600
cal_table_file_tyoe = '.txt'

def_new_cal_table_name = 'Honeywell_3300V'
default_cal_table = 'Honeywell_3100V'
def_MFC_value = '100'
def_cal_duration = '10'


# Copied functions from utils
currentDate = str(datetime.date(datetime.now()))
calibration_file_dir_name = 'calibration_tables'
def get_current_time():
    current_time = datetime.time(datetime.now())
    current_time_f = current_time.strftime('%H:%M:%S.%f')
    current_time_str = current_time_f[:-3]

    return current_time_str
def create_console_handler():
    '''
    Returns console handler for logger
        Set level to 'DEBUG'
    '''
    
    console_handler_level = logging.DEBUG
    console_handler_formatter = logging.Formatter('%(asctime)s : %(name)-14s :%(levelname)-8s: %(message)s',datefmt='%H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_handler_level)
    console_handler.setFormatter(console_handler_formatter)
    
    return console_handler
def find_calibration_table_directory():
    '''In current directory, check if folder called calibration_tables'''

    current_dir = os.getcwd()
    cal_table_dir = os.path.join(current_dir,'calibration_tables')
    
    # Check if this exists
    if os.path.exists(cal_table_dir):
        logger.debug('Found calibration_tables directory at "%s"', cal_table_dir)
    else:
        logger.warning('Cannot find calibration_tables directory, creating folder within current directory')
        os.mkdir(cal_table_dir)

    return cal_table_dir

# CREATE LOGGER
logger = logging.getLogger(name='flow sensor')
logger.setLevel(logging.DEBUG)
if logger.hasHandlers():    logger.handlers.clear()     # removes duplicate log messages
console_handler = create_console_handler()
logger.addHandler(console_handler)

class flowSensor(QGroupBox):

    def __init__(self, port=""):
        super().__init__()
        self.port = port
        self.connected = False
        self.calibration_on = False

        # look for calibration table directory
        self.sccm2Ard_dicts = {}
        self.ard2Sccm_dicts = {}
        self.flow_cal_dir = find_calibration_table_directory()
        self.get_calibration_tables()
        
        self.generate_ui()
    
    
    # CREATE GUI ELEMENTS
    def generate_ui(self):
        self.create_connect_box()
        self.create_settings_box()
        self.create_cal_table_select_box()
        self.create_new_calibration_box()
        self.create_data_receive_box()

        top_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(self.connect_box)
        col1.addWidget(self.settings_box)
        col1.addWidget(self.cal_table_select_box)
        col2 = QVBoxLayout()
        col2.addWidget(self.data_receive_box)
        top_layout.addLayout(col1)
        top_layout.addLayout(col2)

        self.layout = QVBoxLayout()
        self.layout.addLayout(top_layout)
        self.layout.addWidget(self.new_cal_box)
        self.setLayout(self.layout)
        self.setTitle('Flow Sensor')

        self.connect_box.setMaximumHeight(self.connect_box.sizeHint().height())
        self.new_cal_box.setMaximumHeight(self.new_cal_box.sizeHint().height())
        self.settings_box.setMaximumHeight(self.settings_box.sizeHint().height())
        self.data_receive_box.setFixedWidth(self.data_receive_box.sizeHint().width())

        self.cal_file_name_wid.setMinimumWidth(175)

        self.new_cal_box.setEnabled(False)

    def create_connect_box(self):
        self.connect_box = QGroupBox("Connect")

        self.portLbl = QLabel(text="Port/Device:")
        self.port_widget = QComboBox(currentIndexChanged=self.port_changed)
        self.connect_btn = QPushButton(checkable=True,toggled=self.toggled_connect)
        self.refresh_btn = QPushButton(text="Refresh",clicked=self.get_ports)
        self.get_ports()

        connect_box_layout = QFormLayout()
        connect_box_layout.addRow(self.portLbl,self.port_widget)
        connect_box_layout.addRow(self.refresh_btn,self.connect_btn)
        self.connect_box.setLayout(connect_box_layout)

    def create_settings_box(self):
        self.settings_box = QGroupBox('Settings')
        
        self.timebtreqs_wid = QLineEdit(text='100',returnPressed=lambda:self.send_to_arduino('MM_timebt_' + self.timebtreqs_wid.text()))
        self.timebtreqs_btn = QPushButton(text="Send", clicked=lambda:self.send_to_arduino('MM_timebt_' + self.timebtreqs_wid.text()))
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel(text="Time b/t acquisitions (ms):"))
        layout.addWidget(self.timebtreqs_wid)
        layout.addWidget(self.timebtreqs_btn)
        self.settings_box.setLayout(layout)

    def create_cal_table_select_box(self):
        self.cal_table_select_box = QGroupBox('Calibration table')
        
        self.cal_table_widget = QListWidget()
        self.cal_table_widget.addItems(self.sccm2Ard_dicts)

        # Get list of all calibration tables currently in the widget
        item_list_str = [self.cal_table_widget.item(x).text() for x in range(self.cal_table_widget.count())]

        if item_list_str != []: # if there are any calibration tables
            # Check if default calibration table is there
            if default_cal_table in item_list_str:
                index_default_cal_table = item_list_str.index(default_cal_table)                # Get the index of this table
                default_cal_table_item = self.cal_table_widget.item(index_default_cal_table)    # Get the item at this index
            else:
                default_cal_table_item = self.cal_table_widget.item(0)
            
            # Set calibration table
            try:
                self.cal_table_widget.setCurrentItem(default_cal_table_item)
                logger.debug('Calibration table set to %s', default_cal_table_item.text())
            except AttributeError:
                pass
            
        self.cal_table_btn = QPushButton('Set calibration table',checkable=True,toggled=self.cal_tbl_btn_toggled)
        if item_list_str != []:
            if self.cal_table_btn.isChecked() == False:
                self.cal_table_btn.setChecked(True)
        else:
            self.cal_table_btn.setEnabled(False)    # If no tables, disable the button
        
        # LAYOUT
        layout = QVBoxLayout()
        layout.addWidget(self.cal_table_widget)
        layout.addWidget(self.cal_table_btn)
        self.cal_table_select_box.setLayout(layout)
    
    def create_new_calibration_box(self):
        self.new_cal_box = QGroupBox('New calibration')
        
        # File name/Directory
        cal_file_name = def_new_cal_table_name + '_' + currentDate
        self.cal_file_dir_wid = QLineEdit(text=self.flow_cal_dir)
        self.cal_file_name_wid = QLineEdit(text=cal_file_name)

        # MFC value (SCCM)
        self.mfc_value_wid = QLineEdit(text=def_MFC_value)
        self.mfc_value_wid.returnPressed.connect(lambda: self.start_calibration_btn.toggle())
        
        # Create new file / Start
        self.create_new_cal_file_btn = QPushButton(text='Create file',checkable=True)
        self.create_new_cal_file_btn.toggled.connect(self.create_new_cal_file_toggled)
        self.start_calibration_btn = QPushButton(text='Start',checkable=True,toggled=self.start_calibration)
        
        # Widget for calibration duration (& timer for visual)
        self.cal_duration_wid = QLineEdit(text=def_cal_duration)
        self.cal_duration_wid.setToolTip('Max 99 seconds')
        self.cal_duration_wid.returnPressed.connect(lambda: self.start_calibration_btn.toggle())
        self.calibration_duration_timer = QTimer()
        self.calibration_duration_timer.setTimerType(0)     # set to millisecond accuracy
        self.calibration_duration_timer.timeout.connect(self.show_cal_duration_time)
        self.calibration_duration_label = QLabel('000.00')

        # Collected values
        self.collected_values_lbl = QLabel('Collected Values:')
        self.collected_values_wid = QTextEdit()
        self.collected_values_wid.setToolTip('Values collected during calibration at this flow rate')
        layout_collected_vals = QVBoxLayout()
        layout_collected_vals.addWidget(self.collected_values_lbl)
        layout_collected_vals.addWidget(self.collected_values_wid)

        # Calibration results
        self.cal_results_min_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_max_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_med_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_mean_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_range_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_num_wid = QLineEdit(readOnly=True,maximumWidth=40)
        self.cal_results_mean_wid.setText('0')
        self.write_to_file_wid = QLineEdit()
        self.write_to_file_btn = QPushButton(text='Write to file')
        self.write_to_file_wid.returnPressed.connect(self.save_calibration_value)
        self.write_to_file_btn.clicked.connect(self.save_calibration_value)
        self.write_to_file_wid.setToolTip('[SCCM, int] Results to write to calibration file\nBy default, mean of collected values is put here. Pairs can also be manually entered.')
        self.write_to_file_btn.setToolTip('Write pair to calibration file')
        layout_results = QGridLayout()
        layout_results.addWidget(QLabel('Median:'),     0,0);   layout_results.addWidget(self.cal_results_med_wid,  0,1)
        layout_results.addWidget(QLabel('Mean:'),       0,2);   layout_results.addWidget(self.cal_results_mean_wid, 0,3)
        layout_results.addWidget(QLabel('Range:'),      1,0);   layout_results.addWidget(self.cal_results_range_wid,1,1)
        layout_results.addWidget(QLabel('# of Vals:'),  1,2);   layout_results.addWidget(self.cal_results_num_wid,  1,3)
        final_row_layout = QHBoxLayout()
        final_row_layout.addWidget(QLabel('Results:'))
        final_row_layout.addWidget(self.write_to_file_wid)
        final_row_layout.addWidget(self.write_to_file_btn)
        layout_results.addLayout(final_row_layout,3,0,1,4)
        
        # Written to cal file
        self.cal_file_written_display = QTextEdit(readOnly=True)
        layout_cal_file_output = QVBoxLayout()
        layout_cal_file_output.addWidget(QLabel('Written to file:'))
        layout_cal_file_output.addWidget(self.cal_file_written_display)
        
        # Fix GUI
        self.mfc_value_wid.setEnabled(False)
        self.cal_duration_wid.setEnabled(False)
        self.start_calibration_btn.setEnabled(False)
        
        # LAYOUT
        layout_directory = QFormLayout()
        layout_directory.addRow(QLabel("Directory:"),self.cal_file_dir_wid)
        
        layout_file_name = QHBoxLayout()
        layout_file_name.addWidget(QLabel("File name:"))
        layout_file_name.addWidget(self.cal_file_name_wid)
        layout_mfc_value = QHBoxLayout()
        layout_mfc_value.addWidget(QLabel("MFC value (SCCM):"))
        layout_mfc_value.addWidget(self.mfc_value_wid)
        layout_cal_duration = QHBoxLayout()
        layout_cal_duration.addWidget(QLabel("Duration (s):"))
        layout_cal_duration.addWidget(self.cal_duration_wid)
        layout_cal_duration.addWidget(self.calibration_duration_label)        

        layout_entered_vals = QFormLayout()
        layout_entered_vals.addRow(layout_file_name)
        layout_entered_vals.addRow(layout_cal_duration)
        layout_entered_vals.addRow(layout_mfc_value)
        layout_entered_vals.addRow(self.create_new_cal_file_btn,self.start_calibration_btn)

        layout_calibration_box = QGridLayout()
        layout_calibration_box.addLayout(layout_directory,0,0,1,4)      # row0, col0, rowSpan1, colSpan4
        layout_calibration_box.addLayout(layout_entered_vals,1,0)
        layout_calibration_box.addLayout(layout_collected_vals,1,1)
        layout_calibration_box.addLayout(layout_results,1,2)
        layout_calibration_box.addLayout(layout_cal_file_output,1,3)

        self.new_cal_box.setLayout(layout_calibration_box)
        
        # Sizing
        self.collected_values_wid.setMaximumHeight(100)
        self.cal_file_written_display.setMaximumHeight(100)

        self.collected_values_wid.setMaximumWidth(80)
        self.write_to_file_wid.setFixedWidth(80)
        self.write_to_file_btn.setMaximumWidth(80)
        self.cal_file_written_display.setMaximumWidth(115)

    def create_data_receive_box(self):
        self.data_receive_box = QGroupBox("data received")

        self.receive_box = QTextEdit(readOnly=True)
        receive_box_lbl = QLabel(text="Flow val (int), Flow val (SCCM)")
        
        receive_box_layout = QVBoxLayout()
        receive_box_layout.addWidget(receive_box_lbl)
        receive_box_layout.addWidget(self.receive_box)
        self.data_receive_box.setLayout(receive_box_layout)
    
    
    # FUNCTIONS
    def get_calibration_tables(self):
        logger.debug('Loading all flow sensor calibration tables at (%s)', self.flow_cal_dir)
        
        # Get names of all .txt files in flow cal directory # TODO change to .csv
        cal_file_names = os.listdir(self.flow_cal_dir)
        cal_file_names = [fn for fn in cal_file_names if fn.endswith(cal_table_file_tyoe)]      # only txt files # TODO: change to csv
        
        if cal_file_names != []:
            
            # Create dictionaries for storing the calibration tables
            new_sccm2Ard_dicts = {}
            new_ard2Sccm_dicts = {}

            # Parse each file
            for cal_file in cal_file_names:
                idx_ext = cal_file.find('.')
                file_name = cal_file[:idx_ext]
                cal_file_full_dir = os.path.join(self.flow_cal_dir, cal_file)   # Fix for different operating systems by Xuebo 9/5/2025
                
                thisfile_sccm2Ard_dict = {}
                thisfile_ard2Sccm_dict = {}
                with open(cal_file_full_dir, newline='') as f:
                    csv_reader = csv.reader(f)      # Create reader object that will process lines from f (file)
                    firstLine = next(csv_reader)    # Skip over header line
                    
                    # For each row in the file
                    reader = csv.DictReader(f, delimiter=',')   # Create reader object that maps the information in each row to a dict
                    for row in reader:
                        try:
                            # Add to dict
                            thisfile_sccm2Ard_dict[float(row['SCCM'])] = float(row['int'])
                            thisfile_ard2Sccm_dict[float(row['int'])] = float(row['SCCM'])
                        except KeyError as err:
                            # Clear dictionaries & stop trying to read this file
                            logger.debug('KeyError: %s',err)
                            logger.error('%s does not have correct headings for calibration files', cal_file)
                            thisfile_sccm2Ard_dict = {}
                            thisfile_ard2Sccm_dict = {}
                            break
                        except ValueError as err:
                            # Clear dictionaries & stop trying to read this file
                            logger.debug('missing some values, skipping calibration file %s', cal_file)
                            thisfile_sccm2Ard_dict = {}
                            thisfile_ard2Sccm_dict = {}
                            break
                        except TypeError as err:
                            # Clear dictionaries & stop trying to read this file
                            logger.debug('Cannot read %s : %s', cal_file,err)
                            thisfile_sccm2Ard_dict = {}
                            thisfile_ard2Sccm_dict = {}
                            break
                # If this file was good (aka we got values), save it to the dict of dicts
                if bool(thisfile_sccm2Ard_dict) == True:
                    new_sccm2Ard_dicts[file_name] = thisfile_sccm2Ard_dict
                    new_ard2Sccm_dicts[file_name] = thisfile_ard2Sccm_dict
            
            # If we got stuff from these files, replace the old dicts
            if len(new_sccm2Ard_dicts) != 0:
                self.sccm2Ard_dicts = new_sccm2Ard_dicts
                self.ard2Sccm_dicts = new_ard2Sccm_dicts
            else:
                logger.warning('no calibration files found in this directory')
        
        else:
            logger.warning('no .txt files found in this directory :/')

    def cal_tbl_btn_toggled(self, checked):
        if checked:
            self.cal_table_btn.setText('Change current calibration table')
            self.cal_table_widget.setEnabled(False)
            self.calibration_table_changed()
        else:
            self.cal_table_btn.setText('Set calibration table')
            self.cal_table_widget.setEnabled(True)
    
    def calibration_table_changed(self):
        new_calibration_table_name = self.cal_table_widget.currentItem().text()
        self.intToSccm_dict = self.ard2Sccm_dicts.get(new_calibration_table_name)
        self.sccmToInt_dict = self.sccm2Ard_dicts.get(new_calibration_table_name)
    
    
    # CALIBRATION FUNCTIONS
    def create_new_cal_file_toggled(self):
        # Create new file
        if self.create_new_cal_file_btn.isChecked() == True:
            # UI THINGS
            self.create_new_cal_file_btn.setText('End && Save file')
            self.create_new_cal_file_btn.setToolTip('End calibration\n(the file is already saved though)\n(bc it writes the values in real time)')
            self.cal_file_dir_wid.setEnabled(False)
            self.cal_file_name_wid.setEnabled(False)
            
            # Get calibration file name & directory
            self.new_cal_file_name = self.cal_file_name_wid.text()
            self.new_cal_file_dir = self.cal_file_dir_wid.text() + '\\' + self.new_cal_file_name + '.csv'

            # Create calibration file
            if not os.path.exists(self.new_cal_file_dir):
                self.create_file()
            else:
                # Ask user if they want to overwrite the current file
                msg_box = QMessageBox()
                msg_box.setWindowTitle('Confirm Overwrite')
                msg_box.setText(self.new_cal_file_name + ' already exists: overwrite?')
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                ret = msg_box.exec()
                if ret == QMessageBox.Yes:
                    logger.info('Deleting %s.csv (%s)', self.new_cal_file_name, self.new_cal_file_dir)
                    os.remove(self.new_cal_file_dir)
                    self.create_file()
                if ret == QMessageBox.No:
                    logger.debug('Enter new file name to create a calibration file')
                    self.create_new_cal_file_btn.setChecked(False)
        
        # Done with calibration - reset user interface
        else:
            logger.info('Ended recording to calibration file %s.csv', self.new_cal_file_name)
            
            # UI THINGS
            self.create_new_cal_file_btn.setText('Create new file')
            self.create_new_cal_file_btn.setToolTip('')
            self.cal_file_dir_wid.setEnabled(True)
            self.cal_file_name_wid.setEnabled(True)
            
            # Disable the MFC stuff
            self.mfc_value_wid.setEnabled(False)
            self.cal_duration_wid.setEnabled(False)
            self.start_calibration_btn.setEnabled(False)
    
    def start_calibration(self, checked):
        if checked:
            
            # Get sccm value & duration
            self.this_cal_sccm_value = self.mfc_value_wid.text()
            self.this_cal_duration = self.cal_duration_wid.text()

            logger.debug('Starting calibration at %s sccm', self.this_cal_sccm_value)
                        
            # Fix the GUI
            self.write_to_file_btn.setEnabled(False)
            self.create_new_cal_file_btn.setEnabled(False)
            self.start_calibration_btn.setText('End early')
            self.start_calibration_btn.setToolTip('Stop collecting flow values')
            self.collected_values_wid.clear()
            
            # Initialize empty data arrays
            self.serial_values = []
            self.serial_values_std = []
            self.start_of_good_values = []
            self.duration_of_good_values = timedelta(0,10)  # 10 sec
            self.all_std_devs = []
            self.values_means = []
            
            # Set calibration object to ON (add incoming values to collected calibration values)
            self.calibration_on = True

            # Start calibration timer
            self.start_cal_duration_timer(int(self.this_cal_duration))

        else:
            # Fix the GUI
            self.write_to_file_btn.setEnabled(True)
            self.create_new_cal_file_btn.setEnabled(True)
            self.start_calibration_btn.setText('Start')
            self.start_calibration_btn.setToolTip('Collect flow values for x seconds')

            # Stop the timer
            if self.calibration_duration_timer.isActive() == True:  self.end_cal_duration_timer()    
    
    def create_file(self):
        logger.info('Creating calibration file: %s.csv (%s)', self.new_cal_file_name, self.new_cal_file_dir)
        file_created_time = get_current_time()
        File = self.new_cal_file_name,file_created_time
        row_headers = 'SCCM','int'
        
        # Write file header
        with open(self.new_cal_file_dir,'a',newline='') as f:
            writer = csv.writer(f,delimiter=',')
            writer.writerow(File)
            writer.writerow(row_headers)
        
        # Fix the GUI
        self.mfc_value_wid.setEnabled(True)
        self.cal_duration_wid.setEnabled(True)
        self.start_calibration_btn.setEnabled(True)
        self.collected_values_wid.clear()
        self.cal_file_written_display.clear()
    
    def analyze_cal_session(self):
        flowVal_median = np.median(self.serial_values)
        flowVal_mean = round(np.mean(self.serial_values),1)
        
        try:
            # Calculations
            flow_min = min(self.serial_values)
            flow_max = max(self.serial_values)
            flow_range = flow_max - flow_min
            self.cal_results_min_wid.setText(str(flow_min))
            self.cal_results_max_wid.setText(str(flow_max))
            self.cal_results_med_wid.setText(str(flowVal_median))
            self.cal_results_mean_wid.setText(str(flowVal_mean))
            self.cal_results_range_wid.setText(str(flow_range))
            self.cal_results_num_wid.setText(str(len(self.serial_values)))
            logger.debug(self.this_cal_sccm_value + ' SCCM:' +
                         '\t median: ' + str(flowVal_median) +
                         '\t mean: ' + str(flowVal_mean) +
                         '\t range: ' + str(flow_range) +
                         '\t (' + str(self.this_cal_duration) + 'sec, ' + str(len(self.serial_values)) + ' values)')
            
            # Put mean value in the widget so the user can decide whether to keep it or not
            self.this_cal_int_value = flowVal_mean
            if type(self.this_cal_int_value) is np.float64:
                pair = str(self.this_cal_sccm_value) + ', ' + str(round(self.this_cal_int_value,2))
                self.write_to_file_wid.setText(pair)
            else:
                logger.warning('calculated value was not an int - cannot save this value')
        
        except ValueError as err:
            # 11/8/2023: got this error when trying to write to file while calibration was running  -this should be fixed now 6/21/2024
            logger.warning('ValueError:' + str(err))
        
        # Clear the array
        self.serial_values = []
    
    def save_calibration_value(self):
        # Write the data from the widget to the file
        pair_to_write = eval(self.write_to_file_wid.text())     # Convert from string to tuple
        logger.debug('Writing to cal file: %s', pair_to_write)
        try:
            with open(self.new_cal_file_dir,'a',newline='') as f:
                writer = csv.writer(f,delimiter=',')
                writer.writerow(pair_to_write)
        except PermissionError as err:
            logger.warning('Cannot write to file: make sure you don''t have it open anywhere')

        # Display what we wrote to the table
        str_to_display = self.write_to_file_wid.text()
        self.cal_file_written_display.append(str_to_display)
        
        # Clear lists
        self.serial_values = []
        self.serial_converted = []

        # Reset
        self.calibration_on = False
        self.start_calibration_btn.setChecked(False)
    

    # FLOW CALIBRATION TIMER
    def start_cal_duration_timer(self, duration):
        self.calibration_start_time = datetime.now()
        self.calibration_full_duration = timedelta(0,int(duration))
        self.calibration_duration_timer.start(int(duration))

    def show_cal_duration_time(self):
        current_time = datetime.now()
        current_cal_dur = current_time - self.calibration_start_time
        if current_cal_dur >= self.calibration_full_duration:
            self.end_cal_duration_timer()
        
        cal_dur_display_value = str(current_cal_dur)
        cal_dur_display_value = cal_dur_display_value[5:]   # remove beginning digits, 2 values before decimal point
        cal_dur_display_value = cal_dur_display_value[:-3]  # leave 3 digits after the decimal point
        self.calibration_duration_label.setText(cal_dur_display_value)
    
    def end_cal_duration_timer(self):
        self.calibration_duration_timer.stop()
        self.calibration_on = False
        
        self.start_calibration_btn.setChecked(False)
        self.analyze_cal_session()
    
    
    # CONNECT TO DEVICE
    def get_ports(self):
        self.port_widget.clear()
        ports = list_ports.comports()
        if ports:
            for ser in ports:
                port_device = ser[0]
                port_description = ser[1]
                if port_device in port_description:
                    idx1 = port_description.find(port_device)
                    port_description = port_description[:idx1-2]
                ser_str = ('{}: {}').format(port_device,port_description)
                self.port_widget.addItem(ser_str)
        else:
            self.port_widget.addItem(noPortMsg)

        # if any are 'Arduino', set the first one to the current index
        for item_idx in range(0,self.port_widget.count()):
            this_item = self.port_widget.itemText(item_idx)
            if 'Arduino' in this_item:
                break
        if item_idx != []:
            self.port_widget.setCurrentIndex(item_idx)
        else:
            logger.debug('no Arduinos detected :(')
    
    def port_changed(self):
        if self.port_widget.count() != 0:
            self.port = self.port_widget.currentText()
            if self.port == noPortMsg:
                self.portStr = noPortMsg
                self.connect_btn.setEnabled(False)
                self.connect_btn.setText(noPortMsg)
            else:
                self.portStr = self.port[:self.port.index(':')]
                self.connect_btn.setEnabled(True)
                self.connect_btn.setText("Connect to  " + self.portStr)
        
    def toggled_connect(self, checked):
        if checked:
            i = self.port.index(':')
            self.comPort = self.port[:i]
            self.serial = QtSerialPort.QSerialPort(self.comPort,baudRate=flowSens_baud,readyRead=self.receive)
            if not self.serial.isOpen():
                if self.serial.open(QtCore.QIODevice.ReadWrite):
                    self.set_connected(True)
                else:
                    self.set_connected(False)
            else:
                self.set_connected(True)
        else:
            try:
                self.serial.close()
                self.set_connected(False)
            except AttributeError as err:
                logger.error("error :( --> %s", err)
    
    def set_connected(self, connected):
        if connected == True:
            logger.info('Connected to ' + self.port_widget.currentText())
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setToolTip("Disconnect from " + self.portStr)
            self.refresh_btn.setEnabled(False)
            self.port_widget.setEnabled(False)
            self.cal_table_select_box.setEnabled(True)
            self.new_cal_box.setEnabled(True)
        
        else:
            logger.info('Disconnected from ' + self.port_widget.currentText())
            self.connect_btn.setText("Connect")
            self.connect_btn.setToolTip("Connect to " + self.portStr)
            self.connect_btn.setChecked(False)
            self.refresh_btn.setEnabled(True)
            self.port_widget.setEnabled(True)
            self.cal_table_select_box.setEnabled(False)
            self.new_cal_box.setEnabled(False)
    
    
    # SEND/RECEIVE DATA
    def receive(self):
        if self.serial.canReadLine() == True:
            text = self.serial.readLine(1024)
            try:
                text = text.decode("utf-8")
                text = text.rstrip('\r\n')
                if text.isnumeric():
                    str_value = text
                    flowVal_int = int(text)
                    dataStr = str_value + '\t'
                    self.receive_box.append(dataStr)

                    # if calibration is on:
                    if self.calibration_on == True:
                        self.serial_values.append(flowVal_int)
                        self.collected_values_wid.append(str(flowVal_int))

            except UnicodeDecodeError as err:   logger.error('Serial read error: %s',err)
    
    def send_to_arduino(self, strToSend):
        bArr_send = strToSend.encode()
        try:
            if self.serial.isOpen():
                self.serial.write(bArr_send)                # send to Arduino
            else:
                logger.warning('Serial port not open, cannot send parameter: %s', strToSend)
        except AttributeError as err:
            logger.warning('(Attribute Error) Serial port not open, cannot send parameter: %s', strToSend)


if __name__ == "__main__":
    app1 = QApplication(sys.argv)
    theWindow = flowSensor()
    theWindow.show()
    theWindow.setWindowTitle('Flow Sensor Widget')
    sys.exit(app1.exec_())