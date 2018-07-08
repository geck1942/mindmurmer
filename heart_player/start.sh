#!/bin/bash
# Use sox, an open source audio tool, available at http://sox.sourceforge.net/

# These values arereasonably pleasing, they are from
# https://github.com/carlthome/python-audio-effects/blob/master/pysndfx/dsp.py

# reverb filter values
reverberance=50
hf_damping=50
room_scale=100
stereo_depth=100
pre_delay=20
wet_gain=0

# lowpass filter values
lowpass_freq=1000
lowpass_q=0.707q

# sox arguments to open the mic and speaker
default_input_device=-d
default_output_device=-d



# Use sox to stream from the default input device to the default output device
# and apply reverb and a lowpass filter, to cut out high frequency sounds from
# the HeartBuds device.

sox $default_input_device $default_output_device \
reverb $reverberance $hf_damping $room_scale $stereo_depth $pre_delay $wet_gain \
lowpass $lowpass_freq $lowpass_q
