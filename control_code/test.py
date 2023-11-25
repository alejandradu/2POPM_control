import DAXI_template_eSPIM
import MAIN
import pco
import time

time_points = 300

test = MAIN.nidaq(time_points = time_points,
                  time_points_wait_time = 0.0,
                  exposure_time = 25e-3,
                  mode = "FAST",    # TODO: verify all the preset modes like this
                  multi_d = False,
                  cam_trigger_delay = 0.0,
                  samples_per_cycle=50,
                  rf_freq = 100.0)  # set this very low for testing


# -------- Measure camera parameters

# print(test.get_cam_params())
# print(test.get_total_acq_time())

# -------- Test external camera trigger

# NOTE: you have to set MM to Multicam = core cam so that trigger settings are applied to both
# TODO: really verify the cam exp status pulses are synchronous

#print("max fps: ", test._get_trigger_stack_freq())

## Parallel pulse generation
# loops = time_points if test.multi_d else 1

# acq_ctr = test._external_cam_trigger()

# for i in range(loops):
#     # trigger camera for this stack
#     acq_ctr.start()
#     acq_ctr.wait_until_done(test.get_total_acq_time())   # arg of wait until done has to be changed
#     acq_ctr.stop()
#     # min time between stacks
#     time.sleep(0.0) 
    
#      # TODO: measure system delay introduced with sleep and the start-stop at every iteration

# # close remaining trigger
# acq_ctr.close()

# -------- Test internal exposure trigger

# Observe coordination: ctr0 Output and EXP OUT
# Observe frequency (sampling rate) and number of samples from ctr0 Output

# acq_ctr = test._external_cam_trigger()
# exp_ctr = test._internal_exposure_trigger()

# exp_ctr.start()
# acq_ctr.start()
# acq_ctr.wait_until_done(test.get_total_acq_time())
# acq_ctr.stop()

# exp_ctr.close()
# acq_ctr.close()

# -------- Test galvo waveform 

# -------- Test AOTF waveform 

# print(test._get_trigger_stack_freq())

test.acquire()

# -------- Test lasers digital signals

# -------- Test full acquisition 