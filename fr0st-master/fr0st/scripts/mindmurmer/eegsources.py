import random
import numpy as np
import json

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
        self.raw_data = [0.0] * 21
        
    def read_data(self):
        return EEGData(self.raw_data)


class EEGDummy(EEGSource):
    def __init__(self):
        super(EEGDummy, self).__init__()

        # 4 x alpha + 4 x beta + 4 x gamma + 4 x delta + 4 x theta
        for i in range(self.channels * 5):
            self.raw_data[i] = 0.5
        # blink
        self.raw_data[self.channels * 5] = 0

    # generate dummy EEG data
    def read_data(self):
        # random oscillation
        for x in range(self.channels * 5):
            self.raw_data[x] += random.uniform(-0.03, 0.03)

        # blink on random 0.05%
        if(random.random() >= 0.995):
            self.raw_data[self.channels * 5] = 1
        else:
            self.raw_data[self.channels * 5] = 0

        return EEGData(self.raw_data)


class EEGFromJSONFile(EEGSource):
    def __init__(self, filepath):
        super(EEGFromJSONFile, self).__init__()
        # open json file
        self.sample_length = 0
        self.sample_index = 0

        try:
            with open(filepath) as f:
                json_data = json.load(f)
                print('file loaded')

                self.sample_length = len(json_data['timeseries']['alpha_relative']['timestamps'])
                print(str(self.sample_length) + ' samples found')

                self.channels = json_data['meta_data']['config'][0]['eeg_channel_count']
                print(str(self.channels) + ' channels found')

                self.raw_data = []

                for i in range(self.sample_length):
                    eeg_sample_data = (json_data['timeseries']['alpha_relative']['samples'][i] +
                                       json_data['timeseries']['beta_relative']['samples'][i] +
                                       json_data['timeseries']['gamma_relative']['samples'][i] +
                                       json_data['timeseries']['delta_relative']['samples'][i] +
                                       json_data['timeseries']['theta_relative']['samples'][i] +
                                       json_data['timeseries']['blink']['samples'][i])
                    self.raw_data.append(EEGData(eeg_sample_data))
        except Exception as jsonex:
            print('error during loading JSON: ' + str(jsonex))

    # iterate samples
    def read_data(self):
        if(self.sample_index >= self.sample_length):
            print("SAMPLE JSON file is over. Restart")
            self.sample_index = 0

        sample_data = self.raw_data[self.sample_index]
        self.sample_index += 1

        return sample_data

class EEGFromAudioFile(EEGSource):
    def __init__(self, audio_source):
        super(EEGFromAudioFile, self).__init__() 
        self.audio_source = audio_source
        # blink
        self.raw_data[self.channels * 5] = 0

    def read_data(self):
        # read audio data
        audio_data = self.audio_source.read_data()
        audio_data = self.GetFFT(audio_data)

        self.raw_data[0: self.channels * 5] = audio_data if audio_data is not None else [0 for i in range(len(self.raw_data[0: self.channels * 5]))]

        # blink on random 0.05%

        if(random.random() >= 0.995):
            self.raw_data[self.channels * 5] = 1
        else:
            self.raw_data[self.channels * 5] = 0

        return EEGData(self.raw_data)

    def GetFFT(self, audio_data):
        if audio_data is None:
            return None

        # generate an FFT over 5 x n channels
        freqs = np.zeros(self.channels * 5)

        fft = np.absolute(np.fft.rfft(audio_data, n=len(audio_data)))
        freq = np.fft.fftfreq(len(fft), d=1./self.audio_source.get_sample_rate())
        max_freq = abs(freq[fft == np.amax(fft)][0]) / 2
        max_amplitude = np.amax(audio_data)

        #indices = (len(fft) - np.logspace(0, np.log10(len(fft)), len(bins), endpoint=False).astype(int))[::-1]
        #for i in xrange(len(bins) - 1):
        #    bins[i] = np.mean(fft[indices[i]:indices[i+1]]).astype(int)
        #bins[-1] = np.mean(fft[indices[-1]:]).astype(int)
        
        step = int(len(fft) / len(freqs))
        for i in range(len(freqs)):
            freqs[i] = np.mean(fft[i:i+step]) / float(self.audio_source.get_sample_max()) / 10
            # custom noise reduction (remove anything below 10%)
            # + custom scale from 0:max_amplitude to 0:1
            # freqs[i] = reduceAndClamp(freqs[i], 0.1, 1, 0, 1, False)
            # cubic easing
            # freqs[i] = freqs[i]**0.5
            #if(i == 2) : print(str(freqs[i]))

        return freqs

class EEGFromAudio(EEGSource):
    def __init__(self, audio_source):
        super(EEGFromAudio, self).__init__() 
        self.audio_source = audio_source
        # blink
        self.raw_data[self.channels * 5] = 0

    # generate dummy EEG data
    def read_data(self):
        # read audio data
        audio_data = self.audio_source.read_data()
        audio_data = self.GetFFT(audio_data)

        self.raw_data[0: self.channels * 5] = audio_data if audio_data is not None else [0 for i in range(len(self.raw_data[0: self.channels * 5]))]

        # blink on random 0.05%

        if(random.random() >= 0.995):
            self.raw_data[self.channels * 5] = 1
        else:
            self.raw_data[self.channels * 5] = 0

        return EEGData(self.raw_data)

    def GetFFT(self, audio_data):
        if audio_data is None:
            return None

        # generate an FFT over 5 x n channels
        freqs = np.zeros(self.channels * 5)

        fft = np.absolute(np.fft.rfft(audio_data, n=len(audio_data)))
        freq = np.fft.fftfreq(len(fft), d=1./self.audio_source.get_sample_rate())
        max_freq = abs(freq[fft == np.amax(fft)][0]) / 2
        max_amplitude = np.amax(audio_data)

        #indices = (len(fft) - np.logspace(0, np.log10(len(fft)), len(bins), endpoint=False).astype(int))[::-1]
        #for i in xrange(len(bins) - 1):
        #    bins[i] = np.mean(fft[indices[i]:indices[i+1]]).astype(int)
        #bins[-1] = np.mean(fft[indices[-1]:]).astype(int)
        
        step = int(len(fft) / len(freqs))
        for i in range(len(freqs)):
            freqs[i] = np.mean(fft[i:i+step]) / float(self.audio_source.get_sample_max()) / 10
            # custom noise reduction (remove anything below 10%)
            # + custom scale from 0:max_amplitude to 0:1
            # freqs[i] = reduceAndClamp(freqs[i], 0.1, 1, 0, 1, False)
            # cubic easing
            # freqs[i] = freqs[i]**0.5
            #if(i == 2) : print(str(freqs[i]))

        return freqs

