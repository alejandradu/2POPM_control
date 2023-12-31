import MAIN2

nidaq = MAIN2.NIDAQ(
            num_stacks = 10,                # number of 3D stacks if multi d, number of frames if not
            stack_delay_time = 0.0,        # s. time between acquiring any 2 stacks
            exposure_time = 100e-3,           # s. effective exposure will be less due to system delay
            readout_mode = "fast",              # camera readout mode "fast" or "slow"
            lightsheet = False,               # lightsheet mode
            multi_d = False,                  # multidimensional acquisition
            z_start = 0.0,                  # microm. start of z stack
            z_end = 0.0,                            # ASSUMING 175 nm = 20 deg
            num_z_slices = 0,                       # TODO: is it more useful to have a step or a number of slices?
            image_height = 2048,      # px. vertical ROI. Defines frame readout time
            image_width = 2048,        # px. horizontal ROI
            frame_delay_time = 0.0,         # ms. optional delay after each frame trigger
            samples_per_exp = 10,           # sampling to write data for each cam exposure >= 2 by nyquist thm.
            samples_per_stack = 100,         # sampling to write data for each stack
            rf_freq = 1e6)                   # RF frequency of AOTF

nidaq.acquire()

# IMPLEMENT DELAY BETWEEN DIFFERENT STACKS