'''
dilutor_calibration.py

Loads calibration tables for each MFC (main olfa, air, vacuum) and fits linear model to each.
For the desired dilution value, calculates setpoint for air and vacuum MFCs (to match main olfa MFC).

Author:         Shannon Toole
Created:        4/09/2026
Last Modified:  4/17/2026
'''


import os, csv
import numpy as np
import matplotlib.pyplot as plt
plt.ion()   # Enable interactive mode


# Where the calibration tables are stored
current_dir = os.getcwd()
file_directory = os.path.join(current_dir,'calibration_tables')

# File names
#olfa_file = 'dilutor_olfa.csv'
#air_file = 'dilutor_air.csv'
#vac_file = 'dilutor_vac.csv'
olfa_file = 'olfa_main_2026-04-10.csv'
air_file = 'olfa_air_2026-04-10.csv'
vac_file = 'olfa_vac_2026-04-10.csv'

olfa_file = 'olfa_main_2026-04-10 - Copy.csv'
air_file = 'olfa_air_2026-04-10 - Copy.csv'
vac_file = 'olfa_vac_2026-04-10 - Copy.csv'


def load_csv(full_directory):
    '''
    Give it the full directory (including file name)
    Returns 2 lists: mfc_values, flowmeter_values
    '''

    mfc_values = []
    flowmeter_values = []
    
    with open(full_directory,newline='') as f:
        csv_reader = csv.reader(f)      # Create reader object that will process lines from f (file)
        firstLine = next(csv_reader)    # Skip over header line
        secondLine = next(csv_reader)   # Skip over second line
        
        # Load all of the values in
        for row in csv_reader:
            mfc_values.append(float(row[0]))           # First column (MFC_value)
            flowmeter_values.append(float(row[1]))     # Second column (Flowmeter_value)

    return mfc_values,flowmeter_values

def fit_linear(mfc_values,flowmeter_values):
    '''
    Give it the lists of mfc_values and flowmeter_values, Fits linear to it
    '''

    poly1 = np.polyfit(mfc_values, flowmeter_values, 1)  # 1st degree (linear)  (poly1 is an array)    
    fit1 = np.poly1d(poly1)     # Create polynomial functions from the coefficients (these are polynomial class)
    
    return fit1,poly1           # array, polynomial class

def plot_everything(ax,mfc_values,flowmeter_values,fit_olfa,mfc_vac,flowmeter_vac,fit_vac,mfc_air,flowmeter_air,fit_air):
    '''Plot data points and fitted lines for all 3 MFCs'''

    # Generate smooth x values for plotting the fitted curves
    x_smooth = np.linspace(min(mfc_values), max(mfc_values), 100)

    # Plot original data points
    ax.scatter(mfc_values, flowmeter_values, color='r', s=100, label='Olfa MFC', zorder=5)
    ax.scatter(mfc_vac, flowmeter_vac, color='g', s=100, label='Vacuum MFC', zorder=5)
    ax.scatter(mfc_air, flowmeter_air, color='b', s=100, label='Air MFC', zorder=5)
    # Plot fitted curves
    ax.plot(x_smooth, fit_olfa(x_smooth), 'r-',linewidth=2)
    ax.plot(x_smooth, fit_vac(x_smooth), 'g-', linewidth=2)
    ax.plot(x_smooth, fit_air(x_smooth), 'b-', linewidth=2)

    # Labels and formatting
    ax.set_xlabel('MFC set to (SCCM)', fontsize=12)
    ax.set_ylabel('Flowmeter Reading (Vdc)', fontsize=12)
    ax.set_title('Calibration Results', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.show(block=False)   # Non-blocking (script can continue running)
    plt.pause(0.001)        # Give it time to load the plot

def calculate_mfc_linear(poly_,olfa_FM_dil_value):
    '''use poly1d to calculate MFC value from flowmeter value (simple algebraic inversion)'''
    
    slope = poly_[0]
    intercept = poly_[1]
    mfc_value = (olfa_FM_dil_value-intercept)/slope

    return mfc_value


def main():
    '''Load in the 3 csvs'''
    full_dir_olfa = os.path.join(file_directory,olfa_file)  # Directory for olfa file
    mfc_values,flowmeter_values = load_csv(full_dir_olfa)   # Load the mfc values and flowmeter values    
    full_dir_vac = os.path.join(file_directory,vac_file)
    mfc_vac,flowmeter_vac = load_csv(full_dir_vac)
    full_dir_air = os.path.join(file_directory,air_file)
    mfc_air,flowmeter_air = load_csv(full_dir_air)
    
    '''Calculate the linear fit for main olfa MFC'''
    fit_olfa,poly_olfa = fit_linear(mfc_values,flowmeter_values)
    
    '''Convert the vacuum values'''
    # Get the olfa flowmeter reading at 1000 SCCM (Using the polynomial we just calculated)
    try:
        index = mfc_values.index(1000)
        olfa_FM_1000 = flowmeter_values[index]
    except ValueError:
        print("warning: no olfa value at 1000 was recorded")
        olfa_FM_1000 = fit_olfa(1000)
    
    '''
    try:
        index = mfc_values.index(0)
        olfa_FM_0 = flowmeter_values[index]
    except ValueError:
        print("warning: no olfa value at 0 was recorded")
        olfa_FM_0 = fit_olfa(0)
    '''
    
    # Adjust the vacuum flowmeter values
    vac_FM_adjusted = []
    vac_FM_adjusted = [olfa_FM_1000 - fm_vac_value for fm_vac_value in flowmeter_vac]   # olfa 1000 - vac reading
    
    '''Calculate the linear fit for air and vac MFCs'''
    fit_air,poly_air = fit_linear(mfc_air,flowmeter_air)
    '''
    fit_vac,poly_vac = fit_linear(mfc_vac,flowmeter_vac)
    vac_MFC_0 = (olfa_FM_0-poly_vac[1])/poly_vac[0]
    '''
    
    fit_vac_adj,poly_vac_adj = fit_linear(mfc_vac,vac_FM_adjusted)

    '''Plot it'''
    fig1,ax1 = plt.subplots()
    fig1.canvas.manager.set_window_title("Fig 1")
    plot_everything(ax1,mfc_values,flowmeter_values,fit_olfa,mfc_vac,vac_FM_adjusted,fit_vac_adj,mfc_air,flowmeter_air,fit_air)
    fig1.tight_layout()
    
    '''Enter the dilution number you want'''
    dilute_to = 400
    
    '''Get the olfa flowmeter value at the number we want to dilute to'''
    olfa_FM_dil_value = fit_olfa(dilute_to) # this does not seem to be correct bc it's not linear
    print(f"Dilution value: {dilute_to:.2f}")
    print(f"Olfa FM equivalent: {olfa_FM_dil_value:.4f}")
    label = f"Flowmeter value for {dilute_to} SCCM"
    ax1.axhline(y=olfa_FM_dil_value,color='black',linestyle='--',label=label)
    ax1.legend()
    
    '''Calculate air and vac MFC values'''
    air_mfc_value = calculate_mfc_linear(poly_air,olfa_FM_dil_value)
    vac_mfc_value = calculate_mfc_linear(poly_vac_adj,olfa_FM_dil_value)
    print(f"Calculated Air MFC value: {air_mfc_value:.4f}")
    print(f"Calculated Vac MFC value: {vac_mfc_value:.2f}")


    '''
    # Get the vac MFC value
    # Get the olfa flowmeter value at 1000
    index = mfc_values.index(1000)
    olfa_FM_1000 = flowmeter_values[index]


    # Get the value we are looking for for the vacuum
    vac_FM_value_to_look_for = olfa_FM_1000 - olfa_FM_dil_value

    # Find the vacuum value for that flowmeter value
    poly_vac_shifted = fit_vac - vac_FM_value_to_look_for
    mfc_vac_solution = poly_vac_shifted.roots[0]

       

    # Calculate what that should be for each MFC

    # Get the flowmeter value for the olfa at that value
    flowmeter_value_dilution = fit_olfa(dilute_to)

    # Get the air MFC value for that flowmeter value
    # Subtract the target value to find where polynomial equals flowmeter_reading
    # We want to solve: poly1(x) - flowmeter_reading = 0
    #poly_air_shifted = np.poly1d(poly_air) - flowmeter_value_dilution
    poly_air_shifted = fit_air - flowmeter_value_dilution

    # Find the roots (x values where the equation equals zero)
    mfc_air_solution = poly_air_shifted.roots[0]  # For linear, there's only one real root

    #print(f"Flowmeter reading: {flowmeter_value_dilution}")
    print(f"Calculated Air MFC value: {mfc_air_solution:.2f}")

    # Repeat for vac
    #poly_vac_shifted = fit_vac - flowmeter_value_dilution
    #mfc_vac_solution = poly_vac_shifted.roots[0]
    print(f"Calculated Vac MFC value: {mfc_vac_solution:.2f}")
    '''

    '''
    # solve the equation in reverse
    # Your 2nd degree polynomial coefficients
    #poly2 = np.polyfit(mfc_values, flowmeter_values, 2)  # [a, b, c]
    poly2 = poly_air
    # Given a flowmeter value, find the MFC value
    #target_flowmeter = 340.0  # Your known flowmeter value
    target_flowmeter = flowmeter_value_dilution

    # Rearrange: ax² + bx + c - target = 0
    coefficients = [poly2[0], poly2[1], poly2[2] - target_flowmeter]

    # Solve for x (MFC value)
    solutions = np.roots(coefficients)

    print("Solutions:", solutions)
    print("Real solution:", solutions[0].real if np.isreal(solutions[0]) else solutions[1].real)
    '''


if __name__ == "__main__":
    main()
    input("Plots displayed. Press Enter to exit...")