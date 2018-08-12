## Dependencies
1. Please install the `SWMixer` Python packahe by following instructions [here](https://github.com/nwhitehead/swmixer) (install MAD lib too for mp3 support)


## Spinning up the Soundscape sound controller demo
The controller need three inputs:

1. An audio folder
2. An up transition sound filename
3. A down transition sound filename

For the audio folder, its structure should be a set of folders where each folder name is a number symbolizing the meditation stage it's for, having `0`
for the lightest mode. Each folder should contain one track for the heartbeat of that stage with the text `heartbeat` in it and at least another track which is the sound scape track

```
python sounds_controllers/sound_controller.py --audio_folder fr0st-master/fr0st/scripts/mindmurmer/sounds_controller_files/16000hz-24bit/mp3/audio --up_transition_sound_filename fr0st-master/fr0st/scripts/mindmurmer/sounds_controller_files/16000hz-24bit/mp3/transition_up.mp3 --down_transition_sound_filename fr0st-master/fr0st/scripts/mindmurmer/sounds_controller_files/16000hz-24bit/mp3/transition_down.mp3
```