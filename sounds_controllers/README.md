## Dependencies
1. Please install `SWMixer` by following instrcutions [here](https://github.com/nwhitehead/swmixer)


## Spinning up the Heartbeat sound controller demo

The expected input folder form is:
A set of folders where each folder name is of the form `x_y` (`x` is the start rate for the heartbeat track and `y`
is the end of it, i.e. `1_50` folder would contain the heartbeat sound for heartrates between 1 bpm and 50 bpm.

```
python sounds_controllers/sound_controller.py --mode heartbeat --audio_folder sounds_controllers/sound_controller_demo_files/heartbeat_controller_demo_files
```

## Spinning up the Soundscape sound controller demo
The expected input folder form is:
A set of folders where each folder name is a number symbolizing the meditation stage it's for, having `0`
for the lightest mode.

```
python sounds_controllers/sound_controller.py --mode soundscape --audio_folder sounds_controllers/sound_controller_demo_files/soundscape_controller_demo_files
```