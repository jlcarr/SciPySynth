from playsound import playsound
import sys

import numpy as np
from scipy.io import wavfile
from scipy import signal

import matplotlib.pyplot as plt


class oscillator:
	def __init__(self, amp=1.0, shape='sine', attack=0.5, decay=0.25, sustain=0.5, release=1., voices=1, detune=0.):
		self.amp = amp
		self.shape = shape

		self.attack = attack
		self.decay = decay
		self.sustain = sustain
		self.release = release

		self.voices = voices
		self.detune = detune

		self.filters = []
		self.reverb = []

	def add_filter(self, sos):
		self.filters.append(sos)

	def add_reverb(self, impulse_response):
		self.reverb.append(impulse_response)

	def play_note(self, fs, hold, samplerate=44100):
		t_tot = hold + self.release
		size = int(t_tot*samplerate)
		t = np.linspace(0., t_tot, size)
		data = np.zeros(size)
		envelope = np.zeros(size)

		t_start, t_end = 0, min(self.attack,hold)
		start, end = int(t_start*samplerate), int(t_end*samplerate)
		envelope[start:end] = np.linspace(0., 1., end-start)

		if hold > self.attack:
			t_start, t_end = t_end, min(self.attack+self.decay,hold)
			start, end = int(t_start*samplerate), int(t_end*samplerate)
			envelope[start:end] = np.linspace(1., self.sustain, end-start)

		if hold > self.attack+self.decay:
			t_start, t_end = t_end, hold
			start, end = int(t_start*samplerate), int(t_end*samplerate)
			envelope[start:end] = self.sustain*np.ones(end-start)

		t_start, t_end = t_end, t_end+self.release
		start, end = int(t_start*samplerate), int(t_end*samplerate)
		envelope[start:end] = self.sustain*np.linspace(1., 0., end-start)
		

		wave_func = np.sin
		if self.shape == 'sawtooth':
			wave_func = signal.sawtooth
		if self.shape == 'square':
			wave_func = signal.square
		if self.shape == 'whitenoise':
			wave_func = lambda t: np.random.normal(0.0, 1.0, size=t.size)
		if self.shape == 'brownnoise':
			wave_func = lambda t: np.cumsum(np.random.normal(0.0, 1.0, size=t.size))

		data += wave_func(2. * np.pi * fs * t)
		for voice in range(1,self.voices//2 + 1):
			data += wave_func(2. * np.pi * fs * 2**(voice*self.detune) * t)
			data += wave_func(2. * np.pi * fs * 2**(-voice*self.detune) * t)
		
		data *= envelope

		for sos in self.filters:
			data = signal.sosfilt(sos, data)

		for impulse_response in self.reverb:
			data = signal.convolve(data, impulse_response, mode='same')#[:data.shape[0]]

		data *= self.amp * np.iinfo(np.int16).max / np.max(np.abs(data))
		return data


class synth:
	def __init__(self, samplerate=44100):
		self.samplerate = samplerate
		self.oscillators = []

	def add_oscillator(self, osc):
		self.oscillators.append(osc)


	def play_notes(self, fs, hold = 1.):
		t_tot = hold + max([osc.release for osc in self.oscillators])
		size = int(t_tot*self.samplerate)
		t = np.linspace(0.0, t_tot, size)
		data = np.zeros(size)
		
		for osc in self.oscillators:
			data += osc.play_note(fs, hold, self.samplerate)

		return data



samplerate=44100
fs = 261.63
t_tot = 4.
s = synth()

osc = oscillator(shape='sawtooth', attack=1.5, decay=0.0, sustain=1.0, release=3., voices=5, detune = 0.01)
sos = signal.butter(2, fs, 'lowpass', fs=samplerate, output='sos')
osc.add_filter(sos)
#impulse_response = np.exp(-np.linspace(0., 20., 1*samplerate))
#osc.add_reverb(impulse_response)
#impulse_response = np.zeros(4*samplerate)
#impulse_response[::int(samplerate/4)] = 1
#impulse_response *= np.exp(-np.linspace(0.,10.,impulse_response.size))
#osc.add_reverb(impulse_response)
s.add_oscillator(osc)

osc = oscillator(shape='whitenoise', amp=0.03, attack=1.5, decay=0.0, sustain=1.0, release=3)
sos = signal.butter(2, 2*2*fs, 'lowpass', fs=samplerate, output='sos')
osc.add_filter(sos)
s.add_oscillator(osc)


data = s.play_notes(fs, t_tot)
data += s.play_notes(fs*2**(4/12), t_tot)
data += s.play_notes(fs*2**(7/12), t_tot)


data *= np.iinfo(np.int16).max / np.max(np.abs(data))
wavfile.write("example.wav", samplerate, data.astype(np.int16))
playsound('example.wav')

sys.exit()


samplerate=44100
fs = 261.63
t_tot = 2.0
s = synth()

osc = oscillator(shape='swtooth', attack=0.05, decay=0.3, sustain=0.0, voices=3, detune=0.01)
sos = signal.butter(2, fs, 'lowpass', fs=samplerate, output='sos')
osc.add_filter(sos)
impulse_response = np.zeros(samplerate)
impulse_response[::int(1*samplerate/8)] = 1
impulse_response *= np.exp(-np.linspace(0.,10.,impulse_response.size))
osc.add_reverb(impulse_response)
s.add_oscillator(osc)

data = s.play_notes(fs, t_tot)
data *= np.iinfo(np.int16).max / np.max(np.abs(data))
wavfile.write("example.wav", samplerate, data.astype(np.int16))
playsound('example.wav')

