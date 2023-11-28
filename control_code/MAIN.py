import nidaqmx
import nidaqmx.system
import numpy as np
import time
import pco   
import warnings

# Create a workflow using the NI-DAQmx Python API to synchronize the 
# acquisition of a camera with the generation of an analog signal to control a 
# galvo mirror and digital signals to control 2 lasers and drive
# the RF frequency of an AOTF. 


class nidaq:
    # Analog input/output only    
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
    ctr1 = "Dev1/ctr1"                          # counter external camera trigger
    ctr1_internal = "ctr1InternalOutput"   # signal external camera trigger
    ctr0 = "Dev1/ctr0"                          
    ctr0_internal = "ctr0InternalOutput"  

    # programmable function I/O (PFI lines)
    PFI0 = "PFI0" #"Dev1/PFI0"     # name change was necessary
    PFI1 = "Dev1/PFI1"   

    # Digital and timing I/O (not all)
    do0 = "Dev1/port0/line0"   # 488
    do1 = "Dev1/port0/line1"   # 561
    do2 = "Dev1/port0/line2"  

    # galvo
    MAXV_GALVO = 5.0
    MINV_GALVO = 0.0
    
    # AOTFnC-400.650-TN
    MIN_RF = 74e6         # Hz
    MAX_RF = 158e6        # Hz
    MAX_RF_POWER = 0.15   # Watts

    # pco 4.2 CL
    LINE_TIME_SLOW = 27.77e-6     # sec
    LINE_TIME_FAST = 9.76e-6      # sec
    READOUT_RATE_SLOW = 95.3e6    # px/sec
    READOUT_RATE_FAST = 272.3e6   # px/sec
    MAX_FRAME_RATE_SLOW = 35      # fps
    MAX_FRAME_RATE_FAST = 100     # fps
    SYS_DELAY = 2.99e-6           # sec MEASURED 
    JITTER = 0.3e-6               # sec MEASURED
    MIN_EXP = 100e-6              # sec
    MAX_EXP = 10.0                # sec
    MAX_DELAY = 1.0               # sec
    MIN_WIDTH = 40                # px
    MAX_WIDTH = 2060              # px
    MIN_HEIGHT = 16               # px
    MAX_HEIGHT = 2048             # px

    def __init__(
            self, 
            time_points: int,               # number of stacks
            time_points_wait_time: float,   # extra time between stacks (ms)
            exposure_time: float,           # ms. User inputs *not* effective exp time to agree with apps
            mode: str,                      # camera mode: "fast" or "slow"
            multi_d: bool,                  # multidimensional acquisition
            image_height = MAX_HEIGHT,   
            image_width = MAX_WIDTH,
            cam_trigger_delay = 0.0,        # exposure delay after trigger
            z_start = 0.0,
            z_end = 0.0,
            z_step = 0.0,
            samples_per_cycle = 10,         # sampling to write ao / do data. >= 2 by nyquist thm.
            rf_freq = 1e6                   # RF frequency of AOTF
        ):
        """
        Initialize acquisition parameters and properties
        """
        assert(exposure_time >= self.MIN_EXP and exposure_time <= self.MAX_EXP)
        assert(cam_trigger_delay <= self.MAX_DELAY)
        
        self.time_points = time_points
        self.time_points_wait_time = time_points_wait_time
        self.exposure_time = exposure_time
        self.effective_exposure_time = exposure_time - self.SYS_DELAY - self.JITTER
        self.mode = mode
        self.multi_d = multi_d
        self.image_height = image_height
        self.image_width = image_width
        self.cam_trigger_delay = cam_trigger_delay
        self.z_start = z_start
        self.z_end = z_end
        self.z_step = z_step
        self._sampling_rate = samples_per_cycle / exposure_time
        self.samples_per_cycle = samples_per_cycle
        self.rf_freq = rf_freq
        
        if mode == "FAST":
            self.line_time = self.LINE_TIME_FAST
            self.readout_rate = self.READOUT_RATE_FAST
            self.max_frame_rate = self.MAX_FRAME_RATE_FAST
        elif mode == "SLOW":
            self.line_time = self.LINE_TIME_SLOW
            self.readout_rate = self.READOUT_RATE_SLOW
            self.max_frame_rate = self.MAX_FRAME_RATE_SLOW
        else:
            raise ValueError("Invalid camera mode")
        
        if self.image_height % 2 != 0:
            raise ValueError("Image height should be an even number of pixels")
        
        self.frame_readout_time = (self.image_height * self.image_width ) / self.readout_rate
        # NOTE: based on pg 14 general pco.camware manual. assumes 2 sensors in lightsheet mode
    

    @property
    def sampling_rate(self):
        return self._sampling_rate
    
    @sampling_rate.setter
    def sampling_rate(self, dummy):
        self._sampling_rate = self.samples_per_cycle / self.exposure_time
        

    @property
    def stack_slices(self):
        if self.multi_d:
            return np.floor((self.z_end - self.z_start) / self.z_step) + 1   # agrees with MM config
        else:
            return 1


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
            return cam.configuration  #sdk.get_delay_exposure_time() #desc_dict, timing_dict

    # STEPS:

    # 3. get waveform for galvo
    # 4. write test for galvo
    # 5. get waveform for AOTF
    # 6. write test for AOTF

    # NOTE: what daxi refers to as exposure time is our frame time


    def _get_trigger_stack_freq(self):
        """Get external trigger frequency in rolling shutter mode """

        # if self.exposure_time >= self.frame_readout_time:
        #     trigger_period = self.exposure_time + self.cam_trigger_delay + self.line_time
        #     # above would make sense: would make frame rate = 1 / exp time (w system delays)
        #     # TODO: do we use lightsheet mode?  dwExposureLines*dwLineTime*(1000ˆdwTimebase)
        # else:
        #     # warnings.warn("Exposure time is less than readout time, using readout time as trigger period")
        #     #trigger_period = self.frame_readout_time + self.cam_trigger_delay
        #     #trigger_period = self.exposure_time + self.cam_trigger_delay + self.line_time
        #     trigger_period = 0.011  + self.line_time

        trigger_period = self.exposure_time + self.cam_trigger_delay + self.line_time

        # NOTE: that treatment takes you up to 95 fps (below max FPS)

        return np.floor(1/trigger_period)
    

    def get_stack_time(self):
        f = self._get_trigger_stack_freq()
        samps = self.stack_slices if self.multi_d else self.time_points
        return samps / f
    

    def get_total_acq_time(self):
        return self.get_stack_time() * self.time_points + self.time_points_wait_time * (self.time_points - 1)


    def _create_ao_task(self):
        """Create the analog output task for the galvo"""
        task_ao = nidaqmx.Task("AO")
        # task_ao.ao_channels.add_ao_voltage_chan(self.ao0, min_val=self.MINV_GALVO, max_val=self.MAXV_GALVO)
        task_ao.ao_channels.add_ao_voltage_chan(self.ao1, min_val=0.0, max_val=2.0)
        return task_ao
    
        # TODO: have to consider both cases exp time > and < readout time (daxi only considers >)
        # TODO: potentially add driver of RF for AOTF

    def _create_do_task(self):
        task_do = nidaqmx.Task("DO")
        task_do.do_channels.add_do_chan(self.do0)       # 488
        task_do.do_channels.add_do_chan(self.do1)       # 561
        
        # TODO: have to consider both cases exp time > and < readout time (daxi only considers >)
        # do not alternate
        
        
        return task_do


    # TODO: figure out offset - is it necessary to control the galvo?
    def _get_ao_galvo_data(self):
        """Get the array data to write to the ao channel"""
        pass

    def _get_ao_aotf_data(self):
        """Get the array data to drive the AOTF at RF frequency"""
        total_t = max(self.frame_readout_time, self.exposure_time)
        sample_points = np.arange(0, total_t, 1 / self.sampling_rate)
        # 1.0 input modulation voltage is optimal - opto-electronic specs
        analog_output_signal = 1.0 + np.sin(2 * np.pi * self.rf_freq * sample_points)
        
        return analog_output_signal

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
    # TODO: try effect of different duty cycles
    def _external_cam_trigger(self):
        """generate TTL pulse train for parallel cam trigger"""
        task_ctr = nidaqmx.Task("cam_trigger")
        task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr1, idle_state=nidaqmx.constants.Level.LOW, 
                                                    freq=self._get_trigger_stack_freq(), duty_cycle=0.50)
        # DUTY CYCLE IS RELEVANT IF WE DO EXT EXP CONTROL
        # use the internal clock of the device
        samps = self.stack_slices if self.multi_d else self.time_points
        task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=samps)

        return task_ctr


    def _internal_exposure_trigger(self):  
        """triggers ao and do tasks during each cam exposure"""
        task_ctr = nidaqmx.Task("exposure_trigger")
        task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr0,idle_state=nidaqmx.constants.Level.LOW,freq=self.sampling_rate)
        # set buffer size of the counter per stack
        if self.exposure_time < self.frame_readout_time:
            samps = int(self.sampling_rate * self.frame_readout_time)
        else:
            samps = self.samples_per_cycle
        task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=samps)
        # counter is activated when cam1 exposure goes up
        task_ctr.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.PFI0, trigger_edge=nidaqmx.constants.Slope.RISING)
        # new rising exposures will retrigger the counter
        task_ctr.triggers.start_trigger.retriggerable = True
        return task_ctr


    def acquire(self):

        # get light source control
        # task_light = self._create_do_task()
        # data_light = self._get_do_data()

        # # get analog control
        # task_galvo = self._create_ao_task()
        # data_galvo = self._get_ao_galvo_data()
        task_aotf = self._create_ao_task()
        data_aotf = self._get_ao_aotf_data()
        
        # master camera trigger
        acq_ctr = self._external_cam_trigger()
        
        # trigger for sampling within each exposure
        exp_ctr = self._internal_exposure_trigger()

        # sync ao and do tasks with exposure trigger clock 
        src = self.ctr0_internal
        rate = self.sampling_rate
        mode = nidaqmx.constants.AcquisitionType.FINITE
        # rate is the max rate of the source
        # task_galvo.timing.cfg_sample_clk_timing(rate=rate, sample_mode=mode, source=src)
        # task_light.timing.cfg_sample_clk_timing(rate=rate, sample_mode=mode, source=src)
        task_aotf.timing.cfg_samp_clk_timing(rate=rate, sample_mode=mode, source=src)

        # activate exposure sampling trigger: wait for external camera trigger
        exp_ctr.start()
        
        # aotf ao signal frequency is very high - max AO clock is 20 MHZ - analog multiplier
        
        # could let aotf run "untimed here" and the brute force stop if we want to run continuously

        # adjust for 2D acquisition
        loops = self.time_points if self.multi_d else 1

        stack_tot = self.get_stack_time()

        for i in range(loops):
            # write waveform data to channels
            # task_galvo.write(data_galvo, auto_start=False)
            # task_light.write(data_light, auto_start=False)
            task_aotf.write(data_aotf, auto_start=False)

            # start tasks: start when exp_ctr starts
            # task_galvo.start()
            # task_light.start()
            task_aotf.start()

            # trigger camera for this stack
            acq_ctr.start()
            acq_ctr.wait_until_done(stack_tot)   # some extra time
            acq_ctr.stop()

            # min time between stacks
            time.sleep(self.time_points_wait_time)  # TODO: measure system delay introduced

            # task_galvo.stop()
            # task_light.stop()
            task_aotf.stop()
            

        # close triggers
        exp_ctr.close()
        acq_ctr.close()
        # close all tasks
        # task_galvo.close()
        # task_light.close()
        task_aotf.close()



