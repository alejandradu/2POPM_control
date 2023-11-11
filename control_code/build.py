import nidaqmx
import nidaqmx.system
import numpy as np
import time

# Create a workflow using the NI-DAQmx Python API to synchronize the 
# acquisition of a camera with the generation of an analog signal to control a 
# galvo mirror and digital signals to control 3 lasers. 

test_Task = nidaqmx.Task()
test_Task.ao_channels.add_ao_voltage_chan('myDAQ1/ao1')
test_Task.timing.cfg_samp_clk_timing(rate= 80, sample_mode= nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan= 40)

test_Writer = nidaqmx.stream_writers.AnalogSingleChannelWriter(test_Task.out_stream, auto_start=True)

samples = np.append(5*np.ones(30), np.zeros(10))

test_Writer.write_many_sample(samples)
test_Task.wait_until_done()
test_Task.stop()
test_Task.close()