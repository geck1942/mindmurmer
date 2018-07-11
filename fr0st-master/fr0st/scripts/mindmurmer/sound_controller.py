import os
import logging
import numpy as np
import swmixer
import time
import argparse

from collections import defaultdict
from aubio import source, sink, pvoc, cvec, tempo, unwrap2pi, float_type
from numpy import median, diff


class MindMurmurHeartbeatAudioController(object):
	""" Non-blocking Audio controller to mix tracks and play heartbeat sounds according to input heartbeat rate

	NOTE: Currently supporting only tracks with sample rate of 16,000 hz
	"""
	# I cannot figure out the scale of these, not seconds.. these values seem right
	FADEOUT_AMOUNT = 10
	FADEIN_AMOUNT = 300
	HEARTBEAT_SOUND_FILENAME = "heartbeat.wav"
	STAGE_NAME_SPLITTER = "::"
	TRACKS_KEY = "tracks"
	HEARTBEAT_SOUND_FILENAME_KEY = "heartbeat_sound_filename"

	def __init__(self, audio_folder, sample_rate=16000):
		"""
		:param audio_folder: audio folder with sub folders, each named by start rate and end rate (e.g, 20_40, 41_60).
							 Each folder represents a meditation stage and should contain any tracks
							 for that stage and a heartbeat.wav file
		:param sample_rate: the sample rate for the sounds
		"""

		self.audio_folder = audio_folder
		self.sample_rate = sample_rate
		self.current_playing_track_filename = None
		self.playing_tracks = []
		self.playing_heartbeats = []
		self.tracks_by_stage = defaultdict(list)

		self._validate_audio_files_and_prep_data()

		swmixer.init(samplerate=sample_rate, chunksize=1024, stereo=True)
		swmixer.start()

	def _validate_audio_files_and_prep_data(self):
		""" Validate "audio_folder" and "heartbeat_filename" are an actual folders

		"""
		if not os.path.isdir(self.audio_folder):
			raise ValueError("{folder} folder does not exists on system".format(folder=self.audio_folder))

		for dir_name in os.listdir(self.audio_folder):
			full_dir_path = os.path.join(self.audio_folder, dir_name)

			if not os.path.isdir(full_dir_path):
				raise ValueError("{dir_name} is not a folder".format(dir_name=dir_name))

			try:
				stage_thresholds = map(int, dir_name.split("_"))
			except:
				raise ValueError("{dir_name} is not a legal name".format(dir_name=dir_name))

			start_rate = min(stage_thresholds)
			end_rate = max(stage_thresholds)
			tracks = []
			heartbeat_sound_filename = None

			for filename in os.listdir(full_dir_path):
				full_filename = os.path.join(full_dir_path, filename)

				if not os.path.isfile(full_filename):
					raise ValueError("{filename} is not a file".format(filename=filename))
				else:
					if filename == self.HEARTBEAT_SOUND_FILENAME:
						heartbeat_sound_filename = full_filename
					else:
						tracks.append(full_filename)

			if heartbeat_sound_filename is None or len(tracks) == 0:
				raise ValueError(("{dir_name} folder doesn't contain {heartbeat_sounds_filename} "
								  "or at least one track").format(
					dir_name=dir_name, heartbeat_sounds_filename=self.HEARTBEAT_SOUND_FILENAME))
			else:
				logging.info("matched stage from rate {start_rate} to {end_rate}".format(start_rate=start_rate,
																						 end_rate=end_rate))
				self.tracks_by_stage[self._get_meditation_stage_key(start_rate, end_rate)] = {
					self.HEARTBEAT_SOUND_FILENAME_KEY: heartbeat_sound_filename,
					self.TRACKS_KEY: tracks
				}

		logging.info("using audio folder: {audio_folder}".format(audio_folder=self.audio_folder))

	def _mix_track(self, track_filename):
		""" Mix a track with path "track filename" to play. If another track is playing, fade it out, and fade this in

		:param track_filename: track filename to fade in
		"""
		track_full_path = os.path.join(self.audio_folder, track_filename)
		if self.current_playing_track_filename == track_full_path:
			logging.info("track playing is the same as requested, ignoring")
		else:
			fadein_time = 0

			if len(self.playing_tracks) > 0:
				logging.info("fading out current track to end in {fadeout} seconds".format(fadeout=self.FADEOUT_AMOUNT))
				self.playing_tracks[-1].set_volume(0, fadetime=self.sample_rate * self.FADEOUT_AMOUNT)
				fadein_time = self.sample_rate * self.FADEIN_AMOUNT
				logging.info("set fade")

			# fade in of one second
			track_sound = swmixer.Sound(track_full_path)
			track_channel = track_sound.play(fadein=fadein_time)
			self.playing_tracks.append(track_channel)
			self.current_playing_track_filename = track_filename
			logging.info("starting playing {track}".format(track=track_filename))

	def _play_heartbeat(self, heartbeat_track):
		""" Play "heartbeat_track"

		:param heartbeat_track: the filename on system to play
		"""
		heartbeat_sound = swmixer.Sound(heartbeat_track)
		heartbeat_channel = heartbeat_sound.play(volume=1.3)
		self.playing_heartbeats.append(heartbeat_channel)
		logging.info("starting playing heartbeat")

	def _get_meditation_stage_key(self, start_rate, end_rate):
		""" Get a stage str key symbolizing the start and end rate of the stage

		:param start_rate: the rate
		:param end_rate:
		:return: str key symbolizing the start and end rate of the stage
		"""
		return "{start_rate}{stage_name_splitter}{end_rate}".format(stage_name_splitter=self.STAGE_NAME_SPLITTER,
																	start_rate=start_rate, end_rate=end_rate)

	def _get_stage_rates_by_key(self, stage_key):
		""" get start and end rate from stage key

		:param stage_key:
		:return: tuple of start and end rate
		"""
		return sorted(map(int, stage_key.split(self.STAGE_NAME_SPLITTER)))

	def _get_meditation_stage_dat_for_rate(self, rate):
		""" get the correct mediation stage data for rate

		:param rate: the rate to get the stage for
		:return: a dict of the meditation stage data with audio tracks
		"""
		sorted_stage_keys = sorted(self.tracks_by_stage.keys())

		for meditation_stage in sorted_stage_keys:
			start_rate, end_rate = self._get_stage_rates_by_key(meditation_stage)

			if start_rate <= rate <= end_rate:
				return self.tracks_by_stage[meditation_stage]

		if rate < self._get_stage_rates_by_key(sorted_stage_keys[0])[0]:
			logging.info("rate lower than lowest stage, returning it")
			return self.tracks_by_stage[sorted_stage_keys[0]]
		if rate > self._get_stage_rates_by_key(sorted_stage_keys[-1])[1]:
			logging.info("rate higher than highest stage, returning it")
			return self.tracks_by_stage[sorted_stage_keys[-1]]

		raise ValueError("Couldn't find any stage!")

	def stop_all_sounds(self):
		for track in self.playing_tracks + self.playing_heartbeats:
			if not track.done:
				track.stop()

	def set_heart_rate(self, rate):
		""" trigger sounds for given "rate"

		:param rate: the rate to trigger sounds for
		"""
		stage_data = self._get_meditation_stage_dat_for_rate(rate)
		# TODO(AmirW): what happens if we have more than one track per stage?
		self._mix_track(stage_data[self.TRACKS_KEY][0])
		self._play_heartbeat(stage_data[self.HEARTBEAT_SOUND_FILENAME_KEY])

	@staticmethod
	def get_track_bmp(path, params=None):
		""" Calculate the beats per minute (bpm) of a given file.
			path: path to the file
			param: dictionary of parameters
		"""
		if params is None:
			params = {}

		# default:
		sample_rate, win_s, hop_s = 16000, 1024, 512

		if 'mode' in params:
			if params.mode in ['super-fast']:
				# super fast
				sample_rate, win_s, hop_s = 4000, 128, 64
			elif params.mode in ['fast']:
				# fast
				sample_rate, win_s, hop_s = 8000, 512, 128
			elif params.mode in ['default']:
				pass
			else:
				print("unknown mode {:s}".format(params.mode))

		# manual settings
		if 'samplerate' in params:
			sample_rate = params.samplerate
		if 'win_s' in params:
			win_s = params.win_s
		if 'hop_s' in params:
			hop_s = params.hop_s

		s = source(path, sample_rate, hop_s)
		sample_rate = s.samplerate
		o = tempo("specdiff", win_s, hop_s, sample_rate)
		# List of beats, in samples
		beats = []
		# Total number of frames read
		total_frames = 0

		while True:
			samples, read = s()
			is_beat = o(samples)
			if is_beat:
				this_beat = o.get_last_s()
				beats.append(this_beat)
			# if o.get_confidence() > .2 and len(beats) > 2.:
			#    break
			total_frames += read
			if read < hop_s:
				break

		def beats_to_bpm(beats, path):
			# if enough beats are found, convert to periods then to bpm
			if len(beats) > 1:
				if len(beats) < 4:
					print("few beats found in {:s}".format(path))
				bpms = 60. / diff(beats)
				return median(bpms)
			else:
				logging.info("not enough beats found in {:s}".format(path))
				return 0

		return beats_to_bpm(beats, path)

	@staticmethod
	def alter_track_tempo(source_filename, output_filename, rate, sample_rate=0):
		win_s = 512
		hop_s = win_s // 8  # 87.5 % overlap

		warm_up = win_s // hop_s - 1
		source_in = source(source_filename, sample_rate, hop_s)
		sample_rate = source_in.samplerate
		p = pvoc(win_s, hop_s)

		sink_out = sink(output_filename, sample_rate)

		# excepted phase advance in each bin
		phi_advance = np.linspace(0, np.pi * hop_s, win_s / 2 + 1).astype(float_type)

		old_grain = cvec(win_s)
		new_grain = cvec(win_s)

		block_read = 0
		interp_read = 0
		interp_block = 0

		while True:
			samples, read = source_in()
			cur_grain = p(samples)

			if block_read == 1:
				phas_acc = old_grain.phas

			# print "block_read", block_read
			while True and (block_read > 0):
				if interp_read >= block_read:
					break
				# print "`--- interp_block:", interp_block,
				# print 'at orig_block', interp_read, '<- from', block_read - 1, block_read,
				# print 'old_grain', old_grain, 'cur_grain', cur_grain
				# time to compute interp grain
				frac = 1. - np.mod(interp_read, 1.0)

				# compute interpolated frame
				new_grain.norm = frac * old_grain.norm + (1. - frac) * cur_grain.norm
				new_grain.phas = phas_acc

				# psola
				samples = p.rdo(new_grain)
				if interp_read > warm_up:  # skip the first frames to warm up phase vocoder
					# write to sink
					sink_out(samples, hop_s)

				# calculate phase advance
				dphas = cur_grain.phas - old_grain.phas - phi_advance
				# unwrap angle to [-pi; pi]
				dphas = unwrap2pi(dphas)
				# cumulate phase, to be used for next frame
				phas_acc += phi_advance + dphas

				# prepare for next interp block
				interp_block += 1
				interp_read = interp_block * rate
				if interp_read >= block_read:
					break

			# copy cur_grain to old_grain
			old_grain.norm = np.copy(cur_grain.norm)
			old_grain.phas = np.copy(cur_grain.phas)

			# until end of file
			if read < hop_s: break
			# increment block counter
			block_read += 1

		for t in range(warm_up + 2):  # purge the last frames from the phase vocoder
			new_grain.norm[:] = 0
			new_grain.phas[:] = 0
			samples = p.rdo(new_grain)
			sink_out(samples, read if t == warm_up + 1 else hop_s)

		# just to make sure
		source_in.close()
		sink_out.close()

		format_out = "read {:d} blocks from {:s} at {:d}Hz and rate {:f}, wrote {:d} blocks to {:s}"
		logging.info(format_out.format(block_read, source_filename, sample_rate, rate,
									   interp_block, output_filename))


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Process some integers.')
	parser.add_argument('--audio_folder', dest='audio_folder', help="The folder with the tracks")
	parser.add_argument('--create_multi_tempo_versions', dest='create_multi_tempo_versions', action='store_true',
						default=False, help='create multi tempo versions of each track in --audio_folder')

	log_format = ('%(asctime)s %(filename)s %(lineno)s %(process)d %(levelname)s: %(message)s')
	log_level = logging.INFO
	logging.basicConfig(format=log_format, level=log_level)

	args = parser.parse_args()

	ac = MindMurmurHeartbeatAudioController(args.audio_folder)

	if args.create_multi_tempo_versions:
		for bpm in range(10, 185, 5):
			scale = bpm / 60.0
			output_filename = "{filename}_{bpm}.{file_suffix}".format(
				bpm=bpm, filename=args.sound_filename.split(".")[0], file_suffix=args.sound_filename.split(".")[-1])
			logging.info("rendering sound with bpm: {!s}".format(bpm))
			MindMurmurHeartbeatAudioController.alter_track_tempo(args.sound_filename, output_filename, scale)
	else:
		logging.info("set HB to 5 BPM, should get the first stage")
		ac.set_heart_rate(5)
		time.sleep(1)

		logging.info("set HB to 900 BPM, should get the last stage")
		ac.set_heart_rate(900)
		time.sleep(1)

		logging.info("stopping all sounds")
		ac.stop_all_sounds()

		for i in range(10):
			logging.info("set HB to 45 BPM")
			ac.set_heart_rate(45)
			time.sleep(1)
			logging.info("done setting HB with 45 BPM")

		for i in range(10):
			logging.info("set HB to 70 BPM")
			ac.set_heart_rate(70)
			time.sleep(1)
			logging.info("done setting HB with 70 BPM")

		time.sleep(10)