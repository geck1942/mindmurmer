import numpy as np
import wave
import pyaudio
import os

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

class AudioSource(object):
    def __init__(self):
        self.out_stream = None

    def get_sample_rate(self):
        return MEDIASAMPLE_RATE

    def get_sample_max(self):
        return SAMPLE_MAX

class MediaFile(AudioSource):
    def __init__(self, filepath):
        """ Init audio stream """
        super(MediaFile, self).__init__()

        self.wf = wave.open(filepath, 'rb')
        self.p = pyaudio.PyAudio()
        self.outstream = self.p.open(
            format = self.p.get_format_from_width(self.wf.getsampwidth()),
            channels = MEDIACHANNEL_COUNT,
            rate = self.get_sample_rate(),
            output = True
        )


    # read_data is the method shared among audiosources 
    # that should be calles (parameterless) to read data as a stream.
    def read_data(self):
        audiosource_data = self.wf.readframes(chunksize)

        # set as audio ouput what we just read.
        if audiosource_data != '' and os.getenv("MINDMURMUR_PLAY_RECORDED_AUDIOSOURCE", "true").lower() == "true":
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
        super(Microphone, self).__init__()

        self.p = pyaudio.PyAudio()

        self.out_stream = self.p.open(
            format = pyaudio.paInt16,
            channels = CHANNEL_COUNT,
            rate = self.get_sample_rate(),
            output = True)
        self.mic_stream = self.p.open(format = pyaudio.paInt16,
                                      channels = CHANNEL_COUNT,
                                      rate = self.get_sample_rate(),
                                      input = True,
                                      frames_per_buffer = BUFFER_SIZE)

    # read_data is the method shared among audiosources 
    # that should be calles (parameterless) to read data as a stream.
    def read_data(self):
        audio_source_data = self.mic_stream.read(self.mic_stream.get_read_available())
        # set as audio ouput what we just read.

        if os.getenv("MINDMURMUR_PLAY_RECORDED_AUDIOSOURCE", "true").lower() == "true":
            self.out_stream.write(audio_source_data)

        # convert and return readable data
        data = np.fromstring(audio_source_data, 'int16').astype(float)
        if len(data):
            return data

    def get_sample_rate(self):
        return SAMPLE_RATE

    def close(self):
        self.out_stream.close()
        self.mic_stream.close()
        self.p.terminate()

# static audio source method:
def get_audio_source(filepath):
    print('Get Audio source')
    try:
        # record Microphone with Pyaudio
        print('Recording Microphone with Pyaudio')
        mic = Microphone()
        if (mic is not None):
            print('microphone is OK')
            return mic

    except Exception as mic_ex:
        print('Could not record Microphone with Pyaudio: ' + str(mic_ex))
        try:
            # read test .wav with Pyaudio
            print('Reading test media file')
            media = MediaFile(filepath)
            if (media is not None):
                print('media file OK')
                return media

        except Exception as file_ex:
            print('Could not read test media file: ' + str(file_ex))

    return None