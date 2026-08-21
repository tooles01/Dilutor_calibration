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

# --- R² ---
def r_squared(y_actual, y_predicted):
    ss_res = np.sum((y_actual - y_predicted) ** 2)
    ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)
    return 1 - (ss_res / ss_tot)

def calculate_region_stats(mfc_vals_this_region,flow_vals_this_region):
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
        r^2 value?
    '''
    r2_threshold = 0.9995  # TODO probably can change this to .999

    # --- Calculate initial quadratic & R^2 for the entire dataset
    quad_coeffs_0 = np.polyfit(mfc_vals_this_region,flow_vals_this_region,2)
    quad_p_0 = np.poly1d(quad_coeffs_0)
    r2_0 = r_squared(flow_vals_this_region, quad_p_0(mfc_vals_this_region))

    # --- Remove one value from the end, recalculate R^2 until it's > 0.9995
    while r2_0 < r2_threshold:
        # Remove one mfc value and one flowmeter value from the end
        mfc_vals_this_region = mfc_vals_this_region[0:(len(mfc_vals_this_region)-1)]
        flow_vals_this_region = flow_vals_this_region[0:(len(flow_vals_this_region)-1)]

        # Check how many values are left (if we're down to 5, something prob went wrong)
        i = len(mfc_vals_this_region)
        if i < 5:
            print('stop - something went wrong')

        # Recalculate quadratic & R^2 for the shortened dataset
        quad_coeffs_1 = np.polyfit(mfc_vals_this_region,flow_vals_this_region,2)
        quad_p_1 = np.poly1d(quad_coeffs_1)
        r2_0 = r_squared(flow_vals_this_region,quad_p_1(mfc_vals_this_region))

    # When done: print out the stats
    print('got one')
    print(f"   MFC values: \t\t {min(mfc_vals_this_region)} - {max(mfc_vals_this_region)}")
    print(f"   R^2: \t\t {r2_0}")
    print(f"   # of values: \t {len(mfc_vals_this_region)}")

    # Return everything
    return mfc_vals_this_region,flow_vals_this_region,quad_coeffs_1,quad_p_1,r2_0

def fit_linear_1(mfc_values,flowmeter_values):
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
    '''
    
    # --- Plot for debugging
    fig1, (ax1,ax2) = plt.subplots(1,2, figsize=(12,5),sharex=True,sharey=True)
    ax1.scatter(mfc_values,flowmeter_values)
    ax1.set_xlabel('MFC setting (SCCM)')
    ax1.set_ylabel('Flowmeter Reading')
    ax1.set_title('Initial data')
    ax2.scatter(mfc_values,flowmeter_values)
    ax2.set_xlabel('MFC setting (SCCM)')
    ax2.set_ylabel('Flowmeter Reading')
    ax2.set_title('Overlaid equation 1')
    ax1.grid(True)
    ax2.grid(True)
    ax1.set_xlim(-50, 1050)
    ax1.set_ylim(-.5, 5.5)
    fig1.canvas.manager.set_window_title('Initial data')

    # --- Initial Setup
    # Convert data from list to numpy.ndarray
    mfc_values = np.array(mfc_values)
    flowmeter_values = np.array(flowmeter_values)
    
    # Sort data from lowest --> highest
    sort_idx = np.argsort(mfc_values)
    mfc_values = mfc_values[sort_idx]
    flowmeter_values = flowmeter_values[sort_idx]
    
    # --- Get the data & equations for this section
    mfc_vals_1,flow_vals_1,coeffs_1,p_1,r2_1 = calculate_region_stats(mfc_values,flowmeter_values)

    # Show me just the final equation that worked
    x_vals = np.linspace(min(mfc_vals_1),max(mfc_vals_1),100)
    ax2.plot(x_vals, p_1(x_vals), label='Equation 1', color='orange')
    ax2.legend(loc='upper left')

    # --- Plot this section
    plt.figure()
    plt.scatter(mfc_vals_1,flow_vals_1)
    x_1 = np.linspace(min(mfc_vals_1),max(mfc_vals_1),100)
    plt.plot(x_1,p_1(x_1))
    plt.grid(True)
    plt.xlabel('MFC values')
    plt.ylabel('Flow sensor')
    plt.title('First equation')
    fig2 = plt.gcf()
    fig2.canvas.manager.set_window_title('First set of data + equation')#


    # -------------------------------------------------------------
    # --- Reset everything for round 2
    # now start at the next value above this 
    # find the index of the highest value in this first set
    # highest value in the first dataset
    max_mfc_set_1 = max(mfc_vals_1)
    # index of that value within the big dataset ('where' outputs a tuple, so need the [0][0] at the end)
    index = np.where(mfc_values == max_mfc_set_1)[0][0]

    # Get the starting data
    mfc_values_this_region_2 = mfc_values[index:len(mfc_values)]
    flow_values_this_region_2 = flowmeter_values[index:len(mfc_values)]

    # Calculate the initial quadratic and R^2
    quad_coeffs_2 = np.polyfit(mfc_values_this_region_2,flow_values_this_region_2,2)
    quad_p_2 = np.poly1d(quad_coeffs_2)
    r2_2 = r_squared(mfc_values_this_region_2,quad_p_2(flow_values_this_region_2))

    # X-values for plotting
    x_vals = np.linspace(min(mfc_values_this_region_2),max(mfc_values_this_region_2),100)

    # --- Remove one value from the end, recalculate R^2 until it's > 0.9995
    r2_threshold = 0.9995  # TODO probably can change this to .999
    while r2_2 < r2_threshold:
        # Remove one mfc value and one flowmeter value from the end
        mfc_values_this_region_2 = mfc_values_this_region_2[0:(len(mfc_values_this_region_2)-1)]
        flow_values_this_region_2 = flow_values_this_region_2[0:len(flow_values_this_region_2)-1]

        # How many values are left
        i = len(mfc_values_this_region_2)
        if i < 5:
            print('stop')

        # Recalculate R^2
        quad_coeffs_2 = np.polyfit(mfc_values_this_region_2,flow_values_this_region_2,2)
        quad_p_2 = np.poly1d(quad_coeffs_2)
        r2_2 = r_squared(flow_values_this_region_2,quad_p_2(mfc_values_this_region_2))
        
        # Show me what this looks like
        ax2.plot(x_vals, quad_p_2(x_vals))
            
    # --- Data for the second equation
    print('got the second one')
    coeffs_2 = quad_coeffs_2
    p_2 = quad_p_2

    # X and Y values
    mfc_vals_2 = mfc_values_this_region_2
    flow_vals_2 = flow_values_this_region_2

    # Print out what it is
    print(f"   MFC values: \t {min(mfc_vals_2)} - {max(mfc_vals_2)}")
    print(f"   R^2: \t {round(r2_2,5)}")
    print(f"   # of values: \t {len(mfc_vals_2)}")
    
    # show me to me rachel
    plt.figure()
    plt.scatter(mfc_vals_2,flow_vals_2)
    x_2 = np.linspace(min(mfc_vals_2),max(mfc_vals_2),100)
    plt.plot(x_2,p_2(x_2))
    plt.grid(True)
    plt.xlabel('MFC values')
    plt.ylabel('Flow sensor')
    plt.title('Second equation')
    fig2 = plt.gcf()
    fig2.canvas.manager.set_window_title('Second set of data + equation')

    # Show these equations on a single plot


    # TODO continue doing this, save the coefficients or whatever



    '''
    Splitting into three sections: linear, quad, linear
    this works great for the first two sections, but we would need to add more sections
    the high section is just crazy
    '''
    
    mfc_values = np.array(mfc_values)
    flowmeter_values = np.array(flowmeter_values)

    # Sort by SCCM
    sort_idx = np.argsort(mfc_values)
    mfc_values = mfc_values[sort_idx]
    flowmeter_values = flowmeter_values[sort_idx]

    # --- Formulaic Boundary Detection ---
    # Calculate first derivative (slope between consecutive points)
    d_volts = np.diff(flowmeter_values)
    d_sccm  = np.diff(mfc_values)
    slope   = d_volts / d_sccm  # local slope at each interval

    # Normalize slope to detect relative changes
    slope_norm    = slope / slope.max()
    slope_smooth = slope_norm
    #slope_smooth  = np.convolve(slope_norm, np.ones(3)/3, mode='same')  # smooth slightly

    #plt.figure()
    #plt.scatter(mfc_values,flowmeter_values)
    #plt.xlabel('MFC setting (SCCM)')
    #plt.ylabel('Flowmeter Reading')

    # Show me what this looks like
    fig1, (ax1,ax2) = plt.subplots(1,2, figsize=(12,5))
    ax1.scatter(mfc_values,flowmeter_values)
    ax1.set_xlabel('MFC setting (SCCM)')
    ax1.set_ylabel('Flowmeter Reading')
    mfc_vals_averaged = [(mfc_values[i] + mfc_values[i+1]) / 2 for i in range(len(mfc_values) - 1)]
    ax2.scatter(mfc_vals_averaged,slope_norm)
    ax2.set_xlabel('MFC setting')
    ax2.set_ylabel('Slope normalized')
    ax1.grid(True)
    ax2.grid(True)


    # Find where slope drops below thresholds
    LOW_THRESH  = 0.85   # slope is still steep (low region) (linear)
    HIGH_THRESH = 0.35   # slope has compressed significantly (high region)

    # Boundary 1: first point where normalized slope drops below LOW_THRESH
    boundary_low_idx  = np.argmax(slope_smooth < LOW_THRESH)    # if we don't sort, this doesn't work
    boundary_low_sccm = mfc_values[boundary_low_idx]

    # Boundary 2: first point where normalized slope drops below HIGH_THRESH
    boundary_high_idx  = np.argmax(slope_smooth < HIGH_THRESH)
    boundary_high_sccm = mfc_values[boundary_high_idx]

    print(f"Auto-detected boundaries:")
    print(f" Slope drops below 0.85, this is the transition to the middle region")
    print(f"  LOW  → MID1  transition: {boundary_low_sccm:.0f} SCCM")
    print(f" Slope drops below 0.35, this is the transition to the high region")
    print(f"  MID1  → HIGH transition: {boundary_high_sccm:.0f} SCCM")

    # --- Split into regions ---
    mask_low  = mfc_values <= boundary_low_sccm
    mask_mid  = (mfc_values > boundary_low_sccm) & (mfc_values <= boundary_high_sccm)
    mask_high = mfc_values > boundary_high_sccm

    sccm_low,  volts_low  = mfc_values[mask_low],  flowmeter_values[mask_low]
    sccm_mid,  volts_mid  = mfc_values[mask_mid],  flowmeter_values[mask_mid]
    sccm_high, volts_high = mfc_values[mask_high], flowmeter_values[mask_high]

    print(f"\nRegion sizes: LOW={len(sccm_low)}, MID1={len(sccm_mid)}, HIGH={len(sccm_high)} points")

    # --- Fit each region ---
    coeffs_low  = np.polyfit(sccm_low,  volts_low,  1)  # linear
    coeffs_mid  = np.polyfit(sccm_mid,  volts_mid,  2)  # quadratic
    coeffs_high = np.polyfit(sccm_high, volts_high, 1)  # linear

    p_low  = np.poly1d(coeffs_low)
    p_mid  = np.poly1d(coeffs_mid)
    p_high = np.poly1d(coeffs_high)

    print(f"\nFitted Equations:")
    print(f"  LOW  (0–{boundary_low_sccm:.0f}):   V = {coeffs_low[0]:.6f} * SCCM + {coeffs_low[1]:.6f}")
    print(f"  MID1  ({boundary_low_sccm:.0f}–{boundary_high_sccm:.0f}): V = {coeffs_mid[0]:.2e} * SCCM² + {coeffs_mid[1]:.6f} * SCCM + {coeffs_mid[2]:.6f}")
    print(f"  HIGH ({boundary_high_sccm:.0f}–{mfc_values.max():.0f}): V = {coeffs_high[0]:.6f} * SCCM + {coeffs_high[1]:.6f}")
    '''
    # --- R² ---
        def r_squared(y_actual, y_predicted):
            ss_res = np.sum((y_actual - y_predicted) ** 2)
            ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)
            return 1 - (ss_res / ss_tot)
    '''
    
    print(f"\nR² Values:")
    print(f"  LOW:  {r_squared(volts_low,  p_low(sccm_low)):.6f}")
    print(f"  MID1:  {r_squared(volts_mid,  p_mid(sccm_mid)):.6f}")
    print(f"  HIGH: {r_squared(volts_high, p_high(sccm_high)):.6f}")

    # --- Slope diagnostic plot (helpful for tuning thresholds) ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Slope plot
    axes[0].plot(mfc_values[:-1], slope_smooth, color='purple', label='Normalized Slope (smoothed)')
    axes[0].axhline(LOW_THRESH,  color='blue', linestyle='--', label=f'Low threshold ({LOW_THRESH})')
    axes[0].axhline(HIGH_THRESH, color='red',  linestyle='--', label=f'High threshold ({HIGH_THRESH})')
    axes[0].axvline(boundary_low_sccm,  color='blue', linestyle=':', alpha=0.7)
    axes[0].axvline(boundary_high_sccm, color='red',  linestyle=':', alpha=0.7)
    axes[0].set_xlabel("SCCM")
    axes[0].set_ylabel("Normalized Slope")
    axes[0].set_title("Slope-Based Boundary Detection")
    axes[0].legend()
    axes[0].grid(True)

    # Fit plot
    axes[1].scatter(mfc_values, flowmeter_values, color='gray', s=20, label='Data', zorder=5)
    for x, p, label, color in [
        (sccm_low,  p_low,  f"LOW (0–{boundary_low_sccm:.0f})",                   'blue'),
        (sccm_mid,  p_mid,  f"MID1 ({boundary_low_sccm:.0f}–{boundary_high_sccm:.0f})", 'green'),
        (sccm_high, p_high, f"HIGH ({boundary_high_sccm:.0f}–{mfc_values.max():.0f})",   'red'),
    ]:
        x_fit = np.linspace(x.min(), x.max(), 300)
        axes[1].plot(x_fit, p(x_fit), color=color, linewidth=2, label=f"Fit: {label}")
    axes[1].axvline(boundary_low_sccm,  color='blue', linestyle=':', alpha=0.5)
    axes[1].axvline(boundary_high_sccm, color='red',  linestyle=':', alpha=0.5)
    axes[1].set_xlabel("SCCM")
    axes[1].set_ylabel("Voltage (V)")
    axes[1].set_title("Piecewise Fit with Auto Boundaries")
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.show()

    
    '''
    # ── Split into three regions ───────────────────────────────────────────
    mask_low  = mfc_values <= 99
    mask_mid  = (mfc_values >= 99) & (mfc_values <= 798)
    mask_high = mfc_values >= 798

    mfc_vals_low,  flowmet_low  = mfc_values[mask_low],  flowmeter_values[mask_low]
    mfc_vals_mid,  flowmet_mid  = mfc_values[mask_mid],  flowmeter_values[mask_mid]
    mfc_vals_high, flowmet_high = mfc_values[mask_high], flowmeter_values[mask_high]

    # ── Region 1: Linear fit (0–99 SCCM) ──────────────────────────────────
    coeffs_low = np.polyfit(mfc_vals_low, flowmet_low, 1)
    p_low = np.poly1d(coeffs_low)
    print(f"LOW  (0-99):    V = {coeffs_low[0]:.6f}·SCCM + {coeffs_low[1]:.6f}")

    # ── Region 2: Quadratic fit (99–798 SCCM) ─────────────────────────────
    coeffs_mid = np.polyfit(mfc_vals_mid, flowmet_mid, 2)
    p_mid = np.poly1d(coeffs_mid)
    print(f"MID  (99-798):  V = {coeffs_mid[0]:.2e}·SCCM² + "
        f"{coeffs_mid[1]:.6f}·SCCM + {coeffs_mid[2]:.6f}")

    # ── Region 3: Linear fit (798–963 SCCM) ───────────────────────────────
    coeffs_high = np.polyfit(mfc_vals_high, flowmet_high, 1)
    p_high = np.poly1d(coeffs_high)
    print(f"HIGH (798-963): V = {coeffs_high[0]:.6f}·SCCM + {coeffs_high[1]:.6f}")

    # ── R² helper ─────────────────────────────────────────────────────────
    def r_squared(y_actual, y_predicted):
        ss_res = np.sum((y_actual - y_predicted) ** 2)
        ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)
        return 1 - ss_res / ss_tot

    print(f"\nR² LOW:  {r_squared(flowmet_low,  p_low(mfc_vals_low)):.6f}")
    print(f"R² MID:  {r_squared(flowmet_mid,  p_mid(mfc_vals_mid)):.6f}")
    print(f"R² HIGH: {r_squared(flowmet_high, p_high(mfc_vals_high)):.6f}")
    '''    

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
    # Linear
    fit_linear_1(mfc_values,flowmeter_values)


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