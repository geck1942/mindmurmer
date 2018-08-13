import pika
import json
import uuid
import logging


class RabbitController(object):

    def __init__(self, host, port, user, password, virtualhost):

        self.QUEUE_NAME_COLOR = 'MindMurmur.Domain.Messages.ColorControlCommand, MindMurmur.Domain_colorCommand'
        self.QUEUE_NAME_HEART = 'MindMurmur.Domain.Messages.HeartRateCommand, MindMurmur.Domain_heartRateCommand'
        self.QUEUE_NAME_SOUND = 'MindMurmur.Domain.Messages.SoundCommand, MindMurmur.Domain_SoundCommand'
        self.QUEUE_NAME_STATE = 'MindMurmur.Domain.Messages.MeditationStateCommand, MindMurmur.Domain_meditationStateCommand'
        self.QUEUE_NAME_EEGDATA = 'MindMurmur.Domain.Messages.EEGDataCommand, MindMurmur.Domain_eegdataCommand'
        self.EXCHANGE_STATE = 'MindMurmur.Domain.Messages.MeditationStateCommand, MindMurmur.Domain'
        self.EXCHANGE_COLOR = 'MindMurmur.Domain.Messages.ColorControlCommand, MindMurmur.Domain'
        self.EXCHANGE_HEART = 'MindMurmur.Domain.Messages.HeartRateCommand, MindMurmur.Domain'
        self.EXCHANGE_EEGDATA = 'MindMurmur.Domain.Messages.EEGDataCommand, MindMurmur.Domain'
        self.EXCHANGE_SOUND = 'MindMurmur.Domain.Messages.SoundCommand, MindMurmur.Domain'

        self.credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(host, port, virtualhost, self.credentials)
        self.color_props = pika.BasicProperties(type=self.EXCHANGE_COLOR, delivery_mode=2)
        self.heart_props = pika.BasicProperties(type=self.EXCHANGE_HEART, delivery_mode=2)
        self.state_props = pika.BasicProperties(type=self.EXCHANGE_STATE, delivery_mode=2)
        self.eegdata_props = pika.BasicProperties(type=self.EXCHANGE_EEGDATA, delivery_mode=2)
        self.sound_props = pika.BasicProperties(type=self.EXCHANGE_SOUND, delivery_mode=2)

        return

    def subscribe_eegdata(self, callback):
        try:
            
            self.open_channel()

            self.active_channel.queue_declare(queue=self.EXCHANGE_EEGDATA)
            print("eegdata channel opened: %s" %(self.EXCHANGE_EEGDATA))
            self.active_channel.basic_consume(callback, 
                                    queue=self.EXCHANGE_EEGDATA,
                                    no_ack= True)
            self.active_channel.start_consuming()

            # self.active_channel.start_consuming()
            print("eegdata channel terminated: %s" %(self.EXCHANGE_EEGDATA))
            # print(" [x] Sent color message %r {0}" % color)
        except Exception as e:
            print(repr(e))
            # do not raise exception. Channel probably not ready
            # raise e
        finally:
            if self.open_connection:
                self.open_connection.close()

    def publish_color(self, color):
        try:
            color_com = ColorControlCommand(color.red, color.green, color.blue)
            
            self.open_channel()
            self.active_channel.exchange_declare(exchange=self.EXCHANGE_COLOR, passive=True)
            self.active_channel.basic_publish(exchange=self.EXCHANGE_COLOR,
                                    properties=self.color_props,
                                    routing_key='',
                                    body=color_com.to_json())

            # print(" [x] Sent color message %r {0}" % color)
        except Exception as e:
            print(repr(e))
            raise e
        finally:
            if self.open_connection:
                self.open_connection.close()

    def publish_heart(self, heartbeat):
        try:
            heart_com = HeartRateCommand(heartbeat)

            self.open_channel()
            self.active_channel.exchange_declare(exchange=self.EXCHANGE_HEART, passive=True)
            self.active_channel.basic_publish(exchange=self.EXCHANGE_HEART,
                                    properties=self.color_props,
                                    routing_key='',
                                    body=heart_com.to_json())

            # print(" [x] Sent heartbeat message %r {0}" % heartbeat)
        except Exception as e:
            print(repr(e))
            raise e
        finally:
            if self.open_connection:
                self.open_connection.close()


    def publish_state(self, meditation_state):
        try:
            state_com = MeditationStateCommand(meditation_state)

            self.open_channel()
            self.active_channel.exchange_declare(exchange=self.EXCHANGE_STATE, passive=True)
            self.active_channel.basic_publish(exchange=self.EXCHANGE_STATE,
                                    properties=self.state_props,
                                    routing_key='',
                                    body=state_com.to_json())

            # print(" [x] Sent meditation_state message %r {0}" % meditation_state)
        except Exception as e:
            print(repr(e))
            raise e
        finally:
            if self.open_connection:
                self.open_connection.close()

    def publish_eegdata(self, eegdata_values):
        try:
            eegdata_com = EEGDataCommand(eegdata_values)

            self.open_channel()
            self.active_channel.queue_declare(queue=self.EXCHANGE_EEGDATA)
            self.active_channel.basic_publish(exchange='',
                                    properties=self.eegdata_props,
                                    routing_key=self.EXCHANGE_EEGDATA,
                                    body=eegdata_com.to_json())

        except Exception as e:
            print(repr(e))
            raise e
        finally:
            if self.open_connection:
                self.open_connection.close()

    def publish_sound(self, desired_stage):
        try:
            sound_command = SoundCommand(desired_stage)

            self.open_channel()
            self.active_channel.queue_declare(queue=self.QUEUE_NAME_SOUND)
            self.active_channel.basic_publish(exchange='',
                                              properties=self.sound_props,
                                              routing_key=self.QUEUE_NAME_SOUND,
                                              body=sound_command.to_json())

            logging.info("sent sound message {desired_stage}".format(desired_stage=desired_stage))
        except Exception as e:
            print(repr(e))
            raise e
        finally:
            if self.open_connection:
                self.open_connection.close()

    def consume_sound(self, callback):
        try:
            self.open_channel()
            self.active_channel.queue_declare(queue=self.QUEUE_NAME_SOUND)
            self.active_channel.basic_consume(callback, queue=self.QUEUE_NAME_SOUND, no_ack=True)

            logging.info("waiting for sound messages..")
            self.active_channel.start_consuming()
        except Exception as e:
            print(repr(e))

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


class HeartRateCommand(object):
    """An instance of a heart rate command

    Attributes:
        CommandId:  Unique id of the command
        HeartRate:  Current Heart rate
    """

    def __init__(self, heart_rate):
        self.CommandId = str(uuid.uuid4())
        self.HeartRate = heart_rate

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,sort_keys=True, indent=4)

    def to_string(self):
        return "({0}, {1})".format(self.CommandId, self.HeartRate)

class MeditationStateCommand(object):
    """An instance of a meditation state command

    Attributes:
        CommandId:  Unique id of the command
        State:  Current meditation state
    """

    def __init__(self, meditation_state):
        self.CommandId = str(uuid.uuid4())
        self.State = meditation_state

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,sort_keys=True, indent=4)

    def to_string(self):
        return "({0}, {1})".format(self.CommandId, self.State)

class EEGDataCommand(object):
    """An instance of a eeg data command

    Attributes:
        CommandId:  Unique id of the command
        Values:  raw values
    """

    def __init__(self, eegdata_values):
        self.CommandId = str(uuid.uuid4())
        self.Values = eegdata_values

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
