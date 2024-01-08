import MAIN2
import pco
import time
import nidaqmx
import math
import numpy as np

nidaq = MAIN2.nidaq(
            num_stacks = 10,                # number of 3D stacks if multi d, number of frames if not
            stack_delay_time = 0.0,        # s. time between acquiring any 2 stacks
            exposure_time = 100e-3,           # s. effective exposure will be less due to system delay
            readout_mode = "fast",              # camera readout mode "fast" or "slow"
            lightsheet = False,               # lightsheet mode
            multi_d = False,                  # multidimensional acquisition
            z_start = 0.0,                  # microm. start of z stack
            z_end = 0.0,                            # ASSUMING 175 nm = 20 deg
            num_z_slices = 0,                       # TODO: is it more useful to have a step or a number of slices?
            image_height = 2048,      # px. vertical ROI. Defines frame readout time
            image_width = 2048,        # px. horizontal ROI
            frame_delay_time = 0.0,         # ms. optional delay after each frame trigger
            samples_per_exp = 10,           # sampling to write data for each cam exposure >= 2 by nyquist thm.
            samples_per_stack = 100,         # sampling to write data for each stack
            rf_freq = 1e6,                   # RF frequency of AOTF
            duty_cycle=0.5,
            led_control_mode = "Trigger",  # "trigger" or "modulation"
            led_trigger_func = lambda x: math.sin(4*np.pi*x)**2)        # function of time for the stack acquisition      


# # 1. Tets params for not multi_d (stack time = frame time or exposure time)
# # set exposure_time = 5 < frame time
# print("frame time: ", nidaq._get_frame_time())
# print("stack time: ", nidaq._get_stack_time())
# # set exposure_time = 100 > frame time
# print("stack time: ", nidaq._get_stack_time())
# print("acq time: ", nidaq._get_total_acq_time())


# # 2. Test stack trigger by itself
# stack_trigger = nidaq._stack_trigger()
# # connect oscilloscope to ctr0 output and observe pulses
# stack_trigger.start()
# stack_trigger.wait_until_done(nidaq._get_total_acq_time())
# stack_trigger.stop()
# stack_trigger.close()


# # 3. Test stack trigger with exposure trigger
# exp_trigger = nidaq._exposure_trigger()
# # connect second channel of oscilloscope to ctr1 output
# exp_trigger.start()
# stack_trigger.start()
# stack_trigger.wait_until_done(nidaq._get_total_acq_time())
# stack_trigger.stop()
# exp_trigger.stop()
# stack_trigger.close()
# exp_trigger.close()


# # set multi_d = True, z_slices = 10, z_start & end CLARIFY UNITS (or put voltage directly)
# print("stack time: ", nidaq._get_stack_time())
# print("acq time: ", nidaq._get_total_acq_time())


# # 4. Test stack trigger with galvo waveform
# # connect second channel of oscilloscope to ao0 output - observe how fast the sawtooth decays
# task_galvo = nidaq._create_ao_task()
# data_galvo = nidaq._get_ao_galvo_data()
# task_galvo.timing.cfg_sample_clk_timing(rate=nidaq.stack_sampling_rate, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, 
#                                     samps_per_chan= nidaq.samples_per_stack)
# task_galvo.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=nidaq.ctr0_internal, trigger_edge=nidaqmx.constants.Edge.RISING)
# task_galvo.triggers.start_trigger.retriggerable = True
# task_galvo.write(data_galvo, auto_start=False)
# task_galvo.start()

# stack_trigger.start()
# stack_trigger.wait_until_done(nidaq.get_total_acq_time())
# stack_trigger.stop()

# task_galvo.stop()
# task_galvo.close()
# stack_trigger.close()


# 5. Test all
# connect first channel of oscilloscope to ctr1 output (blue is ctr1 now)
nidaq.acquire()

