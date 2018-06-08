import logging
import random
import audiosources
import numpy as np
import wx
from utils import calculate_colors

class EEGSource:
    def __init__(self, channels):
        self.channelscount = channels
        self.values = [0.5] * self.channelscount

    def read_data(self):
        # generate dummy EEG data
        for x in range(0, self.channelscount):
            self.values[x] += random.uniform(-0.03, 0.03)
        return self.values

class MMEngine:
    def __init__(self, EEGSource, AudioSource):
        self.EEGSource = EEGSource
        self.AudioSource = AudioSource
        self.frameindex = 0
        self.speed = 1
        self.channels = 24
        self.sinelength = 300 # frames

    def start(self):
        play = True
        while play:
            play = self.render()
            self.frameindex += 1

            #    preview() for animating wireframe window
            # OR large_preview() for animating rendered window
            large_preview()
            preview()


    def render(self):
        docontinue = True
        try:
            # get eeg data as [] from ext. source
            eegdata = self.EEGSource.read_data()
            # get audio data from current input source
            audiodata = self.AudioSource.read_data()
            audiodata = self.GetFFT(audiodata)

            # FLAME UPDATE
            if(self.frameindex % 251 == 123):
                # Add a new form
                # x = flame.add_xform()
                # x.coefs = [1, 0, 0.1, 0.2, 0, 0]
                # x.a = -1.0
                # x.xp += random.uniform(-.5, +.5)
                # x.yp += random.uniform(-.5, +.5)
                # x.op += random.uniform(-.5, +.5)
                # x.linear = 1
                # x.weight = 1
                # x.color = random.random()
                # x.color_speed = random.uniform(0,0.1)
                # x.rotate(random.random() * 360)
                # x.animate = 1

                # remove form older than 3
                if(len(flame.xform) > 3):
                    del flame.xform[0]

                # move window
                #flame.reframe()

                # update colors
                #calculate_colors(flame.xform)
                
            dataindex = 0
            for x in flame.xform:
                if(x.animate and audiodata is not None):
                    # ROTATION
                    # calculate rotation amount from data elements
                    data = audiodata[dataindex % len(audiodata)]
                    dataindex += 1 # next data from audiodata
                    x.rotate(data * 0.5 * self.speed)

                    # MOVEMENT
                    # calculate move amount from data elements
                    data = audiodata[dataindex % len(audiodata)]
                    dataindex += 1 # next data from audiodata
                    # every n frames is a cycle of X back and forth.
                    data *= np.sin(self.frameindex * (np.pi * 2) / self.sinelength)
                    mov_delta = data * 0.01 * self.speed
                    # move triangle x, y, o points
                    x.xp += mov_delta
                    x.yp += mov_delta
                    x.op += mov_delta

                    # transform the triangle by moving again, one vertice
                    data = audiodata[dataindex % len(audiodata)] 
                    dataindex += 1 # next data from audiodata
                    # every n frames is a cycle of X back and forth.
                    data *= np.sin(self.frameindex * (np.pi * 2) / self.sinelength)
                    x.yp += data * 0.01 * self.speed
                    
                    # COEFS
                    # change one of the coefficients
                    data = audiodata[dataindex % len(audiodata)]
                    dataindex += 1 # next data from audiodata
                    coefindex = random.randint(0, 31)
                    x.coefs[coefindex] =  x.coefs[coefindex] + data * 0.05 * self.speed

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
        
        freqs = np.zeros(self.channels)
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

# static math methods:
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

# static audio source method:
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

# RUN
eeg = EEGSource(24)
audio = getAudioSource()

engine = MMEngine(eeg, audio)
engine.start()