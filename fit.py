import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Read the CSV files
df1 = pd.read_csv('fastmc0.csv')
df2 = pd.read_csv('MM0.csv')

# Extract the Distance and intensity columns
Distance1 = df1['Distance']
intensity1 = df1['Intensity']
Distance2 = df2['Distance']
intensity2 = df2['Intensity']

# Define the square wave function
def square_wave(x, amplitude, period, phase, offset):
    return amplitude * np.sign(np.sin(2 * np.pi * x / period + phase)) + offset

# Fit the square wave function to the data
p0 = [50, 20, 0, 0]  # Initial guess for the parameters
params, _ = curve_fit(square_wave, Distance1, intensity1, p0=p0)

# Generate the fitted square wave
fitted_wave = square_wave(Distance1, *params)

# Plot the original data and the fitted square wave
plt.plot(Distance1, intensity1, label='Original Data', linewidth=0.5)
plt.plot(Distance1, fitted_wave, label='Fitted Square Wave', linewidth=1)
plt.xlabel('Distance (px)')
plt.ylabel('Intensity (a.u.)')

# Add a square grid with ruler lines
plt.minorticks_on()
plt.tick_params(axis='both', which='both', direction='in', top=True, right=True)

# Display the legend
plt.legend()

# Show the plot
plt.show()