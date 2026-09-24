'''
dilutor_calibration.py

Loads calibration tables for each MFC (main olfa, air, vacuum) and fits linear model to each.
For the desired dilution value, calculates setpoint for air and vacuum MFCs (to match main olfa MFC).

ST 2026
'''

import os, csv
import numpy as np
import matplotlib.pyplot as plt
plt.ion()   # Enable interactive mode
import warnings
import logging

################################
# File names
'''
olfa_file = '2026-04-17_olfa_mfc.csv'
air_file = '2026-04-17_air_mfc.csv'
vac_file = '2026-04-17_vac_mfc.csv'
olfa_max = 1000
'''

olfa_file = '2026-08-06_olfa_mfc.csv'
air_file = '2026-08-06_air_mfc.csv'
vac_file = '2026-08-06_vac_mfc.csv'
olfa_max = 958

# Value to dilute to
dilute_to = 970
dilute_to = 900
################################


# Where the calibration tables are stored
current_dir = os.getcwd()
file_directory = os.path.join(current_dir,'calibration_tables')
# For plotting
ylims_V = [.5, 5.5]
ylims_int = [102, 1126]

# Logger
logger = logging.getLogger(name='main')
logger.setLevel(logging.DEBUG)
logger.propagate = False    # removes duplicate log messages
console_handler_formatter = logging.Formatter('%(asctime)s : %(levelname)s: %(message)s',datefmt='%H:%M:%S')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(console_handler_formatter)
logger.addHandler(console_handler)

r2_threshold = 0.9995

def load_csv(full_filepath):
    '''
    Load MFC and flowmeter values from a CSV file.
    Skips the first two header rows.

    Parameters
        full_filepath : str
            Full path to the CSV file (including file name & extension)

    Returns
        mfc_values, flowmeter_values : list of float
            Values from the first and second columns, respectively
    '''

    mfc_values = []
    flowmeter_values = []
    try:
        with open(full_filepath,newline='') as f:
            csv_reader = csv.reader(f)      # Create reader object that will process lines from f (file)
            firstLine = next(csv_reader)    # Skip over header line
            secondLine = next(csv_reader)   # Skip over second line
            
            # Load all of the values in
            for row in csv_reader:
                mfc_values.append(float(row[0]))           # First column (MFC_value)
                flowmeter_values.append(float(row[1]))     # Second column (Flowmeter_value)
    except FileNotFoundError as e:
        logger.error(f"ERROR: File does not exist: {e}")
        logger.error(f"\t\t This is not going to work")

    return mfc_values,flowmeter_values

def fit_quadratic(mfc_values,flowmeter_values):
    '''
    Give it the lists of mfc_values and flowmeter_values, Fits quadratic to it
    '''

    poly2 = np.polyfit(mfc_values, flowmeter_values, 2)  # 2nd degree (quadratic) (poly2 is an array)    
    fit2 = np.poly1d(poly2)     # Create polynomial functions from the coefficients (these are polynomial class)
    
    return fit2,poly2           # array, polynomial class    

def calculate_mfc_quadratic(poly_,olfa_FM_dil_value):
    # Subtract the target value to find where polynomial equals flowmeter_reading
    coefficients = [poly_[0],poly_[1],poly_[2] - olfa_FM_dil_value] # 8/21/26 why... why are we subtracting....plz

    # Solve for x (MFC value)
    solutions = np.roots(coefficients)

    the_solution = None
    # Since it's quadratic there will be two, so pick the one that.... is between 0 and 1000
    for solution in solutions:
        if np.isreal(solution):
            if (solution > 0) and (solution < 1000):
                if the_solution is None:
                    logger.debug('\tfound a solution')
                    the_solution = solution
                else:
                    logger.warning('\tWARNING WARNING found 2 solutions!!!')
                    return solutions
            else:
                logger.debug('\tsolution is real but not within range')
        else:
            logger.debug('\tsolution is not a real number')
    
    if the_solution is None:
        logger.error("big error: did not get any solutions")

    return the_solution

# --- R² ---
def r_squared(y_actual, y_predicted):
    ss_res = np.sum((y_actual - y_predicted) ** 2)
    ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)
    return 1 - (ss_res / ss_tot)

def calculate_section(mfc_values,flowmeter_values):
    '''
    Calculate all of the data for a given region


    Input:
        mfc values
        flowmeter values
        r2 threshold?
    
    Returns:
        mfc values for this section
        flowmeter vals for this section
        coefficients
        polynomial
        r^2 value
    '''

    mfc_vals_section = mfc_values
    flow_vals_section = flowmeter_values

    with warnings.catch_warnings():
        warnings.filterwarnings('error', message='.*Polyfit.*')
        try:
            # --- Calculate initial quadratic & R^2 for the entire dataset
            coeffs_section = np.polyfit(mfc_vals_section,flow_vals_section,2)
            poly1d_section = np.poly1d(coeffs_section)
            r2_section = r_squared(flow_vals_section, poly1d_section(mfc_vals_section))

        except np.exceptions.RankWarning as e:
            logger.warning('RankWarning: need to lower polynomial degree')
            # Need to lower the polynomial degree
            coeffs_section = np.polyfit(mfc_vals_section,flow_vals_section,1)
            poly1d_section = np.poly1d(coeffs_section)
            r2_section = r_squared(flow_vals_section, poly1d_section(mfc_vals_section))            

    # --- Remove one value from the end, recalculate R^2 until it's > 0.9995
    while r2_section < r2_threshold:
        # Remove one mfc value and one flowmeter value from the end
        mfc_vals_section = mfc_vals_section[0:(len(mfc_vals_section)-1)]
        flow_vals_section = flow_vals_section[0:(len(flow_vals_section)-1)]

        # Check how many values are left (if we're down to 5, something prob went wrong)
        i = len(mfc_vals_section)
        if i < 5:
            logger.error('stop - something went wrong')

        # Recalculate quadratic & R^2 for the shortened dataset
        coeffs_section = np.polyfit(mfc_vals_section,flow_vals_section,2)
        poly1d_section = np.poly1d(coeffs_section)
        r2_section = r_squared(flow_vals_section,poly1d_section(mfc_vals_section))
        # TODO also calculate a linear and see if that works better
    
    # Return everything
    return mfc_vals_section,flow_vals_section,coeffs_section,poly1d_section,r2_section


def fit_piecewise_equations(mfc_values,flowmeter_values):
    '''
    New strategy
        calculate a quadratic fit
        calculate the R2
        while R2<.999
            remove points from the end
            recalculate
        
        once it's good
            this is equation [x] for range [x]
        move to the next section and do the same thing
        for as long as it takes

    Returns a list of dicts
    Each dict is a 1 section of the data
    '''
    
    # --- Initialize list of dicts for olfa
    olfa_data_list = []


    # -------------------------------------------------------------
    # --- Initial Setup
    # Convert data from list to numpy.ndarray
    mfc_values = np.array(mfc_values)
    flowmeter_values = np.array(flowmeter_values)

    # Sort data from lowest --> highest
    sort_idx = np.argsort(mfc_values)
    mfc_values = mfc_values[sort_idx]
    flowmeter_values = flowmeter_values[sort_idx]

    i = 1
    # -------------------------------------------------------------
    # --- Get the data & equations for the first section
    mfc_vals_section,flow_vals_section,coeffs_section,poly1d_section,r2_section = calculate_section(mfc_values,flowmeter_values)
    # Add this data to the olfa list of dicts
    this_section_dict = {
        "mfc_values": mfc_vals_section,
        "flowmeter_values": flow_vals_section,
        "coefficients": coeffs_section,
        "poly1d": poly1d_section,
        "r_2": r2_section
    }
    olfa_data_list.append(this_section_dict)
    mfc_vals_prev_section = mfc_vals_section

    i=i+1    
    # -------------------------------------------------------------
    # --- Loop it
    while max(mfc_values) not in mfc_vals_prev_section:
        # -------------------------------------------------------------
        # --- Define section starting from the max value of the previous section
        # Find the maximum MFC value from the previous section & locate its index in the full dataset
        max_mfc_prev_section = max(mfc_vals_prev_section)
        index = np.where(mfc_values == max_mfc_prev_section)[0][0]  # np.where returns a tuple of arrays; use [0][0] to extract the first occurrence

        # Get data from this index onward for the next section
        mfc_values_this_region = mfc_values[index:len(mfc_values)]
        flow_values_this_region = flowmeter_values[index:len(mfc_values)]

        # -------------------------------------------------------------
        # --- Get the data & equations for this section
        mfc_vals_section,flow_vals_section,coeffs_section,poly1d_section,r2_section = calculate_section(mfc_values_this_region,flow_values_this_region)
        # Add this data to the olfa list of dicts
        this_section_dict = {
            "mfc_values": mfc_vals_section,
            "flowmeter_values": flow_vals_section,
            "coefficients": coeffs_section,
            "poly1d": poly1d_section,
            "r_2": r2_section
        }
        olfa_data_list.append(this_section_dict)
        mfc_vals_prev_section = mfc_vals_section

        '''
        if len(coeffs_section) == 3:
            logger.debug(f"\t V = {coeffs_section[0]:.6f} * SCCM² + {coeffs_section[1]:.6f} * SCCM + {coeffs_section[2]:.6f}")
        else:
            logger.debug(f"\t V = {coeffs_section[0]:.6f} * SCCM + {coeffs_section[1]:.6f}")
        '''
        i=i+1

    # The end
    # Return the LIST of DICTS
    # Each DICT is a section of data (& the corresponding equation)
    return olfa_data_list

def find_flow_value_olfa(olfa_data_list, target_value):
    '''
    Input:
        all of the sections for the main olfa MFFC
        MFC value/setting
    Returns:
        section where that MFC value happens
        equivalent flowmeter value
    '''

    for section in olfa_data_list:
        mfc_vals = section["mfc_values"]
        min_val = np.min(mfc_vals)
        max_val = np.max(mfc_vals)
        
        if min_val <= target_value <= max_val:
            # Try to find exact match
            matching_indices = np.where(mfc_vals == target_value)[0]

            if len(matching_indices) > 0:
                # Exact match found
                idx = matching_indices[0]
                flow_value = section["flowmeter_values"][idx]
            else:
                # No exact match - use the polyfit to get the flow value
                polyfit = section["poly1d"]
                flow_value = polyfit(target_value)
            return section, flow_value

    return None

def find_section(data_list, target_value):
    '''
    Input:
        all of the sections for an MFC
        flowmeter value

    Returns:
        section where that flowmeter value happens
        equivalent MFC value
    
    '''
    # Check each section to find where this flowmeter value is
    for section in data_list:
        flow_vals = section["flowmeter_values"]
        mfc_vals = section["mfc_values"]
        min_val = np.min(flow_vals)
        max_val = np.max(flow_vals)

        if min_val <= target_value <= max_val:

            # Try to find exact match (for fun)
            matching_indicies = np.where(flow_vals == target_value)[0]

            if len(matching_indicies) > 0:
                # Exact match found
                idx = matching_indicies[0]
                mfc_value = section["mfc_values"][idx]
                logger.info(f"Exact match found at index {idx}")
                logger.info(f"Corresponding flowmeter value: {mfc_value}")
            else:
                # No exact match, use the polyfit to get the MFC value
                coeffs = section["coefficients"]
                
                # now go back and calculate the quadratic
                mfc_value = calculate_mfc_quadratic(coeffs,target_value)
                # If there are two solutions... we pick the one that is within this range of mfc values
                try:
                    if len(mfc_value) > 1:
                        logger.debug('\tSelecting the mfc value that is in this range')
                        min_mfc = min(mfc_vals)
                        max_mfc = max(mfc_vals)
                        # Thoughts and prayers there are only 2
                        value1 = mfc_value[0]
                        value2 = mfc_value[1]
                        value1_in_range = min_mfc <= value1 <= max_mfc
                        value2_in_range = min_mfc <= value2 <= max_mfc
                        if value1_in_range: mfc_value = value1
                        if value2_in_range: mfc_value = value2
                except TypeError:
                    # It's a float so nothing to worry about
                    pass

            return section, mfc_value   # TODO don't need to return section

def plot_data_with_equations(mfc_values, flowmeter_values, olfa_data_list, title):

    # --- Plot for debugging
    plt.figure(figsize=(6,5))
    plt.scatter(mfc_values,flowmeter_values)
    plt.xlabel('MFC setting (SCCM)')
    plt.ylabel('Flowmeter Reading')
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.scatter(mfc_values, flowmeter_values, color='black')
    plt.xlim(-50, 1050)
    plt.ylim(-.5, 5.5)

    for section in olfa_data_list:
        mfc_vals_section = section['mfc_values']
        poly1d_section = section['poly1d']

        x_vals = np.linspace(min(mfc_vals_section),max(mfc_vals_section),100)
        plt.plot(x_vals, poly1d_section(x_vals))


def main():
    '''Load in the 3 csvs'''
    file_path_olfa = os.path.join(file_directory,olfa_file)  # Directory for olfa file
    mfc_values,flowmeter_values = load_csv(file_path_olfa)   # Load the mfc values and flowmeter values    
    file_path_vac = os.path.join(file_directory,vac_file)
    mfc_vac,flowmeter_vac = load_csv(file_path_vac)
    file_path_air = os.path.join(file_directory,air_file)
    mfc_air,flowmeter_air = load_csv(file_path_air)
    
    '''Check if values are V or int (for plotting)'''
    if max(flowmeter_values) > 100: ylims = ylims_int
    else: ylims = ylims_V

    '''Calculate multiple equations for each MFC'''
    olfa_equations = fit_piecewise_equations(mfc_values,flowmeter_values)
    air_equations = fit_piecewise_equations(mfc_air,flowmeter_air)
    vac_equations = fit_piecewise_equations(mfc_vac,flowmeter_vac)

    '''Plot each'''
    plot_data_with_equations(mfc_values,flowmeter_values,olfa_equations,'Olfa MFC Calibration')
    plot_data_with_equations(mfc_air,flowmeter_air,air_equations,'Air MFC Calibration')
    plot_data_with_equations(mfc_vac,flowmeter_vac,vac_equations,'Vac MFC Calibration')
    
    '''Using these: get the olfa flowmeter value at the number we want to dilute to'''
    olfa_section, olfa_FM_dil_value = find_flow_value_olfa(olfa_equations,dilute_to) # TODO error when i try and run 970
    logger.info(f"Dilution value: {dilute_to:.2f}")
    logger.info(f"Olfa FM equivalent: {olfa_FM_dil_value:.4f}")

    '''Calculate the air MFC value'''
    air_section, air_mfc_value = find_section(air_equations, olfa_FM_dil_value)
    logger.info(f"Calculated Air MFC setting: {air_mfc_value:.2f}")

    '''Calculate the vac MFC value'''
    # vac flowmeter value is olfa function at 1000-setpoint
    # vac_fm_value = olfa_poly1d(max_olfa-target)
    # get the olfa_poly1d for this section
    # except it's no longer one section it is multiple
    # i guess we fucking average these equations??? idk
    # equation as a function of (1000-900)

    # i guess we can start there
    olfa_val_to_plug_in = olfa_max - dilute_to
    # what equation do we use for this
    olfa_section, vac_fm_value = find_flow_value_olfa(olfa_equations,olfa_val_to_plug_in)
    vac_section, vac_mfc_value = find_section(vac_equations, vac_fm_value)
    logger.info(f"Calculated Vac MFC setting: {vac_mfc_value:.2f}")

    ###################################################################

    '''Plot for visual'''
    fig1, (ax1,ax2) = plt.subplots(1,2, figsize=(12,5),sharex=True)#,sharey=True)
    fig1.canvas.manager.set_window_title('Air MFC Setting')

    ax1.scatter(mfc_values,flowmeter_values,color='r')
    ax1.set_xlabel('MFC setting (SCCM)')
    ax1.set_ylabel('Flowmeter Reading')
    ax1.set_title('Olfa MFC Calibration')
    ax1.grid(True)
    ax1.set_xlim(-50, 1050)
    ax1.set_ylim(-.5, 5.5)
    # Plot the olfa curve for the section
    olfa_mfc_vals_section = olfa_section['mfc_values']
    olfa_poly1d_section = olfa_section['poly1d']
    x_vals_olfa = np.linspace(min(olfa_mfc_vals_section),max(olfa_mfc_vals_section),100)
    ax1.plot(x_vals_olfa,olfa_poly1d_section(x_vals_olfa),color='k')
    # Plot horizontal and vertical lines at the dilution value
    ax1.axhline(y=olfa_FM_dil_value,color='k',label=f'{dilute_to} SCCM = {round(olfa_FM_dil_value,2)} V')
    ax1.axvline(x=dilute_to,color='k')

    ax2.scatter(mfc_air,flowmeter_air,color='b')
    ax2.set_xlabel('MFC setting (SCCM)')
    ax2.set_ylabel('Flowmeter Reading')
    ax2.set_title('Air MFC Calibration')
    ax2.grid(True)
    ax2.set_xlim(-50, 1050)
    ax2.set_ylim(-.5, 5.5)
    # Plot the air curve for the section
    air_mfc_vals_section = air_section['mfc_values']
    air_poly1d_section = air_section['poly1d']
    x_vals_air = np.linspace(min(air_mfc_vals_section),max(air_mfc_vals_section),100)
    ax2.plot(x_vals_air,air_poly1d_section(x_vals_air),color='b')
    # Plot horizontal and vertical lines at the dilution value
    ax2.axhline(y=olfa_FM_dil_value,color='k',label=f'{round(olfa_FM_dil_value,2)} V ---> set MFC to {round(air_mfc_value,1)} SCCM')
    ax2.axvline(x=air_mfc_value,color='k')

    ax1.legend(loc='upper left')
    ax2.legend(loc='upper left')
    fig1.tight_layout()

    ###################################################################

    '''Plot for visual'''
    fig1, (ax1,ax2) = plt.subplots(1,2, figsize=(12,5),sharex=True)#,sharey=True)
    fig1.canvas.manager.set_window_title('Vac MFC Setting')

    ax1.scatter(mfc_values,flowmeter_values,color='r')
    ax1.set_xlabel('MFC setting (SCCM)')
    ax1.set_ylabel('Flowmeter Reading')
    ax1.set_title('Olfa MFC Calibration')
    ax1.grid(True)
    ax1.set_xlim(-50, 1050)
    ax1.set_ylim(-.5, 5.5)
    # Plot the olfa curve for the section
    olfa_mfc_vals_section = olfa_section['mfc_values']
    olfa_poly1d_section = olfa_section['poly1d']
    x_vals_olfa = np.linspace(min(olfa_mfc_vals_section),max(olfa_mfc_vals_section),100)
    ax1.plot(x_vals_olfa,olfa_poly1d_section(x_vals_olfa),color='k')
    # Plot horizontal and vertical lines at the dilution value
    ax1.axhline(y=olfa_FM_dil_value,color='k',label=f'{dilute_to} SCCM = {round(olfa_FM_dil_value,2)} V')
    ax1.axvline(x=dilute_to,color='k')

    ax2.scatter(mfc_vac,flowmeter_vac,color='g')
    ax2.set_xlabel('MFC setting (SCCM)')
    ax2.set_ylabel('Flowmeter Reading')
    ax2.set_title('Vac MFC Calibration')
    ax2.grid(True)
    ax2.set_xlim(-50, 1050)
    ax2.set_ylim(-.5, 5.5)

    # Plot the vac curve for the section
    vac_mfc_vals_section = vac_section['mfc_values']
    vac_poly1d_section = vac_section['poly1d']
    x_vals_vac = np.linspace(min(vac_mfc_vals_section),max(vac_mfc_vals_section),100)
    ax2.plot(x_vals_vac,vac_poly1d_section(x_vals_vac),color='g')
    # Plot horizontal and vertical lines at the dilution value
    ax2.axhline(y=olfa_FM_dil_value,color='k',label=f'{round(olfa_FM_dil_value,2)} V ---> set MFC to {round(vac_mfc_value,1)} SCCM')
    ax2.axvline(x=vac_mfc_value,color='k')

    ax1.legend(loc='upper left')
    ax2.legend(loc='upper left')
    fig1.tight_layout()

if __name__ == "__main__":
    main()
    input("Plots displayed. Press Enter to exit...")