import os
import logging
import swmixer
import time
import argparse

from threading import Thread
from collections import defaultdict
from rabbit_controller import RabbitController, MeditationStateCommand, HeartRateCommand


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


	def __init__(self, audio_folder, up_transition_sound_filename, down_transition_sound_filename,
				 sample_rate=16000, bus_host="localhost", bus_port=5672, bus_username='guest',
				 bus_password='guest', bus_virtualhost='/'):
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
		self.bus = RabbitController(bus_host, bus_port, bus_username, bus_password, bus_virtualhost)
		self.current_stage = None

		swmixer.init(samplerate=self.SAMPLE_RATE, chunksize=1024, stereo=True)
		swmixer.start()

		self.current_playing_track_filename = None
		self.tracks_last_playing_position = dict()

		self._validate_audio_files_and_prep_data()

		sound_controller_channel = self.bus.open_channel()
		self.bus.subscribe_meditation(self.process_meditation_state_command, existing_channel=sound_controller_channel)
		self.bus.subscribe_heart_rate(self.process_heart_rate_command, existing_channel=sound_controller_channel)
		logging.info("waiting for meditation state and heart rates messages..")
		sound_controller_channel.start_consuming()

	def process_meditation_state_command(self, channel, method, properties, body):
		logging.info(("received meditation command with body \"{body}\"").format(body=body))

		command = MeditationStateCommand.from_string(body)

		desired_stage = command.get_state()
		logging.info("parsing request to transition to stage \"{desired_stage}\"".format(
			desired_stage=desired_stage))

		if desired_stage ==  self.current_stage:
			logging.info("requested stage is already playing, ignoring")
		else:
			stage_track = self._get_meditation_stage_soundscape_track_for_stage(desired_stage)
			stage_change_direction = desired_stage - (self.current_stage or 0)

			transition_track = (self.up_transition_sound_filename if stage_change_direction > 0 else
								self.down_transition_sound_filename)

			self._mix_track(stage_track, transition_track)
			self.current_stage = desired_stage

	def process_heart_rate_command(self, channel, method, properties, body):
		logging.info(("received heart rate command with body \"{body}\"").format(body=body))

		command = HeartRateCommand.from_string(body)

		logging.info("parsing request to play heartbeat for current stage ({current_stage})".format(
			current_stage=self.current_stage))
		self.play_heartbeat_for_stage()

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


	def play_heartbeat_for_stage(self):
		stage_heartbeat = self._get_meditation_stage_heartbeat_track_for_stage(self.current_stage or 0)
		self._play_heartbeat(stage_heartbeat)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='MindMurmur SoundScape Controller.')
	parser.add_argument('--audio_folder', dest='audio_folder', help="The folder with the tracks")
	parser.add_argument('--up_transition_sound_filename', dest='up_transition_sound_filename',
						help="filename for up_transition_sound_filename")
	parser.add_argument('--down_transition_sound_filename', dest='down_transition_sound_filename',
						help="filename for down_transition_sound_filename")
	parser.add_argument('--sample_rate', dest='sample_rate', help="The sample rate for audio files", default=16000)

	log_format = ('%(asctime)s %(filename)s %(lineno)s %(process)d %(levelname)s: %(message)s')
	log_level = logging.INFO
	logging.basicConfig(format=log_format, level=log_level)

	args = parser.parse_args()

	try:
		mmhac = MindMurmurSoundScapeController(args.audio_folder, args.up_transition_sound_filename,
											   args.down_transition_sound_filename, args.sample_rate)
	except Exception, e:
		logging.exception(e)
