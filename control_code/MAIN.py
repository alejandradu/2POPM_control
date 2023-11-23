import nidaqmx
import nidaqmx.system
import numpy as np
import time

# Create a workflow using the NI-DAQmx Python API to synchronize the 
# acquisition of a camera with the generation of an analog signal to control a 
# galvo mirror and digital signals to control 3 lasers. 
# 3.5 cameras


class nidaq:
    # Channel ports    
    ao0 = "Dev1/ao0"   # OPM galvo
    ao1 = "Dev1/ao1"   
    ai0 = "Dev1/ai0"
    ai1 = "Dev1/ai1"

    # both input and output
    ao2 = "Dev1/ao2"
    ao3 = "Dev1/ao3"
    ao4 = "Dev1/ao4"
    ao5 = "Dev1/ao5"
    ao6 = "Dev1/ao6"
    ao7 = "Dev1/ao7"

    # trigger/counter
    ctr0 = "Dev1/ctr0"    # stack counter
    ctr0_internal = "Dev1/ctr0InternalOutput"   # stack trigger
    ctr1 = "Dev1/ctr1"
    ctr1_internal = "Dev1/ctr1InternalOutput"

    # programmable function I/O (PFI lines)
    PFI0 = "Dev1/PFI0"     # cam1 exposure input
    PFI1 = "Dev1/PFI1"     # idle

    # Digital and timing I/O (not all)
    do0 = "Dev1/port0/line0"   # 488
    do1 = "Dev1/port0/line1"   # 561
    do2 = "Dev1/port0/line2"   # LED (AOTF)
    do3 = "Dev1/port0/line3"   # cam1 trigger
    do4 = "Dev1/port0/line4"   # cam2 trigger

    # constants
    # TODO: check these values
    MAXV_GALVO = 5.0
    MINV_GALVO = 0.0
    REDOUT_CAM1 = None
    READOUT_CAM2 = None
    READOUT_TIME_CAM1 = None   # TODO: verify we need this, different?
    READOUT_TIME_CAM2 = None
    MAX_VERTICAL_PIXELS = None

    # TODO: constants

    def __init__(
            self, 
            exposure_time: float,
            num_stacks: int,
            vertical_pixels: int     # TODO: do we count vertically?
        ):
        """
        Initialize the NI-DAQmx system and create a task for each channel.
        """
        self.exposure_time = exposure_time
        self.num_stacks = num_stacks
        self.num_samples = 10  # HERE - timing purposes (max sample buffer of clock)
        self.readout_time1 = self.READOUT_TIME_CAM1 * vertical_pixels / self.MAX_VERTICAL_PIXELS
        self.readout_time2 = self.READOUT_TIME_CAM2 * vertical_pixels / self.MAX_VERTICAL_PIXELS

    @property
    def sampling_rate(self):
        return self.num_stacks / self.exposure_time

        # TODO: add all instance attributes, including properties
        # TODO: make this specific to volumetric sampling or not - BOTH
        pass

    def _create_ao_task(self):
        """Create the analog output task for the galvo"""
        task_ao = nidaqmx.Task("AO")
        task_ao.ao_channels.add_ao_voltage_chan(self.ao0, min_val=self.MINV_GALVO, max_val=self.MAXV_GALVO)

    def _create_do_tasks(self):
        pass
    # return taskLight, taskCam


    # TODO: get numbers of laser channels, determine line grouping
    # TODO: figure out the purpose of views

    def _get_ao_data(self):
        """Get the array data to write to the ao channel"""
        pass

        # TODO: determine if we can include here the function of the amplifier - VARIABLE PARAM
        # TODO: verify that we don't want data generated in real time
        # TODO: what is the readout time - 
        # TODO: can (should?) all light sources be on at the same time?
        # TODO: we only want the light sources on when the camera is acquiring?

    def _get_do_data(self, *SOME_ARGS):
        """Get the ndarray for the digital ouput of the light sources and cameras"""
        # DIGITAL IS YES/NO SO WILL ONLY HAVE TRUE/FALSE
        # TODO: do the 488 and 561 alternate, then leave the other in
        # the background?
        # TODO: what are the parameter that we typically want to control
        # TODO: cover both cases of using one and 2 cameras? (most likely - 
        # how to adjust the trigger? just leave one trigger and add readouts....)
        pass


    def _external_cam_trigger(self, n_cams: int):
        """sends ONE TTL pulse to the cameras to start acquisition"""
        task_do = nidaqmx.Task("cam_trigger")
        task_do.do_channels.add_do_chan(self.do3)       # start cam1
        if n_cams == 2:  task_do.do_channels.add_do_chan(self.do4)   # start cam2
        task_do.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=1)

        data = [True, True] if n_cams == 2 else [True]

        # write TTL pulse - explicitly start later
        task_do.write(data, auto_start=False)
        
        return task_do


    def _internal_stack_trigger(self):
        """triggers ao and do tasks for each volume stack"""
        task_ctr = nidaqm.Task("stack_trigger")
        task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr0,idle_state=nidaqmx.constants.Level.LOW,freq=self.sampling_rate)
        # set buffer size of the counter per stack
        task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE,samps_per_chan=self.num_samples)
        # counter is activated when cam1 exposure goes up (once for each stack)
        task_ctr.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.PFI0, trigger_edge=nidaqmx.constants.Slope.RISING)
        # new rising exposures will retrigger the counter
        task_ctr.triggers.start_trigger.retriggerable = True

        return task_ctr


    def acquire(self):

        # get light source and camera control
        task_light, task_cam = self._create_do_tasks()
        data_light, data_cam = self._get_do_data()

        # get galvo control
        task_galvo = self._create_ao_tasks()
        data_galvo = self._get_ao_data()
        
        # mimic external camera trigger
        acq_ctr = self._external_cam_trigger()

        # stack trigger
        stack_ctr = self._internal_stack_trigger()

        # sync ao and do tasks with stack counter clock
        src = self.ctr0_internal
        rate = self.sampling_rate
        mode = nidaqmx.constants.AcquisitionType.FINITE
        # rate is the max rate of the source
        task_galvo.timing.cfg_sample_clk_timing(rate=rate, sample_mode=mode, source=src)
        task_light.timing.cfg_sample_clk_timing(rate=rate, sample_mode=mode, source=src)
        task_cam.timing.cfg_sample_clk_timing(rate=rate, sample_mode=mode, source=src)

        # activate start trigger: wait for external camera trigger
        stack_ctr.start()

        for i in range(self.num_stacks):
            # write waveform data to channels
            task_galvo.write(data_galvo, auto_start=False)
            task_cam.write(data_cam, auto_start=False)
            task_light.write(data_light, auto_start=False)

            # start tasks: start when stack_ctr starts
            task_galvo.start()
            task_light.start()
            task_cam.start()

            if i == 0:
                # start acquisition
                acq_ctr.start()
                # Stop and clear the task
                if acq_ctr.is_task_done():
                    acq_ctr.stop()
                task.close()

            # POTENTIALLY include a wait until done here?

            # time to write do and ao data in last slice
            time.sleep(self.exposure_time + 0.1)  

            task_galvo.stop()
            task_light.stop()
            task_cam.stop()

        # close remaining trigger
        stack_ctr.close()
        # close all tasks
        task_galvo.close()
        task_light.close()
        task_cam.close()



