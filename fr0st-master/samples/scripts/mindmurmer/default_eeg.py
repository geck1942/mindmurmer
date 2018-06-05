import logging
import audiosources
import numpy as np
import wx
from utils import calculate_colors

class EEGSource:
    def __init__(self, channels):
        self.channelscount = channels

    def read_data(self):
        return [-3] * self.channelscount

class MMEngine:
    def __init__(self, EEGSource, AudioSource):
        self.EEGSource = EEGSource
        self.AudioSource = AudioSource
        self.frameindex = 0
        self.bounds = wx.Rect(-3,-3,6,6)

    def start(self):
        play = True
        while play:
            preview()
            # large_preview()
            play = self.render()
            # next form
            self.frameindex += 1

    def render(self):
        docontinue = True
        try:
            # get data as [] from ext. source
            eegdata = self.EEGSource.read_data()
            # get audio data from current input source
            audiodata = self.AudioSource.read_data()
            audiodata = self.GetFFT(audiodata)

            # FLAME UPDATE
            if(self.frameindex % 251 == 0):
                # Add a new form until 5
                # initialscale = 0.9
                # xform = flame.add_xform()
                # xform.scale(initialscale)
                # xform.rotate(0)
                # calculate_colors(flame.xform)
                randopt = { 'xv':range(1,6), 'n':2, 'xw':0, 'fx':True, "chance":.5 }
                newform = Xform.random(flame, **randopt)
                newform.animate = 1
                #flame.xform.append(newform)
                if(len(flame.xform) > 5):
                    del flame.xform[0]
            freqindex = 0
            # ROTATION
            for x in flame.xform:
                # calculate rotation amount from data elements
                if(x.animate and audiodata is not None):
                    audiodataindex = freqindex % len(audiodata)
                    rotx_delta = (audiodata[audiodataindex]) * 10
                    x.rotate(rotx_delta)
                freqindex += 1

            # MOVEMENT
            # every 257 frames is a cycle of X back and forth.
            if(self.frameindex % 147 < 73):
                movx_delta = -1
            else:
                movx_delta = 1
            # every 149 frames is a cycle of Y back and forth.
            if(self.frameindex % 61 < 30):
                movy_delta = -1
            else:
                movy_delta = 1

            for x in flame.xform:
                # calculate move amount from data elements
                if(x.animate and audiodata is not None):
                    audiodataindex = freqindex % len(audiodata)
                    movx_delta *= audiodata[audiodataindex] 
                    movy_delta *= audiodata[(freqindex + 1) % len(audiodata)]
                    #x.xp += movx_delta
                    #x.yp += movy_delta
                freqindex += 2

            return True
        except Exception as ex:
            print('error during rendering: ' + str(ex))
            docontinue = False

        # SHOW preview on Fr0st
        return docontinue


    def GetFFT(self, audiodata):

        fft = np.absolute(np.fft.rfft(audiodata, n=len(audiodata)))
        freq = np.fft.fftfreq(len(fft), d=1./self.AudioSource.getSampleRate())
        #max_freq = abs(freq[fft == np.amax(fft)][0]) / 2
        max_amplitude = 196 * 1000
        
        freqs = np.zeros(6)
        #indices = (len(fft) - np.logspace(0, np.log10(len(fft)), len(bins), endpoint=False).astype(int))[::-1]
        #for i in xrange(len(bins) - 1):
        #    bins[i] = np.mean(fft[indices[i]:indices[i+1]]).astype(int)
        #bins[-1] = np.mean(fft[indices[-1]:]).astype(int)
        
        step = int(len(fft) / len(freqs))
        for i in range(len(freqs)):
            freqs[i] = np.mean(fft[i:i+step])
            # custom noise reduction (remove anything below 20%)
            # + custom scale from 0:max_amplitude to 0:1
            freqs[i] = reduceAndClamp(freqs[i], 0, max_amplitude, 0, 1, False)
            # cubic easing
            #freqs[i] = freqs[i]**0.5
            #if(self.frameindex % 12 == 0 and i == 2) : print(str(freqs[i]))

        return freqs

def reduceAndClamp(inrange_value, inrange_min, inrange_max, outrange_min = 0, outrange_max = 1, overflow = False):
    inpct = (inrange_value - inrange_min) / (inrange_max - inrange_min)
    return clamp(inpct, outrange_min, outrange_max, overflow)

def clamp(percent, outrange_min = 0, outrange_max = 1, overflow = False):
    delta = outrange_max - outrange_min
    if (overflow == False and percent > 1): percent = 1
    if (overflow == False and percent < 0): percent = 0
    return (percent * delta) + outrange_min

def easing_cubic(percent, minvalue = 0, maxvalue = 1):
    percent *= 2
    if(percent < 1) : return ((maxvalue - minvalue) / 2) * percent * percent * percent + minvalue
    percent -= 2
    return ((maxvalue - minvalue) / 2) * (percent * percent * percent + 2) + minvalue

def easing_square(percent, minvalue = 0, maxvalue = 1):
    percent *= 2
    if(percent < 1) : return ((maxvalue - minvalue) / 2) * percent * percent + minvalue
    percent -= 2
    return ((maxvalue - minvalue) / 2) * (percent * percent + 2) + minvalue

def getAudioSource():
    print('Get Audio source')
    try:
        # record Microphone with Pyaudio    
        print('Recording Microphone with Pyaudio')
        mic = audiosources.Microphone()
        if (mic is not None):
            print('microphone is OK')            
            return mic

    except Exception as mic_ex:
        print('Could not record Microphone with Pyaudio: ' + str(mic_ex))
        try:
            # read test .wav with Pyaudio    
            print('Reading test media file')
            media = audiosources.MediaFile("audio/midnightstar_crop.wav")
            if (media is not None):
                print('media file OK')
                return media

        except Exception as file_ex:
            print('Could not read test media file: ' + str(file_ex))
    
    return None

eeg = EEGSource(5)
audio = getAudioSource()
engine = MMEngine(eeg, audio)
engine.start()