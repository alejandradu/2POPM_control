import nidaqmx
import nidaqmx.system
import numpy as np
import time
import pco   # to get params

# Create a workflow using the NI-DAQmx Python API to synchronize the 
# acquisition of a camera with the generation of an analog signal to control a 
# galvo mirror and digital signals to control 3 lasers. 


class nidaq:
    # Channel ports    
    ao0 = "Dev1/ao0"   # OPM galvo
    ao1 = "Dev1/ao1"   # AOTF
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
    do2 = "Dev1/port0/line2"  
    do3 = "Dev1/port0/line3"   
    do4 = "Dev1/port0/line4"   

    # constants
    MAXV_GALVO = 5.0
    MINV_GALVO = 0.0

    # pco 4.2 CL
    LINE_TIME_SLOW = 27.77e-6     # seconds
    LINE_TIME_FAST = 9.76e-6      # seconds
    READOUT_RATE_SLOW = 95.3e6    # pixels/second
    READOUT_RATE_FAST = 272.3e6   # pixels/second
    MAX_FRAME_RATE_SLOW = 35      # fps
    MAX_FRAME_RATE_FAST = 100     # fps
    SYS_DELAY = 4294967295e-9     # seconds
    JITTER = 4294967295e-9        # seconds
    MIN_EXP = 100e-6              # seconds
    MAX_EXP = 10                  # seconds

    def __init__(
            self, 
            time_points: int,
            time_points_interval: float,
            exposure_time: float,
            mode: str,                    # camera mode: "fast" or "slow"
            multi_d: bool,                # 2D or 3D imaging
            vertical_pixels: int,         # TODO: do we count vertically?
            cam_trigger_delay = 0.0,      # extra delay to exposure after trigger
            z_start = 0.0,
            z_end = 0.0,
            z_step = 0.0
        ):
        """
        Initialize the NI-DAQmx system and create a task for each channel.
        """
        self.time_points = time_points
        self.time_points_interval = time_points_interval
        self.exposure_time = exposure_time
        self.cam_trigger_delay = cam_trigger_delay
        self.mode = mode
        self.num_slices = 10  # HERE - timing purposes (max sample buffer of clock) - ALSO: 2D imaging = 1 slice
        self.readout_time1 = 0.01 #self.READOUT_TIME_CAM1 * vertical_pixels / self.MAX_VERTICAL_PIXELS
        self.readout_time2 = 0.01 #self.READOUT_TIME_CAM2 * vertical_pixels / self.MAX_VERTICAL_PIXELS

    @property
    def num_stacks(self):
        pass
    
    @property
    def sampling_rate(self):
        return self.num_stacks / self.exposure_time

    @property
    def stack_slices(self):
        return np.floor(self.z_end - self.z_start / self.z_step) + 1   # agrees with MM config

    @property
    def exposure_with_delay(self):
        return self.RISE_SYS_DELAY + self.JITTER   # should be < 10 us (pco 4.2 CL)

    @rising_delay.setter
    def rising_delay(self, extra_delay):
        self.rising_delay += extra_delay

    @property
    def falling_delay(self):
        return self.FALL_SYS_DELAY + self.JITTER   # should be < 10 us (pco 4.2 CL)

    @falling_delay.setter
    def falling_delay(self, extra_delay):
        self.falling_delay += extra_delay


    # TODO: clarify difference num_samples and nb_slices

    def get_cam_params(self, desc_property_key=None, timing_property_key=None):
        """Get parameters of PCO camera - close MM to call this function"""
        # MM can't be open to call this function
        cam = pco.Camera()
        desc_dict = cam.description
        timing_dict = cam.sdk.get_image_timing()
        if desc_property_key:
            return desc_dict[desc_property_key]
        elif timing_property_key:
            return timing_dict[timing_property_key]
        else:
            return desc_dict, timing_dict


    def _wave_calc(self, time_points, interval, z_start, z_end, step_size):
        """Get waveform parameters for one stack"""

        time_diff_triggers = self.rising_delay + self.falling_delay + self.exposure_time

        if self.mode == "fast":
            assert(freq <= self.MAX_FRAME_RATE_FAST / 1.001)
        elif self.mode == "slow":
            assert(freq <= self.MAX_FRAME_RATE_SLOW / 1.001)

        return 1/time_diff_triggers


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
        return task_do


    # TODO: figure out offset - is it necessary to control the galvo?
    def _get_ao_galvo_data(self):
        """Get the array data to write to the ao channel"""
        pass

    def _get_ao_aotf_data(self):
        """Get the array data to write to the ao channel"""
        pass

    # TODO: determine if we can include here the function of the amplifier - VARIABLE PARAM
    # NOTE: currently there is a hardware trigger, keep it that way?
    # NOTE: alternating might not make sense for fast imaging
    # def _get_do_data(self, laser_channels: list, alternate: bool = False):
    #     """Get the ndarray for the digital ouput of the light sources"""
    #     num_on_sample = round((self.exposure_time - self.readout_time1) * self.sampling_rate)
    #     data = [True] * num_on_sample + [False] * (self.num_slices - num_on_sample)
    
    #     if len(laser_channels) == 1:  
    #         return data
    #     elif len(laser_channels) == 2:
    #         if alternate:
    #             data_off = round(len(data)/2) * [False]
    #             data_on = (len(data) - len(data_off)) * [True]
    #             return [data_off + data_on, data_on + data_off]
    #         else:
    #             return [data, data]
    #     elif len(laser_channels) == 3:
    #         pass  # figure out the AOTF
    #     else:
    #         raise ValueError("Invalid number of laser channels")


    # NOTE: discussions have been around the lack of core timing - this would provide that 
    # TODO: params of freq need to agree w those of MM
    def _external_cam_trigger(self, n_cams: int, freq):
        """send parallel TTL pulses to the cameras"""

        task_ctr = nidaqmx.Task("cam_trigger")
        # TODO: try effect of different duty cycles

        task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr1, idle_state=nidaqmx.constants.Level.LOW, freq=freq, duty_cycle=0.2)
        # use the internal clock of the device
        task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=200)

        # TODO: makes this retriggerable with wait time of self.stack_interval

        return task_ctr



    # def _internal_stack_trigger(self):  
    #     """triggers ao and do tasks for each volume stack"""
    #     task_ctr = nidaqmx.Task("stack_trigger")
    #     task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr0,idle_state=nidaqmx.constants.Level.LOW,freq=self.sampling_rate)
    #     # set buffer size of the counter per stack
    #     task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE,samps_per_chan=self.num_slices)
    #     # counter is activated when cam1 exposure goes up (once for each stack)
    #     task_ctr.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.PFI0, trigger_edge=nidaqmx.constants.Slope.RISING)
    #     # new rising exposures will retrigger the counter
    #     task_ctr.triggers.start_trigger.retriggerable = True
    #     return task_ctr

    # letting MM do the subsequent triggering would allow the failure to happen again - change the timer to a single timer - consider delay

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
        # stack_ctr = self._internal_stack_trigger()

        # sync ao and do tasks with stack counter clock
        src = self.ctr1_internal
        rate = self.sampling_rate
        mode = nidaqmx.constants.AcquisitionType.FINITE
        # rate is the max rate of the source
        task_galvo.timing.cfg_sample_clk_timing(rate=rate, sample_mode=mode, source=src)
        task_light.timing.cfg_sample_clk_timing(rate=rate, sample_mode=mode, source=src)

        # activate start trigger: wait for external camera trigger
        #stack_ctr.start()

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
        #stack_ctr.close()
        # close all tasks
        task_galvo.close()
        task_light.close()



