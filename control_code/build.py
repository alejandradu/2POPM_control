import nidaqmx
import nidaqmx.system
import numpy as np
import time
import matplotlib.pyplot as plt

# Create a workflow using the NI-DAQmx Python API to synchronize the 
# acquisition of a camera with the generation of an analog signal to control a 
# galvo mirror and digital signals to control 3 lasers. 

system = nidaqmx.system.System.local()  
# for device in system.devices:
#         print(f'Device Name: {device.name}')

# restart the system

def generate_custom_signal(task, frequency, amplitude, duration, sampling_rate):
    try:
        # Generate a custom analog output signal (e.g., a sine wave)
        t = np.arange(0, duration, 1 / sampling_rate)
        analog_output_signal = amplitude * np.sin(2 * np.pi * frequency * t)

        # # Plot the signal
        # plt.figure()
        # plt.scatter(t, analog_output_signal)
        # plt.xlabel('Time (s)')
        # plt.ylabel('Amplitude (V)')
        # plt.title('Analog Output Signal')
        # plt.show()

        # Configure the analog output task
        task.ao_channels.add_ao_voltage_chan("Dev1/ao0", min_val=-2.0, max_val=2.0)
        task.timing.cfg_samp_clk_timing(rate=sampling_rate, active_edge=nidaqmx.constants.Edge.RISING, sample_mode=nidaqmx.constants.AcquisitionType.FINITE)

        # Write the custom analog output signal to the analog output channel
        task.write(analog_output_signal, auto_start=False)

        # Read back the data
        # read_data = task.read(number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE)
        # print(f'Read data: {read_data}')

        # Run the task
        task.start()

        # Wait for the specified duration
        task.wait_until_done(timeout=duration*2)
    except Exception as e:
        print(f'An error occurred: {e}')
    finally:
        # Stop and clear the task
        if task.is_task_done():
            task.stop()
        task.close()


if __name__ == "__main__":
    # Define the parameters of the custom analog output signal
    frequency = 2.0  # Hz OF THE WAVE
    amplitude = 2.0  # Volts
    duration = 10.0
    sampling_rate = 100.0 # Hz OF MY SAMPLING

    # Create a NIDAQmx task for analog output
    with nidaqmx.Task() as task:
        generate_custom_signal(task, frequency, amplitude, duration, sampling_rate)
