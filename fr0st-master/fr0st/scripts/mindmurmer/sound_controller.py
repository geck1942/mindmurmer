import os
import logging
import numpy as np
from threading import Thread

import swmixer
import time
import argparse

from collections import defaultdict
from aubio import source, sink, pvoc, cvec, tempo, unwrap2pi, float_type
from numpy import median, diff


class AudioUtility(object):
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


class MindMurmurSoundScapeController(object):
	""" Non-blocking Audio controller to mix tracks and play sound scapes and heartbeats
	according to input meditation stage

	NOTE: Currently supporting only tracks with sample rate of 16,000 hz
	"""
	SAMPLE_RATE = 16000

	FADEIN_MAX_AFTER_SIX_SECONDS_RATE = SAMPLE_RATE * 12
	FADEOUT_MAX_AFTER_SIX_SECONDS_RATE = SAMPLE_RATE * 12

	TRACKS_KEY = "tracks"
	HEARTBEAT_KEY = "heartbeat"
	HEARTBEAT_SOUND_FILENAME = "heartbeat"
	STAGE_NAME_SPLITTER = "::"


	def __init__(self, audio_folder, up_transition_sound_filename, down_transition_sound_filename, sample_rate=16000):
		"""
		:param audio_folder: audio folder with sub folders, each numbers after a meditation state (e.g, 0, 1, 2, 3, ..).
							 Each folder represents a meditation stage and should contain any tracks
							 for that stage
		:param up_transition_sound_filename
		:param down_transition_sound_filename
		:param sample_rate: the sample rate for the sounds, defaults to 16 Khz
		"""
		self.SAMPLE_RATE = sample_rate
		self.audio_folder = audio_folder
		self.up_transition_sound_filename = up_transition_sound_filename
		self.down_transition_sound_filename = down_transition_sound_filename
		self.playing_tracks = []
		self.playing_heartbeats = []
		self.playing_transitions = []
		self.tracks_by_stage = defaultdict(list)
		self.performing_a_mix = False
		self.mixing_thread = None

		swmixer.init(samplerate=self.SAMPLE_RATE, chunksize=1024, stereo=True)
		swmixer.start()

		self.current_playing_track_filename = None
		self.tracks_last_playing_position = dict()

		self._validate_audio_files_and_prep_data()

	def stop_all_sounds(self):
		for track in self.playing_tracks + self.playing_heartbeats + self.playing_transitions:
			if not track.done:
				track.stop()

	def _validate_audio_files_and_prep_data(self):
		""" Validates "audio_folder" structure to be of subfolders named after mediation stage and have at least one
		track in them

		"""
		if not os.path.isfile(self.up_transition_sound_filename):
			raise ValueError("{up_transition_sound_filename} is not a file".format(
				up_transition_sound_filename=self.up_transition_sound_filename))

		if not os.path.isfile(self.down_transition_sound_filename):
			raise ValueError("{down_transition_sound_filename} is not a file".format(
				down_transition_sound_filename=self.down_transition_sound_filename))

		if not os.path.isdir(self.audio_folder):
			raise ValueError("{folder} folder does not exists on system".format(folder=self.audio_folder))

		for dir_name in os.listdir(self.audio_folder):
			full_dir_path = os.path.join(self.audio_folder, dir_name)

			if not os.path.isdir(full_dir_path):
				raise ValueError("{dir_name} is not a folder".format(dir_name=dir_name))

			try:
				stage_number = int(dir_name)
			except:
				raise ValueError("{dir_name} is not a legal name".format(dir_name=dir_name))

			tracks = []
			heartbeat_track = None

			for filename in os.listdir(full_dir_path):
				full_filename = os.path.join(full_dir_path, filename)

				if not os.path.isfile(full_filename):
					raise ValueError("{filename} is not a file".format(filename=filename))
				elif self.HEARTBEAT_SOUND_FILENAME in filename:
					heartbeat_track = full_filename
				else:
					tracks.append(full_filename)

			if len(tracks) == 0:
				raise ValueError(("{dir_name} folder doesn't contain tracks").format(dir_name=dir_name))
			elif heartbeat_track is None:
				raise ValueError("No heartbeat track located for phase {!s}".format(stage_number))
			else:
				logging.info("Got data for stage \"{stage_number}\"".format(stage_number=stage_number))
				self.tracks_by_stage[stage_number] = {
					self.TRACKS_KEY: tracks,
					self.HEARTBEAT_KEY: heartbeat_track
				}

		logging.info("using audio folder: {audio_folder}".format(audio_folder=self.audio_folder))

	def _mix_track(self, track_filename, stage_change_indication_filename, play_from_second=None):
		""" Mix a track with path "track filename" to play. If another track is playing, fade it out, and fade this in.

		Overall, this takes 15 seconds:
		0:00 - 0:06: playing track fades out
		0:04 - 0:13: transition sounds plays
		0:09 - 0:15: next track mixes in

		:param track_filename: track filename to fade in
		:param stage_change_direction: int, used for transition change indication sound
		:param play_from_second: the time in the track to jump to (just for testing purposes, shouldn't be used otherwise)
		"""
		logging.info("starting mixing")
		start_time_seconds = time.time()

		if len(self.playing_tracks) > 0:
			logging.info("fading out current track to end in {seconds} seconds".format(
				seconds=self.FADEOUT_MAX_AFTER_SIX_SECONDS_RATE / self.SAMPLE_RATE / 2.0))
			track_current_position = (self.playing_tracks[-1].get_position() + self.FADEOUT_MAX_AFTER_SIX_SECONDS_RATE)
			self.tracks_last_playing_position[self.current_playing_track_filename] = track_current_position

			self.playing_tracks[-1].set_volume(0, fadetime=self.FADEOUT_MAX_AFTER_SIX_SECONDS_RATE)

			time.sleep(4 - (time.time() - start_time_seconds))

			# play transition indication
			logging.info("playing transition")
			transition_indication_sound = swmixer.Sound(stage_change_indication_filename)
			transition_channel = transition_indication_sound.play()
			self.playing_transitions.append(transition_channel)

			time.sleep(9 - (time.time() - start_time_seconds))

		# mix in sound scape for stage
		track_sound = swmixer.Sound(track_filename)
		offset = 0

		if play_from_second is not None:
			offset = self.SAMPLE_RATE * play_from_second

		self.current_playing_track_filename = track_filename

		track_last_position = self.tracks_last_playing_position.get(track_filename, None)
		track_channel = track_sound.play(fadein=self.FADEIN_MAX_AFTER_SIX_SECONDS_RATE,
										 offset=track_last_position or offset, loops=100)
		self.playing_tracks.append(track_channel)

		logging.info("starting playing \"{track}\" from {seconds} seconds in".format(
			track=track_filename.split("/")[-1], seconds=(track_last_position or offset) / self.SAMPLE_RATE / 2.0))

		self.performing_a_mix = False

	def _play_heartbeat(self, heartbeat_track):
		""" Play "heartbeat_track"

		:param heartbeat_track: the filename on system to play
		"""
		heartbeat_sound = swmixer.Sound(heartbeat_track)
		heartbeat_channel = heartbeat_sound.play(volume=1.1)
		self.playing_heartbeats.append(heartbeat_channel)
		logging.info("starting playing heartbeat \"{heartbeat_track}\"".format(
			heartbeat_track=heartbeat_track.split("/")[-1]))

	def _get_meditation_stage_soundscape_track_for_stage(self, stage):
		return self.tracks_by_stage[stage][self.TRACKS_KEY][0]

	def _get_meditation_stage_heartbeat_track_for_stage(self, stage):
		return self.tracks_by_stage[stage][self.HEARTBEAT_KEY]

	def set_meditation_stage(self, from_stage, to_stage, play_from_second=None):
		"""

		:param from_stage: int, the stage we in
		:param to_stage: int, the stage we're going to
		:param play_from_second: the time in the track to jump to (just for testing purposes, shouldn't be used otherwise)
		:return:
		"""
		stage_change_direction = to_stage - from_stage

		if stage_change_direction == 0:
			logging.info("stage is the same as requested, ignoring")
		else:
			if not self.performing_a_mix:
				try:
					self.performing_a_mix = True

					stage_track = self._get_meditation_stage_soundscape_track_for_stage(to_stage)
					transition_track = (self.up_transition_sound_filename if stage_change_direction > 0 else
										self.down_transition_sound_filename)

					self.mixing_thread = Thread(target=self._mix_track, args=[stage_track, transition_track,
																			  play_from_second])
					self.mixing_thread.start()
				except Exception:
					self.performing_a_mix = False
			else:
				logging.info("already in stage transition, ignoring")


	def play_heartbeat_for_stage(self, stage):
		stage_heartbeat = self._get_meditation_stage_heartbeat_track_for_stage(stage)
		self._play_heartbeat(stage_heartbeat)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='MindMurmur SoundScape Controller.')
	parser.add_argument('--audio_folder', dest='audio_folder', help="The folder with the tracks")
	parser.add_argument('--up_transition_sound_filename', dest='up_transition_sound_filename',
						help="filename for up_transition_sound_filename")
	parser.add_argument('--down_transition_sound_filename', dest='down_transition_sound_filename',
						help="filename for down_transition_sound_filename")
	parser.add_argument('--create_multi_tempo_versions', dest='create_multi_tempo_versions', action='store_true',
						default=False, help='create multi tempo versions of each track in --audio_folder')
	parser.add_argument('--sample_rate', dest='sample_rate', help="The sample rate for audio files", default=16000)

	log_format = ('%(asctime)s %(filename)s %(lineno)s %(process)d %(levelname)s: %(message)s')
	log_level = logging.INFO
	logging.basicConfig(format=log_format, level=log_level)

	args = parser.parse_args()

	if args.create_multi_tempo_versions:
		for bpm in range(10, 185, 5):
			scale = bpm / 60.0
			output_filename = "{filename}_{bpm}.{file_suffix}".format(
				bpm=bpm, filename=args.sound_filename.split(".")[0], file_suffix=args.sound_filename.split(".")[-1])
			logging.info("rendering sound with bpm: {!s}".format(bpm))
			AudioUtility.alter_track_tempo(args.sound_filename, output_filename, scale)
	else:
		try:
			mmhac = MindMurmurSoundScapeController(args.audio_folder, args.up_transition_sound_filename,
												   args.down_transition_sound_filename, args.sample_rate)

			logging.info("requesting to set mode to 0")
			mmhac.set_meditation_stage(-1, 0)
			logging.info("requested to set mode to 0")

			logging.info("setting mode to 1, stage should still be in transition so this should be ignored")
			mmhac.set_meditation_stage(0, 1)

			for i in range(4):
				time.sleep(2)
				mmhac.play_heartbeat_for_stage(0)

			logging.info("requesting to set mode to 0, nothing should change")
			mmhac.set_meditation_stage(0, 0)
			logging.info("requested to set mode to 0")

			logging.info("requesting to set mode to 1")
			mmhac.set_meditation_stage(0, 1)
			logging.info("requested to set mode to 1")
			time.sleep(20)

			for i in range(4):
				time.sleep(2)
				mmhac.play_heartbeat_for_stage(1)

			logging.info("requesting to set mode to 0")
			mmhac.set_meditation_stage(1, 0)
			logging.info("requested to set mode to 0")
			time.sleep(20)

			for i in range(4):
				time.sleep(2)
				mmhac.play_heartbeat_for_stage(0)


			for i in range(1, 6):
				logging.info("requesting to set mode to {!s}".format(i))
				mmhac.set_meditation_stage(i - 1, i)
				logging.info("requested to set mode to {!s}".format(i))
				time.sleep(20)

				for m in range(4):
					time.sleep(2)
					mmhac.play_heartbeat_for_stage(i)

				logging.info("requesting to set mode to {!s}".format(i - 1))
				mmhac.set_meditation_stage(i, i - 1)
				logging.info("requested to set mode to {!s}".format(i - 1))
				time.sleep(20)

				for j in range(4):
					time.sleep(2)
					mmhac.play_heartbeat_for_stage(i - 1)

			mmhac.stop_all_sounds()
		except Exception, e:
			logging.exception(e)
