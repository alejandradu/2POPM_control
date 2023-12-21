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

# TODO: the aotf module and the synchronization should be 2 different modules

class nidaq:
    # Analog input/output only    
    ao0 = "Dev1/ao0"   # OPM galvo
    ao1 = "Dev1/ao1"   # AOTF / LED voltage modulator

    # trigger/counter
    ctr1 = "Dev1/ctr1"                     # counter external camera trigger
    ctr1_internal = "ctr1InternalOutput"   # signal external camera trigger
    ctr0 = "Dev1/ctr0"                     # other trigger to sync the galvo
    ctr0_internal = "ctr0InternalOutput"  

    # programmable function I/O (PFI lines)
    PFI0 = "PFI0"
    PFI1 = "Dev1/PFI1"   

    # Digital and timing I/O (not all)
    do0 = "Dev1/port0/line0"   # 488
    do1 = "Dev1/port0/line1"   # 561
    do2 = "Dev1/port0/line2"  

    # galvo GVS011
    MAXV_GALVO = 5.0   # or 10. ask
    MINV_GALVO = 0.0
    SCALING_FACTOR = 0.5   # 0.5 V/deg check (max 10V, 20 deg) 20 deg = 175 microm, 0 deg = 0 microm
    
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
            num_stacks: int,                # number of 3D stacks if multi d, number of frames if not
            stack_delay_time: float,        # s. time between acquiring any 2 stacks
            exposure_time: float,           # s. effective exposure will be less due to system delay
            readout_mode: str,              # camera readout mode "fast" or "slow"
            lightsheet: bool,               # lightsheet mode
            multi_d: bool,                  # multidimensional acquisition
            z_start = 0.0,                  # microm. start of z stack
            z_end = 0.0,                            # ASSUMING 175 nm = 20 deg
            num_z_slices = 0,                       # TODO: is it more useful to have a step or a number of slices?
            image_height = MAX_HEIGHT,      # px. vertical ROI. Defines frame readout time
            image_width = MAX_WIDTH,        # px. horizontal ROI
            frame_delay_time = 0.0,         # s. optional delay after each frame trigger
            samples_per_exp = 10,           # sampling to write data for each cam exposure >= 2 by nyquist thm.
            samples_per_stack = 10,         # sampling to write data for each stack
            rf_freq = 1e6,                   # RF frequency of AOTF
            duty_cycle = 0.98):              # duty cycle of exposure trigger 
        
        if (exposure_time < self.MIN_EXP or exposure_time > self.MAX_EXP):
            raise ValueError("Exposure time is not between 100e-6 and 10.0 sec")
        if (frame_delay_time > self.MAX_DELAY):
            raise ValueError("Delay between frame triggers is greater than 1.0 sec")
        if (image_height > self.MAX_HEIGHT or image_height < self.MIN_HEIGHT):
            raise ValueError("Image height is not between 16 and 2048 pixels")
        if (image_height % 2 != 0):
            raise ValueError("Image height should be an even number of pixels")
        if (image_width > self.MAX_WIDTH or image_width < self.MIN_WIDTH):
            raise ValueError("Image width is not between 40 and 2060 pixels")
        if (z_end < z_start):
            raise ValueError("z_end is smaller than z_start")
        if (z_end > 175.0):
            raise ValueError("z_end is greater than 175 microm")
        
        if readout_mode == "FAST":
            self.line_time = self.LINE_TIME_FAST
            self.readout_rate = self.READOUT_RATE_FAST
            self.max_full_frame_rate = self.MAX_FRAME_RATE_FAST
        elif readout_mode == "SLOW":
            self.line_time = self.LINE_TIME_SLOW
            self.readout_rate = self.READOUT_RATE_SLOW
            self.max_full_frame_rate = self.MAX_FRAME_RATE_SLOW
        else:
            raise ValueError("Invalid camera readout mode")
        
        # assign user inputs
        self.num_stacks = num_stacks
        self.stack_delay_time = stack_delay_time
        self.exposure_time = exposure_time
        self.readout_mode = readout_mode
        self.lightsheet = lightsheet
        self.multi_d = multi_d
        self.image_height = image_height
        self.image_width = image_width
        self.frame_delay_time = frame_delay_time
        self.z_start = z_start
        self.z_end = z_end
        self.num_z_slices = num_z_slices
        self.samples_per_exp = samples_per_exp
        self.samples_per_stack = samples_per_stack
        self.rf_freq = rf_freq
        self.duty_cycle = duty_cycle
        
        # conversion from z to galvo voltage
        # TODO: check is 175 microm +20v range? or 10?
        self.volt_per_z = 10 / 175 * self.SCALING_FACTOR


    @property
    def frames_per_stack(self):
        """Get number of frames per stack (agrees with MM)"""
        return self.num_z_slices if self.multi_d else 1
    
    
# ------------------------------- TIMING --------------------------------- #

    def _get_frame_time(self):
        """Get frame readout time: min time between camera triggers"""
        if not self.lightsheet:
            return self.image_height * self.line_time / 2
        else:
            return self.image_height * self.line_time
        
        
    def _get_trigger_exp_freq(self):
        """Get external trigger frequency in rolling shutter mode """
        # no delay between frames if 2D (delay is between stacks)
        delay = self.frame_delay_time if self.multi_d else 0
        if self.exposure_time < self._get_frame_time():
            # max frame rate. Can give many fps if vertical ROI is low
            return 1 / (self._get_frame_time() + delay)  
        else:
            return 1 / (self.exposure_time + delay)
        
        
    @property
    def exp_sampling_rate(self):
        """Get sampling rate of output to write for each frame"""
        return self.samples_per_exp / self._get_frame_time()
    
    
    @property
    def stack_sampling_rate(self):
        """Get sampling rate of output to write for each stack"""
        return self.samples_per_stack / self.get_stack_time()
        
        
    @property
    def max_frame_rate(self):
        """Get max frame rate at given ROI without user input delays"""
        return 1 / self._get_frame_time()
        
        
    def get_stack_time(self):
        """Get time to acquire a stack if 3D, or a frame if 2D"""
        f = self._get_trigger_exp_freq()
        samps = self.frames_per_stack if self.multi_d else 1
        return samps / f
    

    def get_total_acq_time(self):
        """Get total time to acquire all stacks if 3D, or all frames if 2D"""
        return self.get_stack_time() * self.num_stacks + self.stack_delay_time * (self.num_stacks - 1)
        
        
# ---------------------------- CAM PROPERTIES ----------------------------- #

    def get_cam_params(self, desc_property_key=None, timing_property_key=None):
        """Get parameters of PCO camera - close MM to call this function"""
        cam = pco.Camera()
        desc_dict = cam.description
        timing_dict = cam.sdk.get_image_timing()
        if desc_property_key:
            return desc_dict[desc_property_key]
        elif timing_property_key:
            return timing_dict[timing_property_key]
        else:
            return cam.configuration
        
        
    def setup_lightsheet(self):
        """optional setup for rolling shutter mode"""
        pass 
    
# --------------------------- I/0 SETTINGS  ----------------------------- #


    def _create_ao_task(self):
        """Create the analog output task for the galvo"""
        task_ao = nidaqmx.Task("AO")
        task_ao.ao_channels.add_ao_voltage_chan(self.ao0, min_val=self.MINV_GALVO, max_val=self.MAXV_GALVO)       
        return task_ao
    

    def _create_do_task(self):
        task_do = nidaqmx.Task("DO")
        task_do.do_channels.add_do_chan(self.do0)       # 488
        task_do.do_channels.add_do_chan(self.do1)       # 561     
        
        return task_do


    def _get_ao_galvo_data(self):
        """Get the array data to write to the ao channel"""
        # we have a number of z steps and we start the scanning with the first line, but how do we know that it's hitting the sensor?
        # continuous sawtooth requires more samples than frames_per_stack  - could refine more how this is related to z step
        return np.linspace(self.volt_per_z*self.z_start, self.volt_per_z*self.z_end, self.samples_per_stack)


    def _get_ao_aotf_data(self):
        """Get the array data to drive the AOTF at RF frequency"""
        total_t = max(self._get_frame_time(), self.exposure_time)
        sample_points = np.arange(0, total_t, 1 / self.exp_sampling_rate)
        # 1.0 input modulation voltage is optimal - opto-electronic specs
        analog_output_signal = 1.0 + np.sin(2 * np.pi * self.rf_freq * sample_points)
        
        return analog_output_signal

    # TODO: determine if we can include here the function of the amplifier - VARIABLE PARAM
    # NOTE: currently there is a hardware trigger, keep it that way?
        
# ------------------------------ TRIGGERS  ------------------------------- #

    # could technically use the cam_exposure_trigger, but this could only give step-like sweeping
    # NOTE: discussions have been around the lack of core timing - this would provide that 
    def _stack_trigger(self):
        """generate rising edge trigger for each stack or frame"""    
        task_ctr = nidaqmx.Task("stack_trigger")
        task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr0, idle_state=nidaqmx.constants.Level.LOW, 
                                                    freq=1/self.get_stack_time(), duty_cycle=0.2)
        task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=self.num_stacks)
        
        return task_ctr
        
        
    def _cam_exposure_trigger(self):
        """generate TTL pulse train for parallel cam trigger"""
        task_ctr = nidaqmx.Task("cam_trigger")
        # duty cycle < 1.0 means the real exposure time is even less than input with rising delay
        task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr1, idle_state=nidaqmx.constants.Level.LOW, freq=self._get_trigger_exp_freq(), duty_cycle=self.duty_cycle)
        # use the internal clock of the device
        if self.multi_d:
            task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS, samps_per_chan=self.frames_per_stack)
        else:
            task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=1)
        # trigger is activated when ctr0 goes up
        task_ctr.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.ctr0_internal, trigger_edge=nidaqmx.constants.Slope.RISING)
        task_ctr.triggers.start_trigger.retriggerable = True

        return task_ctr

# -------------------------------- MAIN ---------------------------------- #

    def acquire(self):
        # get light source control
        # task_light = self._create_do_task()
        # data_light = self._get_do_data()
        
        # TODO: incorporate stack_delay_time in this logic (prob delay to stack_trigger)
        # TODO: determine if we want to more precisely control exposure via duty cycle (seems the best, otherwise we
        #      have to introduce a delay between frames - actually this is close to what i have)

        # master trigger
        stack_ctr = self._stack_trigger()

        # galvo control
        if self.multi_d:
            task_galvo = self._create_ao_task()
            data_galvo = self._get_ao_galvo_data()
            # cannot put src_galvo as src bc then it would sample at the rate of galvo triggers
            task_galvo.timing.cfg_samp_clk_timing(rate=self.stack_sampling_rate, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, 
                                                samps_per_chan= self.samples_per_stack)
            # set start trigger
            task_galvo.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.ctr0_internal, trigger_edge=nidaqmx.constants.Edge.RISING)
            # retriggerable between stacks
            task_galvo.triggers.start_trigger.retriggerable = True
            # start and wait for stack trigger
            task_galvo.write(data_galvo, auto_start=False)
            task_galvo.start()
        
        # task_aotf = self._create_ao_task()
        # data_aotf = self._get_ao_aotf_data()
        
        # camera pulse train
        exp_ctr = self._cam_exposure_trigger()
        # start and wait for stack trigger
        exp_ctr.start()
        
        # start stack or frame acquisition.
        stack_ctr.start()
        stack_ctr.wait_until_done(self.get_total_acq_time())
        stack_ctr.stop()
        
        # stop tasks
        exp_ctr.stop()
        if self.multi_d:
            task_galvo.stop()
            
        # close tasks
        stack_ctr.close()
        exp_ctr.close()
        if self.multi_d:
            task_galvo.close()

