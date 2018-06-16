import logging
import random
import numpy as np
import wx
from utils import calculate_colors, normalize_weights
from prefabs import FlamePrefabs

import audiosources
from eegsources import * 

class MMEngine:
    def __init__(self, EEGSource, AudioSource):
        self.EEGSource = EEGSource
        self.AudioSource = AudioSource
        self.frameindex = 0
        self.speed = 1
        self.channels = 24
        self.sinelength = 300 # frames
        self.prefabs = FlamePrefabs()

    def start(self):
        play = True
        while play:
            #    preview() for animating wireframe window
            # OR large_preview() for animating rendered window
            large_preview()
            #preview()

            play = self.render()
            self.frameindex += 1



    def render(self):
        docontinue = True
        if (flame.xform is None or len(flame.xform) == 0):
            return False
        try:
            # get eeg data as [] from ext. source
            eegdata = self.EEGSource.read_data()
            # get audio data from current input source
            audiodata = self.AudioSource.read_data()
            audiodata = self.GetFFT(audiodata)

            # shows the spectrum of the current data:
            showFFT(audiodata)

            # FLAME UPDATE (at least 25 frames apart)
            if(eegdata.blink == 1 and self.frameindex > 2500):
                self.NewFlame()
                self.frameindex = 0
                print("BLINK: new flames generated")
                # adjust form weights (from utils)
                #normalize_weights(flame)
                
                # move window
                #flame.reframe()

                # update colors
                #calculate_colors(flame.xform)

            dataindex = 0
            for x in flame.xform:
                if(x.animate and audiodata is not None):
                    # ROTATION
                    # calculate rotation amount from data elements
                    data = eegdata.waves[dataindex % len(eegdata.waves)]
                    dataindex += 1 # next data from audiodata
                    x.rotate(data * 1.5 * self.speed)

                    # MOVEMENT
                    # calculate move amount from data elements
                    data = eegdata.waves[dataindex % len(eegdata.waves)]
                    dataindex += 1 # next data from audiodata
                    # every n frames is a cycle of X back and forth.
                    data *= np.sin(self.frameindex * (np.pi * 2) / self.sinelength)
                    mov_delta = data * 0.01 * self.speed
                    # move triangle x, y, o points
                    #x.xp += mov_delta
                    #x.yp += mov_delta
                    x.op += mov_delta

                    # # transform the triangle by moving again, one vertice
                    # data = audiodata[dataindex % len(audiodata)] 
                    # dataindex += 1 # next data from audiodata
                    # # every n frames is a cycle of X back and forth.
                    # data *= np.sin(self.frameindex * (np.pi * 2) / self.sinelength)
                    # #x.yp += data * 0.01 * self.speed
                    
                    # COEFS
                    # change one of the coefficients
                    # data = audiodata[dataindex % len(audiodata)]
                    # dataindex += 1 # next data from audiodata
                    # coefindex = random.randint(0, len(x.coefs))
                    # x.coefs[coefindex] =  x.coefs[coefindex] + data * 0.05 * self.speed

            return True
        except Exception as ex:
            print('error during rendering: ' + str(ex))
            docontinue = False

        # SHOW preview on Fr0st
        return docontinue

    # Generate a whole new Flame
    def NewFlame(self):
        
        # if(not flame.final is None):
        #     flame.final.delete()
        # l = len(flame.xform)
        # # cannot remove form #0
        # for i in range(l-1):
        #     flame.xform[-1].delete()
        
        # flame.xform[-1].delete()
        #flame.xform =[]
        
        ran = random.uniform
        # based on julia lines:
        # Form 1: BASE
        if(len(flame.xform) == 0):
            x1 = flame.add_xform()
        else:
            x1 = flame.xform[0]
        # x1.coefs = [1, 0,    # x
        #             0, 1,    # y
        #             ran(-0.2, 0.2), ran(-0.2, 0.2) ]    # o around 0
        x1.weight = 0.25
        x1.color = random.random() # [0 : 1]
        x1.color_speed = 0.9
        x1.noise = 0.0 + random.random() * 0.4 # [0.0 : 0.4]
        x1.blur = 0.0 + random.random() * 0.1 # [0.0 : 0.1]
        x1.animate = 1
        x1.rotate(random.random() * 360)

        # Form 2: JULIA TRANSFORM
        if(len(flame.xform) > 1):
            x2 = flame.xform[1]
            # x2.coefs = [0.5, 0,    # x
            #             0, 0.5,    # y
            #             ran(-0.5, 0.5), ran(-0.5, 0.5) ]    # o
            x2.weight = 0.5
            # x2.color = random.random() # [0 : 1]
            x2.color_speed = 0.5
            x2.julian = 0.7 + random.random() * 0.3 # [0.7 : 1]
            x2.animate = 1
            x2.rotate(random.random() * 360)

        # Form 3: LINE
        if(len(flame.xform) > 2):
            x3 = flame.xform[2]
            # x3.coefs = [ran(1, 3), 0,    # x
            #             0, 0,    # y
            #             ran(-1.0, 1.0), ran(-1.0, 1.0) ]    # o
            x3.weight = 0.25
            # x3.color = random.random() # [0 : 1]
            x3.color_speed = 0.5
            x3.cross = 0.5 + random.random() * 1.5 # [0.5 : 2]
            x3.julian = 0.2 + random.random() * 0.8 # [0.2 : 1]
            x3.animate = 1
            x3.rotate(random.random() * 360)

        # Form 4: FLOWERS
        if(len(flame.xform) > 3):
            x4 = flame.xform[3]
            # x4.coefs = [0.5, 0,    # x
            #             0, 0.5,    # y
            #             ran(-0.5, 0.5), ran(-0.5, 0.5) ]    # o                    
            x4.weight = 0.25
            # x4.color = random.random() # [0 : 1]
            x4.color_speed = 0.9
            x4.julian = 0.9 + random.random() * 0.1 # [0.9 : 1]
            x4.animate = 1
            x4.rotate(random.random() * 360)

        # Form 5: FINAL
        if(not flame.final is None):
            x5 = flame.final
            # x5.coefs = [1, 0,    # x
            #             0, 1,    # y
            #             ran(-0.5, 0.5), ran(-0.5, 0.5) ]    # o around 0
            # x5.color = 0.0
            x5.color_speed = 0.0
            x5.spherical = 0.1 + random.random() * 0.9 # [0.1 : 1]
            x5.julia = 0.1 + random.random() * 0.4 # [0.1 : 0.5]
            x5.linear = 0.0
            x5.rotate(random.random() * 360)

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

# static wx Painting methods:
def showFFT(audiodata):
    # dc = wx.PaintDC(wx.App.MainWindow.previewframe)
    # dc.SetPen(wx.Pen(wx.WHITE, 4))
    # dc.DrawLine(0, 0, 50, 50)
    return

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
eeg = EEGDummy()
audio = getAudioSource()

engine = MMEngine(eeg, audio)
engine.start()