# Analysis

After getting calibration tables for each MFC, use `dilutor_calibration.py` to plot the calibration values.

******Need to enter the **names of the calibration files** and **value to dilute to** at the top of the script  
<br>

#
# How does it work?

---

## Load the 3 calibration files
```python
mfc_values, flowmeter_values = load_csv(file_path_olfa)
```

#### load_csv
```mfc_values, flowmeter_values``` : list of float

<details>

- Get the full directory path:
    - current directory + "\\calibration_tables\\" + ```file name``` (including extension)
- Load the csv in
    - Start at the third row (first two rows are headers)
    - Load everything from column 1 into "mfc_values" [list]
    - Load everything from column 2 into "flowmeter_values" [list]

Note:
Assumes the CSV uses a standard comma delimiter and that all data rows (after the header) contain valid numeric values in the first two columns.
</details>

---
## Calculate multiple equations for each MFC
```python
olfa_equations = fit_piecewise_equations(mfc_values, flowmeter_values)
```
<br>

## fit_piecewise_equations

### Initial setup
- Initialize empty list of dicts    <!--# TODO what will this be-->  
- Change data type to numpy.ndarray
- Sort data from lowest to highest


### Get the data & equations for the first section
```python
mfc_vals_section, flow_vals_section, coeffs_section, poly1d_section, r2_section = calculate_section(mfc_values, flowmeter_values)
```
```mfc_vals_section, flow_vals_section``` --> Data for this section  
```coeffs_section, poly1d_section, r2_section``` --> Equations/etc for this section
    
#### calculate_section

- Calculates quadratic fit for the data
- If the R^2 of this is < 0.9995:
    - Remove the last value from the dataset and recalculate
    - Keep doing this until we have a small dataset and an equation that fits well  

<details><summary>More Details</summary>

- Calculate quadratic fit for the given data (quad_coeffs_0 = coefficients)
- Calculate R^2 for the data & the quadratic (r2_0)
- While R^2 < 0.9995:
    - Remove one data point from the end of each array
    - Calculate quadratic fit and R^2 again
- Return the new dataset

<br>

**Parameters**  
```mfc_values, flowmeter_values``` : numpy.ndarray

**Returns**  
```mfc_vals_section, flow_vals_section``` : numpy.ndarray  
    ---> Shrunk down dataset that fits this equation  

```coeffs_section``` : numpy.ndarray  
    ---> Coefficients for the equation that fits this data  

```poly1d_section``` : numpy.poly1d  
    ---> Polynomial class (for easy plotting) <!--# TODO maybe don't need to return this-->  

```r2_section``` : numpy.float64  
    ---> R^2 for this equation/this section
</details>


### Add this data to the olfa list of dicts
```python
this_section_dict = {
    "mfc_values": mfc_vals_section,
    "flowmeter_values": flow_vals_section,
    "coefficients": coeffs_section,
    "poly1d": poly1d_section,
    "r_2": r2_section
}
olfa_data_list.append(this_section_dict)
```

#### Initialize mfc_vals_prev_section
```python
mfc_vals_prev_section = mfc_vals_section
```


### Now loop through the rest of the data
Grab the next set of data (Start from max value of the prevous section ---> end of ```mfc_values```)  
Run the same thing: Shrink the data down until you can make a quadratic fit with a good R^2  
Add this data to the olfa list of dicts  

<details>
<br>

**Loop until we hit the end of the data:**

- Define new section:
    - max value of the previous section ---> end of ```mfc_values```

- Get the data and equations for this section
    ```python
    mfc_vals_section,flow_vals_section,coeffs_section,poly1d_section,r2_section = calculate_section(mfc_values_this_region,flow_values_this_region)
    ```

- Add to the olfa list of dicts
    ```python
    this_section_dict = {
        "mfc_values": mfc_vals_section,
        "flowmeter_values": flow_vals_section,
        "coefficients": coeffs_section,
        "poly1d": poly1d_section,
        "r_2": r2_section
    }
    olfa_data_list.append(this_section_dict)
    ```

- Reset ```mfc_vals_prev_section```
    ```python
    mfc_vals_prev_section = mfc_vals_section
    ```
</details>


### Finally: return the list of dicts
Each dict in the list contains all of the info for one section of data.  
```python
return olfa_data_list
```

<br>

---
## Use these equations to get the MFC settings for a particular flow rate

To be continued..................