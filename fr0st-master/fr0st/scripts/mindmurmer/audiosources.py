import sys
import numpy as np
import wave
import pyaudio

# RUNNING SETTINGS
chunksize = 1024

# microphone SETTINGS
SAMPLE_MAX = 32767
SAMPLE_MIN = -(SAMPLE_MAX + 1)
SAMPLE_RATE = 16000 # [Hz]
NYQUIST = SAMPLE_RATE / 2 
SAMPLE_SIZE = 16 # [bit]
CHANNEL_COUNT = 1
BUFFER_SIZE = 5000 

MEDIASAMPLE_RATE = 44000 # [Hz]
MEDIACHANNEL_COUNT = 2

class AudioSource:
    def __init__(self):
        self.outstream = None

    def getSampleRate(self):
        return MEDIASAMPLE_RATE
        
    def getSampleMax(self):
        return SAMPLE_MAX

class MediaFile(AudioSource):

    def __init__(self, filepath):
        """ Init audio stream """ 
        self.wf = wave.open(filepath, 'rb')
        self.p = pyaudio.PyAudio()
        self.outstream = self.p.open(
            format = self.p.get_format_from_width(self.wf.getsampwidth()),
            channels = MEDIACHANNEL_COUNT,
            rate = self.getSampleRate(),
            output = True
        )

    # read_data is the method shared among audiosources 
    # that should be calles (parameterless) to read data as a stream.
    def read_data(self):
        audiosource_data = self.wf.readframes(chunksize)
        # set as audio ouput what we just read.
        if audiosource_data != '':
            self.outstream.write(audiosource_data)

        # convert and return readable data
        data = np.fromstring(audiosource_data, 'int16').astype(float)
        if len(data):
            return data

    def close(self):
        self.outstream.close()
        self.p.terminate()

class Microphone(AudioSource):

    def __init__(self):
        self.p = pyaudio.PyAudio()

        self.outstream = self.p.open(
                        format = pyaudio.paInt16,
                        channels = CHANNEL_COUNT,
                        rate = self.getSampleRate(),
                        output = True)
        self.micstream = self.p.open(format = pyaudio.paInt16,
                        channels = CHANNEL_COUNT,
                        rate = self.getSampleRate(),
                        input = True,
                        frames_per_buffer = BUFFER_SIZE)

    # read_data is the method shared among audiosources 
    # that should be calles (parameterless) to read data as a stream.
    def read_data(self):
        audiosource_data = self.micstream.read(self.micstream.get_read_available())
        # set as audio ouput what we just read.
        self.outstream.write(audiosource_data)

        # convert and return readable data
        data = np.fromstring(audiosource_data, 'int16').astype(float)
        if len(data):
            return data
            
    def getSampleRate(self):
        return SAMPLE_RATE

    def close(self):
        self.outstream.close()
        self.micstream.close()
        self.p.terminate()