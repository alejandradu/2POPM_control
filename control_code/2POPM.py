import nidaqmx
import nidaqmx.system
import numpy as np
import time

# Create a workflow using the NI-DAQmx Python API to synchronize the 
# acquisition of a camera with the generation of an analog signal to control a 
# galvo mirror and digital signals to control 3 lasers. 

class nidaq:
    # Channel ports             # not all ports assigned yet
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

    # Digital and timing I/O
    di0 = "Dev1/port0/line0"   # laser 1
    di1 = "Dev1/port0/line1"   # laser 2
    di2 = "Dev1/port0/line2"   # LED
    di3 = "Dev1/port0/line3"

    # TODO: constants

    def __init__(self):
        """
        Initialize the NI-DAQmx system and create a task for each channel.
        """

        # TODO: add all instance attributes, including properties
        pass

    def _create_ao_task(self, minV, maxV):
        """
        Create all analog output tasks (galvo)
        """
        task_ao = nidaqmx.Task()
        task_ao.ao_channels.add_ao_voltage_chan(channel, min_val=minV, max_val=maxV)

    def _create do_task(self, cha)





