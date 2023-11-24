import DAXI_template_eSPIM
import MAIN
import pco

# temp = DAXI_template_eSPIM.NIDaq(exposure=10, nb_timepoints=5, scan_step=2.5, stage_scan_range=2.5)

test = MAIN.nidaq(exposure_time=10, num_stacks=5, vertical_pixels=512, stack_interval=2.5, z_start=0, z_end=2.5, z_step=2.5)
# max frame rate: 10 ms exposure+
## Test mimic external trigger of cameras

# test pulse generation - parallel from ctr1
acq_ctr = test._external_cam_trigger(n_cams=1, freq= 5, mode="fast")
# start acquisition
acq_ctr.start()
print('Pulse sent - acquisition started')
acq_ctr.wait_until_done()
# Stop and clear the task (wait until done does not work)
acq_ctr.close()

# is able to SEND parallel pulses at fastest freq: 200 Hz

# cam trigger works
# TEST WITH BOTH INTERNALLY TRIGGERED: DOES THE IMAGE SHOW UP THE SAME?
# coordination with AO OPM waveform (NO truncation) (bc MM will not use the nidaqhub anymore)
# light stimulation - potentially USE THE SAME COUNTER BUT MAYBE INTRODUCE A DELAY

# EXPOSURE TIME IS MIN 1/FPS

# MM can't be open to get these
# test.get_cam_params('frame time ns')

# {'serial': 61006126, 'type': 'pco.edge 4.2 CL', 'sub type': 0, 'interface type': 'Camera Link ME4', 'min exposure time': 0.0001, 'max exposure time': 10.0, 'min exposure step': 1e-05, 'min delay time': 0.0, 'max delay time': 1.0, 'min delay step': 1e-05, 'max 
# width': 2060, 'max height': 2048, 'min width': 40, 'min height': 16, 'roi steps': (20, 1), 'bit resolution': 16, 'roi is vert symmetric': True, 'roi is horz symmetric': False, 'has timestamp': True, 'has ascii-only timestamp': False, 'has acquire': True, 'has 
# extern acquire': True, 'has metadata': False, 'has ram': False, 'pixelrates': [95333333, 272250000], 'binning horz vec': [1, 2, 4]}

# {'frame time ns': 28442854, 'frame time s': 0, 'exposure time ns': 9999441, 'exposure time s': 0, 'trigger system delay ns': 4294967295, 'trigger system jitter ns': 4294967295, 'trigger delay ns': 0, 'trigger delay s': 0}