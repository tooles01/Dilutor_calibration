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
    
    with open(full_filepath,newline='') as f:
        csv_reader = csv.reader(f)      # Create reader object that will process lines from f (file)
        firstLine = next(csv_reader)    # Skip over header line
        secondLine = next(csv_reader)   # Skip over second line
        
        # Load all of the values in
        for row in csv_reader:
            mfc_values.append(float(row[0]))           # First column (MFC_value)
            flowmeter_values.append(float(row[1]))     # Second column (Flowmeter_value)

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
    coefficients = [poly_[0],poly_[1],poly_[2] - olfa_FM_dil_value]

    # Solve for x (MFC value)
    solutions = np.roots(coefficients)

    the_solution = None
    # Since it's quadratic there will be two, so pick the one that.... is between 0 and 1000
    for solution in solutions:
        if np.isreal(solution):
            if (solution > 0) and (solution < 1000):
                if the_solution is None:
                    print('\tfound a solution')
                    the_solution = solution
                else:
                    print('\tWARNING WARNING found 2 solutions!!!')
            else:
                print('\tsolution is real but not within range')
        else:
            print('\tsolution is not a real number')
    
    if the_solution is None:
        print("big error: did not get any solutions")

    return the_solution

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

    '''Calculate the quadratic fit for MFCs'''
    fit_olfa,poly_olfa = fit_quadratic(mfc_values,flowmeter_values)
    fit_air,poly_air = fit_quadratic(mfc_air,flowmeter_air)
    fit_vac,poly_vac = fit_quadratic(mfc_vac,flowmeter_vac)

    '''Get the olfa flowmeter value at the number we want to dilute to'''
    olfa_FM_dil_value = fit_olfa(dilute_to)
    print(f"Dilution value: {dilute_to:.2f}")
    print(f"Olfa FM equivalent: {olfa_FM_dil_value:.4f}")

    ################################################################

    '''Calculate air MFC value'''
    air_mfc_value = calculate_mfc_quadratic(poly_air,olfa_FM_dil_value)
    
    '''Plot olfa and air side by side'''
    fig_oa, (ax_o1,ax_a) = plt.subplots(1,2, figsize=(12,5),sharex=True,sharey=True)
    
    # Olfa
    x_olfa = np.linspace(min(mfc_values), max(mfc_values), 100)
    ax_o1.scatter(mfc_values,flowmeter_values,color='r')
    ax_o1.set_title('Olfa MFC Calibration')
    ax_o1.plot(x_olfa, fit_olfa(x_olfa),'r',linewidth=2)
    
    # Air
    x_air = np.linspace(min(mfc_air), max(mfc_air), 100)
    ax_a.scatter(mfc_air,flowmeter_air,color='b')
    ax_a.set_title('Air MFC Calibration')
    ax_a.plot(x_air, fit_air(x_air),'b',linewidth=2)

    # Horizontal line at flowmeter value
    ax_o1.axhline(y=olfa_FM_dil_value,color='k',label=f'{round(olfa_FM_dil_value,2)} V ({dilute_to} SCCM)')
    ax_a.axhline(y=olfa_FM_dil_value,color='k',label=f'{round(olfa_FM_dil_value,2)} V ---> set MFC to {round(air_mfc_value,2)} SCCM')
    
    # Vertical line at MFC setting
    ax_a.axvline(x=air_mfc_value,color='b')

    ax_o1.grid(True, alpha=0.3)
    ax_a.grid(True, alpha=0.3)
    ax_o1.legend(loc='upper left')
    ax_a.legend(loc='upper left')
    ax_o1.set_xlabel('MFC setting (SCCM)', fontsize=12)
    ax_a.set_xlabel('MFC setting (SCCM)', fontsize=12)
    ax_o1.set_ylabel('Flowmeter Reading (Vdc)', fontsize=12)
    ax_a.set_ylabel('Flowmeter Reading (Vdc)', fontsize=12)
    ax_o1.set_xlim([-50, 1050])
    ax_o1.set_ylim(ylims)
    fig_oa.tight_layout()

    ################################################################

    '''Calculate vac MFC value'''
    # vac flowmeter value is olfa function at 1000-setpoint
    vac_fm_value = fit_olfa(olfa_max-dilute_to)
    vac_mfc_value = calculate_mfc_quadratic(poly_vac,vac_fm_value)

    '''Plot olfa and vac side by side'''
    fig_ov, (ax_o2,ax_v) = plt.subplots(1,2, figsize=(12,5),sharex=True,sharey=True)
    
    # Olfa
    x_olfa = np.linspace(min(mfc_values), max(mfc_values), 100)
    ax_o2.scatter(mfc_values,flowmeter_values,color='r')
    ax_o2.set_title('Olfa MFC Calibration')
    ax_o2.plot(x_olfa, fit_olfa(x_olfa),'r',linewidth=2)

    # Vac
    x_vac = np.linspace(min(mfc_vac), max(mfc_vac), 100)
    ax_v.scatter(mfc_vac,flowmeter_vac,color='g')
    ax_v.set_title('Vac MFC Calibration')
    ax_v.plot(x_vac, fit_vac(x_vac),'g',linewidth=2)
    
    # Olfa at (1000-dilution value)
    vac_mfc_dil_value = olfa_max-dilute_to
    vac_FM_dil_value = fit_olfa(vac_mfc_dil_value)
    
    # Horizontal line at flowmeter value
    ax_o2.axhline(y=vac_FM_dil_value,color='k',label=f'FM at [{olfa_max}-{dilute_to}] SCCM  = ({round(vac_FM_dil_value,2)} V)')
    ax_v.axhline(y=vac_FM_dil_value,color='k',label=f'{round(vac_FM_dil_value,2)} V ---> set MFC to {round(vac_mfc_value,2)} SCCM')

    # Vertical line at MFC setting
    ax_v.axvline(x=vac_mfc_value,color='g')
    
    ax_o2.grid(True, alpha=0.3)
    ax_v.grid(True, alpha=0.3)
    ax_o2.legend(loc='upper left')
    ax_v.legend(loc='upper left')
    ax_o2.set_xlabel('MFC setting (SCCM)', fontsize=12)
    ax_v.set_xlabel('MFC setting (SCCM)', fontsize=12)
    ax_o2.set_ylabel('Flowmeter Reading (Vdc)', fontsize=12)
    ax_v.set_ylabel('Flowmeter Reading (Vdc)', fontsize=12)
    ax_o2.set_xlim([-50, 1050])
    ax_o2.set_ylim(ylims)
    fig_ov.tight_layout()
    
    ################################################################
    
    print(f"Calculated Air MFC value: {air_mfc_value:.2f}")
    print(f"Calculated Vac MFC value: {vac_mfc_value:.2f}")


if __name__ == "__main__":
    main()
    input("Plots displayed. Press Enter to exit...")