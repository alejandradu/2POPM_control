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
    ctr1 = "Dev1/ctr1"    # mimic external camera trigger - pulse generation (in parallel for both)
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
        self.num_slices = 10  # HERE - timing purposes (max sample buffer of clock) - ALSO: 2D imaging = 1 slice
        self.readout_time1 = 0.01 #self.READOUT_TIME_CAM1 * vertical_pixels / self.MAX_VERTICAL_PIXELS
        self.readout_time2 = 0.01 #self.READOUT_TIME_CAM2 * vertical_pixels / self.MAX_VERTICAL_PIXELS

    @property
    def sampling_rate(self):
        return self.num_stacks / self.exposure_time

    # TODO: clarify difference num_samples and nb_slices

    def _create_ao_task(self):
        """Create the analog output task for the galvo"""
        task_ao = nidaqmx.Task("AO")
        task_ao.ao_channels.add_ao_voltage_chan(self.ao0, min_val=self.MINV_GALVO, max_val=self.MAXV_GALVO)
        return task_ao
    
        # TODO: potentially add driver of RF for AOTF

    def _create_do_task(self):
        task_do = nidaqmx.Task("DO")
        task_do.do_channels.add_do_chan(self.do0)       # 488
        task_do.do_channels.add_do_chan(self.do1)       # 561
        # task_do.do_channels.add_do_chan(self.do2)       # LED (AOTF)
        return task_do

    # TODO: get numbers of laser channels, determine line grouping
    # TODO: figure out the purpose of views

    def _get_ao_data(self):
        """Get the array data to write to the ao channel"""
        pass

        # TODO: determine if we can include here the function of the amplifier - VARIABLE PARAM
        # TODO: figure out offset - is it necessary to control the galvo?

    def _get_do_data(self, laser_channels: list, alternate: bool = False):
        """Get the ndarray for the digital ouput of the light sources"""
        if alternate:
            pass
        # HERE: ASSUMING SAME READOUT TIME, both light sources on at the same time
        num_on_sample = round((self.exposure_time - self.readout_time1) * self.sampling_rate)
        data = [True] * num_on_sample + [False] * (self.num_slices - num_on_sample)
    
        if len(laser_channels) == 1:  
            return data
        elif len(laser_channels) == 2:
            if alternate:
                data_off = round(len(data)/2) * [False]
                data_on = (len(data) - len(data_off)) * [True]
                return [data_off + data_on, data_on + data_off]
            else:
                return [data, data]
        elif len(laser_channels) == 3:
            pass  # figure out the AOTF
        else:
            raise ValueError("Invalid number of laser channels")


    # def _external_cam_trigger(self, n_cams: int):
    #     """sends ONE TTL pulse to the cameras to start acquisition"""
    #     task_do = nidaqmx.Task("cam_trigger")
    #     task_do.do_channels.add_do_chan(self.do3)       # start cam1
    #     if n_cams == 2:  task_do.do_channels.add_do_chan(self.do4)   # start cam2
    #     # use the internal clock of the device
    #     task_do.timing.cfg_samp_clk_timing(rate=1, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS, samps_per_chan=20)

    #     data = [True, True] if n_cams == 2 else [True, True]*10
    #     # TODO: figure out what data points are specifically read

    #     # write TTL pulse - explicitly start later
    #     task_do.write(data, auto_start=False)
        
    #     return task_do

    def _external_cam_trigger(self, n_cams: int):
        """sends ONE TTL (parallel) pulse to the cameras to start acquisition"""
        task_ctr = nidaqmx.Task("cam_trigger")
        task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr1, idle_state=nidaqmx.constants.Level.LOW, freq=200.0, duty_cycle=0.5)
        # use the internal clock of the device
        task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=200)

        return task_ctr


    def _internal_stack_trigger(self):
        """triggers ao and do tasks for each volume stack"""
        task_ctr = nidaqmx.Task("stack_trigger")
        task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr0,idle_state=nidaqmx.constants.Level.LOW,freq=self.sampling_rate)
        # set buffer size of the counter per stack
        task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE,samps_per_chan=self.num_slices)
        # counter is activated when cam1 exposure goes up (once for each stack)
        task_ctr.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.PFI0, trigger_edge=nidaqmx.constants.Slope.RISING)
        # new rising exposures will retrigger the counter
        task_ctr.triggers.start_trigger.retriggerable = True

        return task_ctr


    def acquire(self):

        # get light source control
        task_light = self._create_do_task()
        data_light = self._get_do_data()

        # get galvo control
        task_galvo = self._create_ao_task()
        data_galvo = self._get_ao_data()
        
        # mimic external camera trigger (ONE start trigger)
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

        # activate start trigger: wait for external camera trigger
        stack_ctr.start()

        for i in range(self.num_stacks):
            # write waveform data to channels
            task_galvo.write(data_galvo, auto_start=False)
            task_light.write(data_light, auto_start=False)

            # start tasks: start when stack_ctr starts
            task_galvo.start()
            task_light.start()

            if i == 0:
                # start acquisition
                acq_ctr.start()
                # Stop and clear the task
                if acq_ctr.is_task_done():
                    acq_ctr.stop()
                acq_ctr.close()

            # POTENTIALLY include a wait until done here?

            # time to write do and ao data in last slice
            time.sleep(self.exposure_time + 0.1)  

            task_galvo.stop()
            task_light.stop()

        # close remaining trigger
        stack_ctr.close()
        # close all tasks
        task_galvo.close()
        task_light.close()



