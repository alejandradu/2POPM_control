import nidaqmx
import nidaqmx.system
import numpy as np
import time

# Create a workflow using the NI-DAQmx Python API to synchronize the 
# acquisition of a camera with the generation of an analog signal to control a 
# galvo mirror and digital signals to control 3 lasers. 

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
    ctr0 = "Dev1/ctr0"
    ctr0_internal = "Dev1/ctr0InternalOutput"
    ctr1 = "Dev1/ctr1"
    ctr1_internal = "Dev1/ctr1InternalOutput"

    # programmable function I/O (PFI lines)
    PFI0 = "Dev1/PFI0"     # master cam exposure input
    PFI1 = "Dev1/PFI1"     # secondary cam exposure input

    # Digital and timing I/O (not all)
    di0 = "Dev1/port0/line0"   # 488
    di1 = "Dev1/port0/line1"   # 561
    di2 = "Dev1/port0/line2"   # LED

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
        self.readout_time1 = self.READOUT_TIME_CAM1 * vertical_pixels / self.MAX_VERTICAL_PIXELS
        self.readout_time2 = self.READOUT_TIME_CAM2 * vertical_pixels / self.MAX_VERTICAL_PIXELS

    @property
    def sampling_rate(self):
        return self.num_stacks / self.exposure_time

        # TODO: add all instance attributes, including properties
        # TODO: make this specific to volumetric sampling or not
        pass

    def _create_ao_task(self, minV, maxV):
        """
        Create all analog output tasks (galvo)
        """
        task_ao = nidaqmx.Task("AO")
        task_ao.ao_channels.add_ao_voltage_chan(self.ao0, min_val=minV, max_val=maxV)


    # TODO: get numbers of laser channels, determine line grouping
    # TODO: figure out the purpose of views

    def _create_do_task(self, *channels):
        """
        Create all digital output tasks (light sources)
        *channels: tuple of strings, e.g. ("488", "561", "LED")
        """
        task_do = nidaqmx.Task("DO")
        for chan in channels:
            task_do.do_channels.add_do_chan(chan)

    def _acquire(self, task_ao, task_do, *channels):
        pass

    def _get_ao_data(self):
        """ Get the array data to write to the ao channels during 
        acquisition """
        pass

        # TODO: determine if we can include here the function of the amplifier
        # TODO: verify that we don't want data generated in real time
        # TODO: what is the readout time
        # TODO: can (should?) all light sources be on at the same time?
        # TODO: we only want the light sources on when the camera is acquiring?

    def _get_do_data(self,
                       single_acq_time,
                       switch: bool,
                       channels):
        """Get the ndarray for the digital ouput of specific wavefo"""
        # DIGITAL IS YES/NO SO WILL ONLY HAVE TRUE/FALSE
        # TODO: do the 488 and 561 alternate, then leave the other in
        # the background?
        # TODO: what are the parameter that we typically want to control
        # TODO: cover both cases of using one and 2 cameras? (most likely - 
        # how to adjust the trigger? just leave one trigger and add readouts....)
        light_on = round((self.exposure_time - self.readout_time1) * self.sampling_rate)
    

    def _set_retriggerable_counter(self, counter):
        """set up a retriggerable counter task"""
        task_ctr = nidaqmx.Task()
        # create OUTPUT pulses at sampling rate
        # TODO: what is the pulse voltage?
        task_ctr.co_channels.add_co_pulse_chan_freq(counter,
                                                    idle_state=nidaqmx.constants.Level.LOW,
                                                    freq=self.sampling_rate)
        # TODO: revise these params 
        task_ctr.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                            samps_per_chan=self.num_samples)
        task_ctr.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=self.PFI0,
                                                                trigger_edge=nidaqmx.constants.Slope.RISING)
        task_ctr.triggers.start_trigger.retriggerable = True
        # The device ignores a trigger if it is in the process of acquiring or generating signals.
        return task_ctr
    

    # LINE 305: set do channel and make it retriggerable w a DIFFERENT data than what it writes to the do itself
    

        



