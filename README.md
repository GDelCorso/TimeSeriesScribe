# TimeSeriesScribe

TimeSeriesScribe is an open-source versatile package which can be used to create a time segmentation of a signal with multiple channels. A tecnical review of the package can be found "TimeSeriesScribe: Open-source Platform for Enhanced
Annotation in Multi-channel Signal processing" with examples of its use in Eosinophilic esophagitis segmentation. 

## How to cite it
FARE DOPO SCHOLAR

## Creation of the executable file

An executable script (.exe) can be made with the use of the python package PyInstaller. To create the executable script run the following lines in a prompt terminal inside the cloned folder of the repository:

if you don't have PyInstaller installed then install it as follows
- pip install PyInstaller 

to create the executable copy and paste the follow line in the terminal
- python -m PyInstaller -F GUI_TimeSeriesScribe.py

The last sentence will create two folders: build and dist. Inside the dist folder the executable file is created (GUI_TimeSeriesScribe.exe). Executable can then be moved to the desired location. 

## Script modification and adaptibility 

At the moment the script is built to visualize a 6+1 multichannel signal in which 6 channels have the same dynamic measurement range and the last one its single case. 






