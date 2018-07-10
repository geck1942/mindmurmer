rem Use sox, an open source audio tool, available at http://sox.sourceforge.net/
rem These values arereasonably pleasing, they are from
rem https://github.com/carlthome/python-audio-effects/blob/master/pysndfx/dsp.py

rem reverb filter values
reverberance=50
hf_damping=50
room_scale=100
stereo_depth=100
pre_delay=20
wet_gain=0

rem lowpass filter values
lowpass_freq=1000
lowpass_q=0.707q

rem sox arguments to open the mic and speaker
default_input_device=-d
default_output_device=-d



rem Use sox to stream from the default input device to the default output device
rem and apply reverb and a lowpass filter, to cut out high frequency sounds from
rem the HeartBuds device.

sox.exe %default_input_device% %default_output_device%^
 reverb %reverberance% %hf_damping% %room_scale% %stereo_depth% %pre_delay% %wet_gain%^
 lowpass %lowpass_freq% %lowpass_q%
