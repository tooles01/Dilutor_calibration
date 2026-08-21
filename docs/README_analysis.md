# Analysis

After getting calibration tables for each MFC, use `dilutor_calibration.py` to plot the calibration values.

******Need to enter the **names of the calibration files** and **value to dilute to** at the top of the script

## What it do

- Loads the 3 calibration files
    <details>

    - For each file:
        - Get the full directory path:
            - current directory + 'calibration_tables' + file name
        - Load the csv in
            - Start at the third row (first two rows are headers)
            - Load everything from column 1 into "mfc_values" [list]
            - Load everything from column 2 into "flowmeter_values" [list]

        Load MFC and flowmeter values from a CSV file.

        Parameters
        ----------
        full_directory : str
            Full path to the CSV file, including the file name and extension.
            The file is expected to have two header rows (which are skipped)
            followed by data rows with at least two columns:
                - Column 1: MFC value
                - Column 2: Flowmeter value

        Returns
        -------
        mfc_values : list of float
            Values from the first column (MFC readings).
        flowmeter_values : list of float
            Values from the second column (Flowmeter readings).

        Notes
        -----
        Assumes the CSV uses a standard comma delimiter and that all data
        rows (after the header) contain valid numeric values in the first
        two columns.
        '''
    </details>

<br>






# Update 8/20/2026
- Sort data from lowest to highest
- Calculate the quadratic fit & R^2 of the entire set of data
- Calculate the equation for the first (low) section
    - While the R^2 is less than 0.9995:
        - Remove one value from the end of the dataset
        - Recalculate R^2
        - Error check: If we get to less than 5 values remaining in the dataset, stop
    - Get the coefficients and the polynomial for this region
    - Get the array of MFC values and flow values for this region
- Prep to calculate data for the next section:
    - Get the max MFC value from the first set
    - Get the index of where that value is within the big set of data
    - Get starting MFC and flow values for the next set
        - Include the last value from set 1
        - Get from that value ---> end of the data





##########################

- Calculates quadratic fit for each MFC
    - We're going to assume this for now because the flow sensor curve is weird
    - Could pos change to linear interpolation between each set of points, depending on number of points
    - or do some stats stuff and find the actual best curve

- Gets the flowmeter value ("ground truth") for the olfa MFC ("ground truth") at the value we want to dilute to


- Prints that out



- Calculates the setting for the air MFC 
    <details>

    calculate_mfc_quadratic



<br>

- Calculates the setting for the vac MFC

<!--
### Converts the vacuum values
- Get the olfa flowmeter reading at 1000 SCCM (Using the polynomial we just calculated)
- 4.91 V
- Adjusted vacuum values = 4.91V (Real 1000 SCCM) - Recorded Vac flowmeter values

<br>

Example:  
When vacuum is set to 900 SCCM, the flowmeter reading is 2.1 V  
Check the olfa plot: 2.1 V = 125 SCCM  
So the vacuum is actually sucking:  
1000 - 125 = 875 SCCM  

Our data to work with 

-->
<br>

<!--
## Dilutor calculation

### Get the olfa flowmeter value at the number we want to dilute to

Example: 970 SCCM = 4.865V

![image](../images/olfa_970_sccm_plot.png)


Now 4.865V is the value we are looking for


### Air MFC: Find the setpoint that had the same flowmeter output

This means it put out the same amount of air as the olfa

Example: 

![image](air_970_sccm_plot.png)


### Vac MFC: find the setpoint that gives us that same flowmeter reading (this one is trickier)

1. Get the olfa flowmeter value at the desired setpoint (ex: 0.2V for 100 SCCM)

Fmo(1000-100)
NOT
Fmo(1000) - Fmo(100)

2. Olfa_FM_1000 - Olfa_FM_spt = Vac_FM[x] (ex: 5V - 0.2V = 4.8V)
3. Plug this into the vacuum curve to find the setpoint we want

-->

## Calculation details


### Equations

$y$ = flow sensor reading  
$F$ = function for given MFC  
$x$ = MFC setting  

### Main olfa MFC
$y = F_0(x_0)$

### Air MFC

$y = F_2(x_2)$

### Vac MFC
$y = F_1 ( x_1, x_0 = 1000)$

---


Get the **flow sensor reading** ($y$) at the desired dilution value using the **main olfa MFC function** ($F_0$)

$y = F_0(x_0)$

<!--
![image](../images/olfa_calibration_plot.png)
-->

Calculate the **air MFC setting** ($x_2$) by plugging that **flow sensor reading** ($y$) into the **air MFC function** ($F_2$)

$y = F_2(x_2)$

Calculate the **vac MFC setting** ($x_1$) by pluggint that **flow sensor reading&** ($y) into the **vac MFC function** ($F_1)$:

$y = F_0(1000-setpoint)$

<!--
NOT THIS
y = F0(1000) - F0(setpoint)
-->