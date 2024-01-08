import MAIN2
import pco
import time

# -------------------------- Instructions ----------------------------------- #


# This is a script to run high-speed imaging with one or two (simultaneous) PCO Edge cameras and the NI DAQ card.

# It relies on Micro-Manager as an image viewer only.
# Control over the cameras, the stage (galvo), and the LED is done through the NI DAQ card.
# Control over the lasers is hardware-based.

# Although Micro-Manager has no control over the cameras, the imaging parameters have to 
# agree between this script and Micro-Manager to obtain all the images in the viewer.

# The following instructions indicate how to run different types of acquisition.


# ------ 2D, 2 camera imaging: stacks represent the frames to be taken ------ #

#    In this script:
# 1. Set multi_d = False
# 2. Set num_stacks to the number of frames desired
# 3. Set stack_delay_time to the desired delay between frames (not frame_delay_time), if any
# 4. Set any LED control if desired. If using "software_fraction", led_stack_fraction 
#    is the fraction of time the LED is on during each frame. If using "software_time",
#    led pulse width and frequency is independent of frame acquisition
# 5. Set exposure time, image height, and image width to the desired values
# 6. Set the readout mode as "fast" unless you particularly need the camera sensor to read out in slow mode

# 7. Open Micro-Manager and set: 
#    Core Cam -> Multi Camera
#    Multicam 1  -> pco_camera_1
#    Multicam 1 (trigger mode)  -> External Exp. Ctrl.
#    Multicam 2  -> pco_camera_2
#    Multicam 2 (trigger mode)  -> External Exp. Ctrl.
#    NIDAQ (sequence)  ->  Off

# 8. In Micro-Manager, open "Multi-D Acq":
#    Check "Time Points" and uncheck all other boxes
#    Under "Time Points", set "Counts" to the number of frames desired (num_stacks) + 1
#    Under "Time Points", set "Interval" to the delay between frames (stack_delay_time), if any
#    Check that the time units is seconds (s)

# 9. In Micro-Manager, click "Acquire!"

# 10. Right after, run this script with the run button in the top right corner




# ------ 3D, 2 camera imaging: stacks represent 3D stacks, frames are the z-slices in each ------ #

#    In this script:
# 1. Set multi_d = True
# 2. Set num_stacks to the number of volumes (3D stacks) desired
# 3. Set stack_delay_time to the desired delay (interval) between 3D stacks
# 4. Set z_start and z_end to the desired start and end of the z stack, and num_z_slices to the number of z slices
# 5. Set frame_delay_time to the desired delay between z slices, if any
# 6. Set any LED control if desired. If using "software_fraction", led_stack_fraction 
#    is the fraction of time the LED is on during each 3D stack. If using "software_time",
#    led pulse width and frequency is independent of frame acquisition
# 7. Set exposure time, image height, and image width to the desired values
# 8. Set the readout mode as "fast" unless you particularly need the camera sensor to read out in slow mode

# 9. Open Micro-Manager and set: 
#    Core Cam -> Multi Camera
#    Multicam 1  -> pco_camera_1
#    Multicam 1 (trigger mode)  -> External Exp. Ctrl.
#    Multicam 2  -> pco_camera_2
#    Multicam 2 (trigger mode)  -> External Exp. Ctrl.
#    NIDAQ (sequence)  ->  Off

# 10. In Micro-Manager, open "Multi-D Acq":
#     Check "Time Points" and uncheck all other boxes
#     Under "Time Points", set "Counts" to num_stacks * num_z_slices (total number of frames)
#     Under "Time Points", set "Interval" to zero
#     Check that the time units is seconds (s)

# 11. In Micro-Manager, click "Acquire!"

# 12. Right after, run this script with the run button in the top right corner

# Important: for now, long interval times between stacks might not work with the Micro-Manager viewer



# -------------------------- 1 camera imaging ----------------------------------- #

# In the camera to be inactivated, disconnect the BNC cable from the IN 1 port

# In Micro-Manager, set:
#    Core Cam -> pco_camera_1 or pco_camera_2 (whichever still has the BNC cable connected to IN 1)
#    Multicam 1  -> pco_camera_1
#    Multicam 1 (trigger mode)  -> External Exp. Ctrl.
#    NIDAQ (sequence)  ->  Off

# If Multi-D Acq in Micro-Manager is open, close it and reopen it

# All other steps are the same as above


# -------------------------------- notes ---------------------------------------- #


# You can see acquisition status in Micro-Manager in the home page, next to a yellow bell icon
# that appears while Multi-D Acq is running. 

# If at some point Micro-Manager freezes and does not finish the acquisition, run this script 
# again independently and as many times as needed. This will complete the acquisition in Micro-Manager
# and let you close it and re-start a new one.


# ----------------------------- modify below ------------------------------------ #

scope = MAIN2.nidaq(num_stacks = 10,                      # number of 3D stacks if multi_d, number of frames otherwise
                               stack_delay_time = 1.0,               # sec. time between acquiring any 2 stacks
                               exposure_time = 100e-3,               # sec. camera exposure time. min 100e-6 max 10.0
                               readout_mode = "fast",                # camera readout mode "fast" or "slow". Default to "fast"
                               multi_d = True,                       # multidimensional acquisition
                               z_start = 0.0,                        # microm. start of z stack. min -178.36 
                               z_end = 100.0,                        # microm. end of z stack. max 178.36 
                               num_z_slices = 10,                    # int. number of z slices
                               image_height = 248,                   # px. vertical ROI. Defines frame readout time
                               image_width = 800,                    # px. horizontal ROI
                               frame_delay_time = 0.0,               # sec. optional delay after taking each frame
                               led_trigger = "software_time",        # "hardware", "software_fraction", "software_time" triggering of LED if light control is desired
                               led_stack_fraction_on = 0.5,          # percent of time LED is on during every stack acquisition in software_fraction mode
                               led_time_on = 1.0,                    # sec. time LED is on during acquisition in software_time mode (i.e. LED period)
                               led_frequency = 0.5)                  # pulses/second. Nonzero to pulse the LED for led_time_on at given frequency


# -------------------------- do not modify below --------------------------------- #

# Get parameters
print("Total acquisition time (s): ", scope.get_total_acq_time())
print("Frame rate (frames/s): ", scope._get_trigger_exp_freq())
print("Volumes per second: ", 1/scope.get_stack_time())

# Start acquisition
#scope.acquire()

print(scope._get_do_led_data_no_trigger())
