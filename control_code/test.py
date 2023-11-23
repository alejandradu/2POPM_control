import DAXI_template_eSPIM
import MAIN

# temp = DAXI_template_eSPIM.NIDaq(exposure=10, nb_timepoints=5, scan_step=2.5, stage_scan_range=2.5)

test = MAIN.nidaq(exposure_time=10, num_stacks=5, vertical_pixels=512)

## Test mimic external trigger of cameras

# test pulse generation - parallel from ctr1
acq_ctr = test._external_cam_trigger(n_cams=1)
# start acquisition
acq_ctr.start()
print('Pulse sent - acquisition started')
acq_ctr.wait_until_done()
# Stop and clear the task (wait until done does not work)
acq_ctr.close()

# is able to SEND parallel pulses at fastest freq: 200 Hz

# cam trigger works
# coordination with AO OPM waveform (NO truncation) (bc MM will not use the nidaqhub anymore)
# light stimulation - potentially USE THE SAME COUNTER BUT MAYBE INTRODUCE A DELAY