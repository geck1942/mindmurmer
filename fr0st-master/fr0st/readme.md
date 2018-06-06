# mindmurmer
## about
original fr0st application: Fractlat Fr0st fr0stlib
https://code.launchpad.net/fr0st
## requirements:

The app is using **python v2.7**
the following libraries are required:
- **numpy**
- **pyaudio**
- **PySide**
- **wxPython** (wx 3.0, not the 4.0)
- **wave**

## the fr0st folder

under the fr0st folder, are stored
- **parameters**: library of flames, used as shapes for generating the fractals
- **scripts**: the scripts to run to animate and render the flames
- **config.cfg**: configuration file. Delete it to restore defaults.

This folder should be the default folder used by the app to load config from.
Depending on your folder location or operating system, you might want to **allow access to this folder** for python to run.

### parameters
The samples.flame are the default set of flames included in Fractal Fr0st. 

### scripts
In the scripts folder are the default scripts that came with Fractal Fr0st.
Some create random flames, others render pictures in batches.

the mindmurmer folder has the script used for running the EEG algorithm.

## RUN the application

run the following command to start the app:
```
python "./fr0st.py"
``` 
If running windows with both 2.7 and 3.6 versions of python, run:
```
py -2 "./fr0st.py"
``` 

## SETUP the preferences

Open the Edit > Preferences and reduce the default settings (if not done already).
exemple:
Preview: quality = 1, density = 0, filter radius = 0, oversample = 1
Large preview: quality = 25, density = 0, filter radius = 0.25, oversample = 2
xform: range = 1, quality = 5, depth = 2
**Renderer = flam4**
Misc > jpeg quality = 15

## START the visualization

Select the flame to use from the set by default or load a set of flames.
Show the preview window (right end of the toolbar) to see the rendered fractal.

Open the following script from the app:
```
./fr0st/scripts/default_eeg.py
```
Press the green light to see animation.