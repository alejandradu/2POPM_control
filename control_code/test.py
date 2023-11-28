import DAXI_template_eSPIM
import MAIN
import pco
import time

time_points = 600

test = MAIN.nidaq(time_points = time_points,
                  time_points_wait_time = 0.0,
                  # BASICALLY 100 FPS
                  exposure_time = 0.011,#5e-3,  # the total cam "fake" exp time REAL ONE = FAKE * DUTY CYCLE IN EXP CTR MODE (+DELAY...)
                  mode = "FAST",    # TODO: verify all the preset modes like this
                  multi_d = False,
                  cam_trigger_delay = 0.0,
                  samples_per_cycle=50,
                  rf_freq = 100.0)  # set this very low for testing

# TODO: fix weird behavior of duty cycle - test so that images are not corrupted (my guess this camera can do readout and exposure at the same time)
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
# going to trigger at max frame rate w exp set to 5 (shouldn't matter) and duty cycle = 0.99, exp = around 0.1

test.acquire()

# -------- Test lasers digital signals

# -------- Test full acquisition 

# get cam params
# cam1 = pco.Camera()
# cam1.sdk.open_camera()
# cam2 = pco.Camera()
# cam2.sdk.open_next_camera()

# print('exposure time: ', cam.sdk.get_delay_exposure_time())
# print('frame rate: ', cam.sdk.get_frame_rate())
# print('roi: ', cam.sdk.get_roi())
# print('mode: ', cam.sdk.get_trigger_mode())
# cam.sdk.set_trigger_mode('external exposure control')
# print('mode: ', cam.sdk.get_trigger_mode())

# test.acquire()