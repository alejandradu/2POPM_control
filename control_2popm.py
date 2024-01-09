import nidaqmx
import nidaqmx.system
import numpy as np
import tkinter as tk
from tkinter import messagebox
import pco   
import matplotlib.pyplot as plt
import scipy
import math

# Create a workflow using the NI-DAQmx Python API to synchronize the 
# acquisition of a camera with the generation of an analog signal to control a 
# galvo mirror and digital signals to control 2 lasers and drive
# the RF frequency of an AOTF. 

class nidaq:
    # Analog input/output only    
    ao0 = "Dev1/ao0"   # OPM galvo
    ao1 = "Dev1/ao1"   # AOTF / LED voltage modulator

    # trigger/counter
    ctr1 = "Dev1/ctr1"                     # camera exposure pulses
    ctr1_internal = "ctr1InternalOutput"   # idle
    ctr0 = "Dev1/ctr0"                     # stack trigger
    ctr0_internal = "ctr0InternalOutput"   # internal signal for stack trigger

    # programmable function I/O (PFI lines)
    PFI0 = "PFI0"
    PFI1 = "Dev1/PFI1"   

    # Digital and timing I/O (not all)
    do0 = "Dev1/port0/line0"   # LED
    do1 = "Dev1/port0/line1"   # 488
    do2 = "Dev1/port0/line2"   # 561

    # galvo GVS011
    MAXV_GALVO = 5.0  
    MINV_GALVO = -5.0
    
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
            multi_d: bool,                  # multidimensional acquisition
            z_start = 0.0,                  # microm. start of z stack. min -178.36 
            z_end = 0.0,                    # microm. end of z stack. max 178.36 
            z_step = 0.0,                   # microm. Step size of galvo scanning
            image_height = MAX_HEIGHT,      # px. vertical ROI. Defines frame readout time
            image_width = MAX_WIDTH,        # px. horizontal ROI
            frame_delay_time = 0.0,         # s. optional delay after each frame trigger
            rf_freq = 1e6,                  # RF frequency of AOTF
            led_stack_fraction_on = 1.0,    # percent of time LED is on during every stack acquisition in software_fraction mode
            led_trigger = None,             # "hardware", "software_fraction", "software_time" triggering of LED if light control is desired
            led_time_on = 0.0,              # s. time LED is on during acquisition in software_time mode (i.e. LED period)
            led_frequency = 0):             # pulses/second. Nonzero to pulse the LED for led_time_on at given frequency
        
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
        if (z_end > 178.36 or z_start < -178.36):
            raise ValueError("z_end and/or z_start are out of range [-178.36, 178.36]")
        
        if readout_mode == "fast":
            self.line_time = self.LINE_TIME_FAST
            self.readout_rate = self.READOUT_RATE_FAST
            self.max_full_frame_rate = self.MAX_FRAME_RATE_FAST
        elif readout_mode == "slow":
            self.line_time = self.LINE_TIME_SLOW
            self.readout_rate = self.READOUT_RATE_SLOW
            self.max_full_frame_rate = self.MAX_FRAME_RATE_SLOW
        else:
            raise ValueError("Invalid camera readout mode")
        
        if led_trigger == "hardware":
            print("LED hardware trigger selected. Verify BNC cable connects Cam Exp Out to LED In")
        elif led_trigger == "software_fraction" or led_trigger == "software_time":
            print("LED software trigger selected. Verify BNC cable connects USER1 OUT to LED In")
        elif led_trigger is None:
            print("No LED light control selected.")
        else:
            raise ValueError("Invalid LED trigger mode")
        
        # assign user inputs
        self.num_stacks = num_stacks
        self.stack_delay_time = stack_delay_time
        self.exposure_time = exposure_time
        self.readout_mode = readout_mode
        self.multi_d = multi_d
        self.image_height = image_height
        self.image_width = image_width
        self.frame_delay_time = frame_delay_time
        self.z_start = z_start
        self.z_end = z_end
        self.z_step = z_step
        self.rf_freq = rf_freq
        self.led_fraction_on = led_stack_fraction_on
        self.led_trigger = led_trigger
        self.led_time_on = led_time_on
        self.led_frequency = led_frequency
        
        # conversion from z to galvo voltage according to experimental calibration
        self.volt_per_z = 5 / (178.36)
        
        if self.multi_d:
            print("Stage (galvo) control enabled. Verify MicroManager NIDAQHub control is disabled.")
                    

    @property
    def frames_per_stack(self):
        """Get number of frames per stack) start and end inclusive"""
        n = math.floor((self.z_end - self.z_start) / self.z_step) + 1 
        return n if self.multi_d else 1
    
    
# ------------------------------- TIMING --------------------------------- #

    def _get_frame_time(self):
        """Get frame readout time: min time between camera triggers"""
        return self.image_height * self.line_time / 2
        
        
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
    def duty_cycle(self):
        """Get duty cycle of exposure trigger"""
        return 0.98 - self.frame_delay_time * self._get_trigger_exp_freq()
        
        
    @property
    def max_frame_rate(self):
        """Get max frame rate at given ROI without user input delays"""
        return 1 / self._get_frame_time()
        
        
    def get_stack_time(self):
        """Get time to acquire a stack if 3D, or a frame if 2D, including delay between stacks"""
        f = self._get_trigger_exp_freq()
        return self.frames_per_stack / f + self.stack_delay_time
    
    
    @property
    def stack_sampling_rate(self): 
        """Get sampling rate of output to write for each stack without delay time"""
        if self.multi_d:
            return self._get_trigger_exp_freq()
        else: # at least 2x cam trigger freq
            return 10 / self.exposure_time
    
    
    @property
    def stack_sampling_rate_delay(self):
        """Get sampling rate of output to write for each stack with delay time"""
        # only use case now is LED software time mode - 10 samples while active
        return 10 / self.led_time_on
    

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
        
    
# --------------------------- I/0 SETTINGS  ----------------------------- #


    def _create_ao_task(self):
        """Create the analog output task for the galvo"""
        task_ao = nidaqmx.Task("AO")
        task_ao.ao_channels.add_ao_voltage_chan(self.ao0, min_val=self.MINV_GALVO, max_val=self.MAXV_GALVO)       
        return task_ao


    def _get_ao_galvo_data(self):
        """Get the array data to write to the ao channel"""
        # continuous sawtooth requires more samples than frames_per_stack  - could refine more how this is related to z step
        return np.linspace(self.volt_per_z*self.z_start, self.volt_per_z*self.z_end, self.frames_per_stack)


    def _get_ao_aotf_data(self):
        """Get the array data to drive the AOTF at RF frequency"""
        rate = 100
        total_t = max(self._get_frame_time(), self.exposure_time)
        sample_points = np.arange(0, total_t, 1 / rate)
        # 1.0 input modulation voltage is optimal - opto-electronic specs
        analog_output_signal = 1.0 + np.sin(2 * np.pi * self.rf_freq * sample_points)
        
        return analog_output_signal
    
    
    def _create_led_do_task(self):
        task_do = nidaqmx.Task("LED")
        task_do.do_channels.add_do_chan(self.do0)       # LED
        return task_do
    
    
    def _get_do_led_data_trigger(self):
        """Get the array data to write to the do channel for LED fraction trigger mode"""
        n = self.frames_per_stack if self.multi_d else 10
        data = [True] * int(n * self.led_fraction_on) + [False] * int(n * (1 - self.led_fraction_on))   
        data[-3:] = [False]*3     # guarantee LED ends off
        return data
    
    
    def _get_do_led_data_no_trigger(self):
        """Get the array data to write to the do channel for LED time trigger mode"""
        tot_samples = self.stack_sampling_rate_delay * self.get_total_acq_time()
        time_off = 1/self.led_frequency - self.led_time_on
        led_samples_on = int(self.led_time_on * self.stack_sampling_rate_delay)
        led_samples_off = int(time_off * self.stack_sampling_rate_delay)
        n = math.ceil(tot_samples / (led_samples_off + led_samples_on))
        data = n * ([True] * led_samples_on + [False] * led_samples_off)
        data = data[:tot_samples]
        data[-3:] = [False]*3   # guarantee LED ends off
        return data
        
# ------------------------------ TRIGGERS  ------------------------------- #

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
        # duty cycle < 1.0 means the real exposure time is slightly less than input with rising delay
        task_ctr.co_channels.add_co_pulse_chan_freq(self.ctr1, idle_state=nidaqmx.constants.Level.LOW, freq=self._get_trigger_exp_freq(), duty_cycle=self.duty_cycle)
        # use the internal clock of the device
        if self.multi_d:
            if self.stack_delay_time == 0:
                task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS, samps_per_chan=self.frames_per_stack)
            else:
                # finite mode is able to finish with a delay between stacks
                task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=self.frames_per_stack)
        else:
            task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=1)
        # trigger is activated when ctr0 goes up
        task_ctr.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.ctr0_internal, trigger_edge=nidaqmx.constants.Slope.RISING)
        task_ctr.triggers.start_trigger.retriggerable = True

        return task_ctr
    
    
    def setup_triggered_task(self, task, data_task):
        """Setup task to be re-triggerable by ctr0"""
        # rate and number of samples stop it before delay (idle time)
        samps = self.frames_per_stack if self.multi_d else 10
        task.timing.cfg_samp_clk_timing(rate=self.stack_sampling_rate, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, 
                                            samps_per_chan= samps)
        # set start trigger
        task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.ctr0_internal, trigger_edge=nidaqmx.constants.Edge.RISING)
        # retriggerable between stacks
        task.triggers.start_trigger.retriggerable = True
        # start and wait for stack trigger
        task.write(data_task, auto_start=False)
        task.start()
        
    def setup_not_triggered_task(self, task, data_task):
        """Setup task to take a single trigger by ctr0. Sampling rate does include stack delay"""
        # rate and number of samples stop it before delay (idle time)
        task.timing.cfg_samp_clk_timing(rate=self.stack_sampling_rate_delay, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, 
                                            samps_per_chan= self.stack_sampling_rate_delay*self.get_total_acq_time())
        # set start trigger
        task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.ctr0_internal, trigger_edge=nidaqmx.constants.Edge.RISING)
        # retriggerable between stacks
        task.triggers.start_trigger.retriggerable = False
        # start and wait for stack trigger
        task.write(data_task, auto_start=False)
        task.start()
        
        
# ------------------------------ GRAPHING -------------------------------- #

    def plot_preview(self, n_cycles=1):
        
        t = np.linspace(0.0, n_cycles * self.get_stack_time(), n_cycles * 500, endpoint=False)
        one_t = np.linspace(0.0, self.frames_per_stack / self._get_trigger_exp_freq(), 500, endpoint=False)
        stack_pulse = 2.5 * (1 + scipy.signal.square(2 * np.pi * t / self.get_stack_time(), 0.2))
        exp_pulse_on = 3.3/2 * (1 + scipy.signal.square(2 * np.pi * one_t * self._get_trigger_exp_freq(), self.duty_cycle))
        
        plt.figure(figsize=(10, 5))  # Set the figure size to create a big rectangle
        
        # Plot the pulse train
        plt.plot(t, stack_pulse)
        #plt.plot(t, exp_pulse)
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
        plt.ylim(-1, 6)
        if self.multi_d:
            plt.title("3D acquisition")
        else:
            plt.title("2D acquisition")
        plt.show()
        
        
    def print_parameters(self):
        root = tk.Tk()
        root.withdraw()
        message = f"Total number of time points (input in Micro-Manager): \n{self.num_stacks*self.frames_per_stack}\n\nTotal acquisition time (s): \n{round(self.get_total_acq_time(),4)}"
        if self.multi_d:
            message = message + f"\nVoumes per second: \n{round(1/self.get_stack_time(),3)}\nFrames per z-stack: \n{self.frames_per_stack}"
        else:
            message = message + f"\nFrames per second: \n{round(self._get_trigger_exp_freq(),3)}"
        message = message + "\n\nStart acquisition?"
        result = messagebox.askokcancel(title="Timing parameters", message=message)
        return result
        

# -------------------------------- MAIN ---------------------------------- #

    def acquire(self):
        
        if self.led_time_on > self.get_total_acq_time():
            raise ValueError("LED time on is greater than total acquisition time")
        
        ready = self.print_parameters()
        
        if ready: 

            # master trigger
            stack_ctr = self._stack_trigger()

            # galvo control
            if self.multi_d:
                task_galvo = self._create_ao_task()
                data_galvo = self._get_ao_galvo_data()
                self.setup_triggered_task(task_galvo, data_galvo)

            # LED control
            if self.led_trigger == "software_fraction":
                # same timing setup as galvo
                task_led = self._create_led_do_task()
                data_led = self._get_do_led_data_trigger()
                # sample at rate without delay
                self.setup_triggered_task(task_led, data_led)
            elif self.led_trigger == "software_time":
                task_led = self._create_led_do_task()
                data_led = self._get_do_led_data_no_trigger()
                # sample at rate with (if any) stack delay
                self.setup_not_triggered_task(task_led, data_led)

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
            if self.led_trigger == "software_time" or self.led_trigger == "software_fraction":
                task_led.stop()

            # close tasks
            stack_ctr.close()
            exp_ctr.close()
            if self.multi_d:
                task_galvo.close()
            if self.led_trigger == "software_time" or self.led_trigger == "software_fraction":
                task_led.close()

