import pyaudio
import time
import numpy as np
from scipy.signal import butter, lfilter, freqz

order=6
lowpass_cutoff=1000
amplification_factor=10

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


WIDTH = 2
CHANNELS = 1
RATE = 44100
delay         = 40      # samples
release_coeff = 0.5555  # release time factor
attack_coeff  = 0.5     # attack time factor
dtype         = np.int16 # default data type

class Limiter:
    def __init__(self, attack_coeff, release_coeff, delay):
        self.delay_index = 0
        self.envelope = 0
        self.gain = 1
        self.delay = delay
        self.delay_line = np.zeros(delay)
        self.release_coeff = release_coeff
        self.attack_coeff = attack_coeff

    def limit(self, signal, threshold):
        for i in np.arange(len(signal)):
            self.delay_line[self.delay_index] = signal[i]
            self.delay_index = (self.delay_index + 1) % self.delay

            # calculate an envelope of the signal
            self.envelope *= self.release_coeff
            self.envelope = max(abs(signal[i]), self.envelope)

            # have self.gain go towards a desired limiter gain
            if self.envelope > threshold:
                target_gain = (1+threshold-self.envelope)
            else:
                target_gain = 1.0
            self.gain = ( self.gain*self.attack_coeff +
                          target_gain*(1-self.attack_coeff) )

            # limit the delayed signal
            signal[i] = self.delay_line[self.delay_index] * float(self.gain)


p = pyaudio.PyAudio()
limiter = Limiter(attack_coeff, release_coeff, delay)

def callback(in_data, frame_count, time_info, status):
    samples = np.fromstring(in_data, dtype=dtype)

    # fft = np.fft.fft(samples)

    if max(samples) > 3000 or min(samples) < -3000:
        samples = np.zeros(frame_count, dtype=dtype)
    # print(min(samples), max(samples), highest_nonzero_index)

    # amplify the signal 5x
    for i in range(len(samples)):
    	samples[i] = samples[i] * amplification_factor

    # audio_data = [s/float(65536) for s in samples]
    # filtered_audio_data = butter_lowpass_filter(audio_data, lowpass_cutoff, RATE, order)
    # print(min(audio_data), max(audio_data), min(filtered_audio_data), max(filtered_audio_data))
    # limiter.limit(audio_data, 0.8)
    # out_samples = [int(s*65536) for s in filtered_audio_data]
    # out_data = np.array(out_samples, dtype=dtype).tostring()
    # for i in range(len(in_samples)):
    #     if in_samples[i] < -3000:
    #         in_samples[i] = -3000
    #     if in_samples[i] > 3000:
    #         in_samples[i] = 3000

    # print(min(in_samples), max(in_samples), min(audio_data), max(audio_data), min(out_samples), max(out_samples))
    return (samples.tostring(), pyaudio.paContinue)
    # return (out_data, pyaudio.paContinue)

stream = p.open(format=p.get_format_from_width(WIDTH),
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                stream_callback=callback)

stream.start_stream()

while stream.is_active():
    time.sleep(0.1)

stream.stop_stream()
stream.close()

p.terminate()
