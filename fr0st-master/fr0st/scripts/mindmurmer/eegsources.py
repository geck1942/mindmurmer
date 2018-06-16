
import random
import numpy as np
from utils import reduceAndClamp

class EEGData():
    # inline values
    def __init__(self, values):
        self.channels = (len(values)-1) / 5
        # each waves is average of 4 channels
        self.alpha = np.average(values[self.channels * 0 : self.channels * 1])
        self.beta  = np.average(values[self.channels * 1 : self.channels * 2])
        self.gamma = np.average(values[self.channels * 2 : self.channels * 3])
        self.delta = np.average(values[self.channels * 3 : self.channels * 4])
        self.theta = np.average(values[self.channels * 4 : self.channels * 5])
        # blink
        self.blink = values[self.channels * 5]
        # sum of the 5 waves
        self.waves = [self.alpha, self.beta, self.gamma, self.delta, self.theta]
    

class EEGSource(object):
    def __init__(self):
        self.channels = 4
        # raw data:
        # 4 channels x 5 waves
        # + blink = 21
        self.rawdata = [0.0] * 21
        
    def read_data(self):
        return EEGData(self.rawdata)


class EEGDummy(EEGSource):
    def __init__(self):
        super(EEGDummy, self).__init__() 
        # 4 x alpha + 4 x beta + 4 x gamma + 4 x delta + 4 x theta
        for i in range(self.channels * 5):
            self.rawdata[i] = 0.5
        # blink
        self.rawdata[self.channels * 5] = 0

    # generate dummy EEG data
    def read_data(self):
        # random oscillation
        for x in range(self.channels * 5):
            self.rawdata[x] += random.uniform(-0.03, 0.03)

        # blink on random 0.05%
        if(random.random() >= 0.995):
            self.rawdata[self.channels * 5] = 1
        else:
            self.rawdata[self.channels * 5] = 0

        return EEGData(self.rawdata)
        

class EEGFromAudio(EEGSource):
    def __init__(self, audiosource):
        super(EEGFromAudio, self).__init__() 
        self.audiosource = audiosource
        # blink
        self.rawdata[self.channels * 5] = 0

    # generate dummy EEG data
    def read_data(self):
        # read audio data
        audiodata = self.audiosource.read_data()
        audiodata = self.GetFFT(audiodata)
        self.rawdata[0 : self.channels * 5] = audiodata
        # blink on random 0.05%
        if(random.random() >= 0.995):
            self.rawdata[self.channels * 5] = 1
        else:
            self.rawdata[self.channels * 5] = 0

        return EEGData(self.rawdata)

    def GetFFT(self, audiodata):
        # generate an FFT over 5 x n channels
        freqs = np.zeros(self.channels * 5)

        fft = np.absolute(np.fft.rfft(audiodata, n=len(audiodata)))
        freq = np.fft.fftfreq(len(fft), d=1./self.audiosource.getSampleRate())
        max_freq = abs(freq[fft == np.amax(fft)][0]) / 2
        max_amplitude = np.amax(audiodata)

        
        #indices = (len(fft) - np.logspace(0, np.log10(len(fft)), len(bins), endpoint=False).astype(int))[::-1]
        #for i in xrange(len(bins) - 1):
        #    bins[i] = np.mean(fft[indices[i]:indices[i+1]]).astype(int)
        #bins[-1] = np.mean(fft[indices[-1]:]).astype(int)
        
        step = int(len(fft) / len(freqs))
        for i in range(len(freqs)):
            freqs[i] = np.mean(fft[i:i+step]) / float(self.audiosource.getSampleMax()) / 10
            # custom noise reduction (remove anything below 10%)
            # + custom scale from 0:max_amplitude to 0:1
            # freqs[i] = reduceAndClamp(freqs[i], 0.1, 1, 0, 1, False)
            # cubic easing
            # freqs[i] = freqs[i]**0.5
            #if(i == 2) : print(str(freqs[i]))

        return freqs

