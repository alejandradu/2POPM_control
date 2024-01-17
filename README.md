# FastMC: Module for fast multi-camera acquisition with the 2P-OPM

This repository contains all files required to run acquisition with the 2P-OPM as well as the results of the experiments presented in the Fall JP. 

1. FastMC_core.py : the implementation of all the 2P-OPM functions as described in the paper. Do not modify this file.

2. FastMC.py : the script for the user to run the program. Instructions are included at the top of the document, and the imaging parameters can be input here.

3. Links to videos in mp4 format, with reference to the paper figures (the quality is decreased for file compression requirements):

- Figure 14:
  
- grid scan with Micro-Manager (raw data): https://drive.google.com/file/d/14FUdQYWjKBHMniXpj3h9dwHfg-zhCZvT/view?usp=sharing

- grid scan with FastMC (raw data): https://drive.google.com/file/d/17qjWqrYO1qL1TqZTJ0aX7w794sfaoeBY/view?usp=sharing

- Figure 16:
  
- ArgoSIM matrix with crosses scan (reconstructed, and only frames focused at some point of the matrix selected): https://drive.google.com/file/d/1THlw7nOFJ_tkmjFs6G8xzd5oZr6pbaz8/view?usp=sharing

4. JP_notebook : Jupyter notebook where I documented the progress over the semester. It is mainly composed of PicoScope (oscilloscope) measures of the input/output signals of the NI-DAQ, cameras, lights, and galvo mirror. The logic behind FastMC changed over time, so the first results recorded do not reflect the current behavior of the program.

5. development : folder with past Python scripts used as scratch work.

6. data_analysis : folder with the files and scripts used to generate the figures presented in the paper. (Note: to properly visualize 1p_2p_fluorescence.nb, it must be opened with Mathematica.)

7. Daxi_Yang_et_al_resources : part of the repository https://github.com/royerlab/daxi . The files here were used as a starting point to build FastMC.

