import DAXI_template_eSPIM
import MAIN

temp = DAXI_template_eSPIM.NIDaq(exposure=10, nb_timepoints=5, scan_step=2.5, stage_scan_range=2.5)

test = MAIN.nidaq()

## Test mimic external trigger of cameras

# test pulse generation - to do3 and do4
acq_ctr = test._external_cam_trigger()
# start acquisition
acq_ctr.start()
print('Pulses sent')
# Stop and clear the task
if acq_ctr.is_task_done():
    print('Pulses received')
    acq_ctr.stop()
acq_ctr.close()