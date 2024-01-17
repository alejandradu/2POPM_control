import numpy as np

# Three spherical caps: 1 and 2 are centered on the z-axis, 3 is pi
# radians wide
cap_1_width = np.arcsin(1.49/1.51) # radians
cap_2_width = np.arcsin(0.96)       # radians
sheet_half_angle = 3 * np.pi/180    # radians
cap_3_tilt = (np.pi/2 - cap_1_width) + sheet_half_angle # radians, in yz plane
# Generate random points on the surface of a sphere
num_points = int(3e4)
phi = np.random.uniform(0, 2*np.pi, num_points)
theta = np.arccos(np.random.uniform(-1, 1, num_points))
# Calulate z in a rotated frame where cap 2 is centered on the (new) z-axis:
z_rotated = (np.sin(cap_3_tilt) * np.sin(theta) * np.sin(phi) +
             np.cos(cap_3_tilt) * np.cos(theta))
# Check which caps each point occupies:
in_cap_1 = theta < cap_1_width
in_cap_2 = theta < cap_2_width
in_cap_3 = z_rotated > 0
# Estimate the fraction of the first cap covered by the second and third caps
ratio_1_2 = (np.count_nonzero(in_cap_1 & in_cap_2) /
             np.count_nonzero(in_cap_1))
ratio_2_3 = (np.count_nonzero(in_cap_2 & in_cap_3) /
             np.count_nonzero(in_cap_2))
print("Spherical cap 1 half-angle: %0.3fpi radians (%0.2f degrees)"%(
    cap_1_width / np.pi, cap_1_width * 180/np.pi))
print("Spherical cap 2 half-angle: %0.3fpi radians (%0.2f degrees)"%(
    cap_2_width / np.pi, cap_2_width * 180/np.pi))
print("Spherical cap 3 tilt angle: %0.3fpi radians (%0.2f degrees)"%(
    cap_3_tilt / np.pi, cap_3_tilt * 180/np.pi))
print("Fraction of cap 1 covered by cap 2: %0.5f"%(ratio_1_2))
print("Fraction of cap 2 covered by cap 3: %0.5f"%(ratio_2_3))