import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read the CSV files
df1 = pd.read_csv('fastmc1.csv')
df2 = pd.read_csv('MM1.csv')

# Extract the Distance and intensity columns
Distance1 = df1['Distance']
intensity1 = df1['Intensity']
Distance2 = df2['Distance']
intensity2 = df2['Intensity']

# Subtract the intensity values
n = 15

# Calculate the average of every group of 10 values
grouped_average = [np.mean(intensity1[i:i+n]) for i in range(0, len(intensity1), n)]
grouped_average2 = [np.mean(intensity2[i:i+n]) for i in range(0, len(intensity2), n)]

# Create an array of x-values for the grouped averages
x_values = np.arange(0, len(grouped_average) * n, n)
diff = [grouped_average[i] - grouped_average2[i] for i in range(len(grouped_average))]

# Plot the grouped averages
plt.plot(x_values, grouped_average, label='FastMC', linewidth=0.75)
plt.plot(x_values, grouped_average2, label='MM', linewidth=0.75)
#plt.plot(x_values, diff, label='Difference', linewidth=0.75, linestyle='--')
plt.xlabel('Distance (px)')
plt.ylabel('Average Intensity (a.u.)')

# Add a square grid with ruler lines
plt.grid(True, which='both', linestyle=':', linewidth=0.2)
plt.minorticks_on()
plt.tick_params(axis='both', which='both', direction='in', top=True, right=True)

# Display the legend
plt.legend()

# Show the plot
plt.show()