import logging

from fr0stlib import Flame
from eegsources import *
from fr0st.scripts.mindmurmer.sound_controller import AudioController

# For running the script as stand alone and not through the fractal app
if 'flame' not in locals() and 'flame' not in globals():
	print "generating random flame"
	flame = Flame()
	flame.add_xform()


if 'large_preview' not in locals() and 'preview' not in globals():
	def DoNothing():
		pass

	large_preview = DoNothing
	preview = DoNothing


class MMEngine:
	def __init__(self, eeg_source, audio_folder):
		self.eeg_source = eeg_source
		self.audio_controller = AudioController(audio_folder)
		self.frame_index = 0
		self.speed = 1
		self.channels = 24
		self.sinelength = 300 # frames

	def start(self):
		play = True
		while play:
			# preview() for animating wireframe window
			# OR large_preview() for animating rendered window
			large_preview()
			preview()

			play = self.render()
			self.frame_index += 1

	def render(self):
		if (flame.xform is None or len(flame.xform) == 0):
			return False
		try:
			# get eeg data as [] from ext. source
			eegdata = self.eeg_source.read_data()

			# FLAME UPDATE (at least 25 frames apart)
			if(eegdata.blink == 1 and self.frame_index > 2500):
				self.NewFlame()
				self.frame_index = 0
				print("BLINK: new flames generated")

				self.audio_controller.switch_track("mode-we're-going-into")

			dataindex = 0
			for x in flame.xform:
				if(x.animate and eegdata is not None):
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
					data *= np.sin(self.frame_index * (np.pi * 2) / self.sinelength)

			return True
		except Exception as ex:
			logging.exception(ex)
			print('error during rendering: ' + str(ex))

			# SHOW preview on Fr0st
			return False

	@staticmethod
	def NewFlame():
		# based on julia lines:
		# Form 1: BASE
		if(len(flame.xform) == 0):
			x1 = flame.add_xform()
		else:
			x1 = flame.xform[0]

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
			x2.weight = 0.5
			x2.color_speed = 0.5
			x2.julian = 0.7 + random.random() * 0.3 # [0.7 : 1]
			x2.animate = 1
			x2.rotate(random.random() * 360)

		# Form 3: LINE
		if(len(flame.xform) > 2):
			x3 = flame.xform[2]
			x3.weight = 0.25
			x3.color_speed = 0.5
			x3.cross = 0.5 + random.random() * 1.5 # [0.5 : 2]
			x3.julian = 0.2 + random.random() * 0.8 # [0.2 : 1]
			x3.animate = 1
			x3.rotate(random.random() * 360)

		# Form 4: FLOWERS
		if(len(flame.xform) > 3):
			x4 = flame.xform[3]
			x4.weight = 0.25
			x4.color_speed = 0.9
			x4.julian = 0.9 + random.random() * 0.1 # [0.9 : 1]
			x4.animate = 1
			x4.rotate(random.random() * 360)

		# Form 5: FINAL
		if(not flame.final is None):
			x5 = flame.final
			x5.color_speed = 0.0
			x5.spherical = 0.1 + random.random() * 0.9 # [0.1 : 1]
			x5.julia = 0.1 + random.random() * 0.4 # [0.1 : 0.5]
			x5.linear = 0.0
			x5.rotate(random.random() * 360)


# RUN
# audio = get_audio_source("fr0st/scripts/mindmurmur/audio/midnightstar_crop.wav")
# eeg = EEGDummy()
# eeg = EEGFromAudio(audio)
# eeg = EEGFromJSONFile('fr0st/scripts/mindmurmer/data/Muse-B1C1_2018-06-11--07-48-41_1528717729867.json') # extra small
eeg = EEGFromJSONFile('fr0st/scripts/mindmurmer/data/Muse-B1C1_2018-06-10--18-35-09_1528670624296.json') # medium

audio_folder = "fr0st/scripts/mindmurmer/audio"

engine = MMEngine(eeg, audio_folder)
engine.start()