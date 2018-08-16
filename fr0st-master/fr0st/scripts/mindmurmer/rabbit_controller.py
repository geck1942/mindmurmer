import pika
import json
import uuid
import logging


class RabbitController(object):

    def __init__(self, host, port, user, password, virtualhost):

        self.QUEUE_NAME_COLOR = 'MindMurmur.Domain.Messages.ColorControlCommand, MindMurmur.Domain_colorCommand'
        self.QUEUE_NAME_HEART = 'MindMurmur.Domain.Messages.HeartRateCommand, MindMurmur.Domain_heartRateCommand'
        self.QUEUE_NAME_STATE = 'MindMurmur.Domain.Messages.MeditationStateCommand, MindMurmur.Domain_meditationStateCommand'
        self.QUEUE_NAME_EEGDATA = 'MindMurmur.Domain.Messages.EEGDataCommand, MindMurmur.Domain_eegdataCommand'
        self.EXCHANGE_STATE = 'MindMurmur.Domain.Messages.MeditationStateCommand, MindMurmur.Domain'
        self.EXCHANGE_COLOR = 'MindMurmur.Domain.Messages.ColorControlCommand, MindMurmur.Domain'
        self.EXCHANGE_HEART = 'MindMurmur.Domain.Messages.HeartRateCommand, MindMurmur.Domain'
        self.EXCHANGE_EEGDATA = 'MindMurmur.Domain.Messages.EEGDataCommand, MindMurmur.Domain'

        self.credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(host, port, virtualhost, self.credentials)
        self.color_props = pika.BasicProperties(type=self.EXCHANGE_COLOR, delivery_mode=2)
        self.heart_props = pika.BasicProperties(type=self.EXCHANGE_HEART, delivery_mode=2)
        self.state_props = pika.BasicProperties(type=self.EXCHANGE_STATE, delivery_mode=2)
        self.eegdata_props = pika.BasicProperties(type=self.EXCHANGE_EEGDATA, delivery_mode=2)

        return

    def _base_subscribe(self, consume_target_str, queue_name, callback):
        try:
            new_channel = self.open_channel()
            new_channel.queue_declare(queue=queue_name)
            new_channel.basic_consume(callback, queue=queue_name, no_ack=True)
            new_channel.start_consuming()

            logging.info("waiting for {consume_target_str} state messages..".format(
                consume_target_str=consume_target_str))
        except Exception as e:
            print(repr(e))

            if self.open_connection:
                self.open_connection.close()

    def _base_publish(self, queue_name, properties, command):
        try:
            self.open_channel()
            self.active_channel.queue_declare(queue=queue_name, passive=True)
            self.active_channel.basic_publish(exchange='',
                                              properties=properties,
                                              routing_key=queue_name,
                                              body=command.to_json())
        except Exception as e:
            print(repr(e))
            raise e
        finally:
            if self.open_connection:
                self.open_connection.close()

    def open_channel(self):
        try:

            self.open_connection = pika.BlockingConnection(self.parameters)
            self.active_channel = self.open_connection.channel()
            # self.on_channel_open(self.active_channel)

            return self.active_channel

        except Exception as ex:
            print('error during rabbitMQ channel creation: ' + str(ex))
            return None

    def subscribe_meditation(self, callback):
        self._base_subscribe("meditation state", self.EXCHANGE_STATE, callback)

    def subscribe_heart_rate(self, callback):
        self._base_subscribe("heart rate", self.EXCHANGE_HEART, callback)

    def subscribe_eegdata(self, callback):
        self._base_subscribe("EEG data", self.EXCHANGE_EEGDATA, callback)

    def publish_color(self, color):
        color_command = ColorControlCommand(color.red, color.green, color.blue)
        self._base_publish(self.EXCHANGE_COLOR, self.color_props, color_command)

        logging.info("sent color message (Red: {red}, Blue: {blue}, Green: {green})".format(
            red=color.red, green=color.green, blue=color.blue))

    def publish_heart(self, heartbeat):
        heart_command = HeartRateCommand(heartbeat)
        self._base_publish(self.EXCHANGE_HEART, self.heart_props, heart_command)

        logging.info("sent heart rate message {heartbeat}".format(heartbeat=heartbeat))

    def publish_state(self, meditation_state):
        state_command = MeditationStateCommand(meditation_state)
        self._base_publish(self.EXCHANGE_STATE, self.state_props, state_command)

        logging.info("sent meditation state message {meditation_state}".format(
            meditation_state=meditation_state))

    def publish_eegdata(self, eegdata_values):
        eegdata_command = EEGDataCommand(eegdata_values)
        self._base_publish(self.EXCHANGE_EEGDATA, self.eegdata_props, eegdata_command)

        logging.info("sent eegdata message {eegdata_values}".format(eegdata_values=eegdata_values))


class ColorControlCommand(object):
    """An instance of a color control command

    Attributes:
        CommandId:   Unique id of the command
        ColorRed: Red value of RGB
        ColorGreen: Green value of RGB
        ColorBlue: Blue value of RGB
    """

    def __init__(self, color_red, color_green, color_blue):
        self.CommandId = str(uuid.uuid4())
        self.ColorRed = color_red
        self.ColorGreen = color_green
        self.ColorBlue = color_blue

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,sort_keys=True, indent=4)

    def to_string(self):
        return "({0}, {1}, {2}, {3})".format(self.CommandId, self.ColorRed, self.ColorGreen, self.ColorBlue)


class BaseCommand(object):
    """

    """
    def __init__(self):
        self.CommandId = str(uuid.uuid4())

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,sort_keys=True, indent=4)

class HeartRateCommand(BaseCommand):
    """An instance of a heart rate command

    Attributes:
        CommandId:  Unique id of the command
        HeartRate:  Current Heart rate
    """

    def __init__(self, heart_rate):
        super(HeartRateCommand, self).__init__()
        self.HeartRate = heart_rate

    @staticmethod
    def from_string(command_string):
        return HeartRateCommand(json.loads(command_string)["HeartRate"])

    def to_string(self):
        return "({0}, {1})".format(self.CommandId, self.HeartRate)

    def get_heart_rate(self):
        return self.HeartRate

class MeditationStateCommand(BaseCommand):
    """An instance of a meditation state command

    Attributes:
        CommandId:  Unique id of the command
        State:  Current meditation state
    """

    def __init__(self, meditation_state):
        super(MeditationStateCommand, self).__init__()
        self.State = meditation_state

    @staticmethod
    def from_string(command_string):
        return MeditationStateCommand(json.loads(command_string)["State"])

    def get_state(self):
        return self.State

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,sort_keys=True, indent=4)

    def to_string(self):
        return "({0}, {1})".format(self.CommandId, self.State)

class EEGDataCommand(BaseCommand):
    """An instance of a eeg data command

    Attributes:
        CommandId:  Unique id of the command
        Values:  raw values
    """

    def __init__(self, eegdata_values):
        super(EEGDataCommand, self).__init__()
        self.Values = eegdata_values

    def get_values(self):
        return self.Values

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,sort_keys=True, indent=4)

    def to_string(self):
        return "({0}, {1})".format(self.CommandId, self.Values)

class SoundCommand(object):
    """An instance of a sound command

    Attributes:
        CommandId:  Unique id of the command
        DesiredStage: stage to transition sound to
    """

    def __init__(self, desired_stage):
        self.CommandId = str(uuid.uuid4())
        self.DesiredStage = desired_stage

    @staticmethod
    def from_string(command_string):
        return SoundCommand(json.loads(command_string)["DesiredStage"])

    def get_desired_stage(self):
        return self.DesiredStage

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,sort_keys=True, indent=4)

    def to_string(self):
        return "({0}, {1})".format(self.CommandId, self.DesiredStage)
