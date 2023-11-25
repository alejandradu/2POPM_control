import DAXI_template_eSPIM
import MAIN
import pco
import time

test = MAIN.nidaq(time_points = 5,
                  time_points_interval= 0.0,
                  exposure_time = 1e-3,
                  mode = "fast",
                  multi_d = True,
                  cam_trigger_delay = 0.0)


# -------- Measure camera parameters

sys_delay = test.get_cam_params("trigger system delay ns")
sys_jitter = test.get_cam_params("trigger system jitter ns")
frame_time = test.get_cam_params("frame time ns")
print(sys_delay, sys_jitter, frame_time)

# -------- Test external camera trigger

# Parallel pulse generation: measure delay of EXP OUT matches sys delay + jitter
# Imaging at fastest frame rate for given exposure time
acq_ctr = test._external_cam_trigger()
acq_ctr.start()
acq_ctr.wait_until_done()
acq_ctr.close()

# -------- Test internal exposure trigger

# Connect cam EXP OUT to PFI0.
# Connect picoscope (voltimeter) to ctr0 Output port.
# Observe coordination: ctr0 Output and EXP OUT
# Observe frequency (sampling rate) and number of samples from ctr0 Output

exp_ctr = test._internal_exposure_trigger()
exp_ctr.start()
acq_ctr.start()
acq_ctr.wait_until_done()
acq_ctr.close()
time.sleep(1 / test._get_trigger_stack_freq())  
exp_ctr.close()

# -------- Test galvo waveform 

# -------- Test AOTF waveform 

# -------- Test lasers digital signals

# -------- Test full acquisition 