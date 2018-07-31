import pika
import json
import uuid



class RabbitController(object):

    def __init__(self, host, port, user, password, virtualhost):

        self.QUEUE_NAME_COLOR = 'MindMurmur.Domain.Messages.ColorControlCommand, MindMurmur.Domain_colorCommand'
        self.QUEUE_NAME_HEART = 'MindMurmur.Domain.Messages.HeartRateCommand, MindMurmur.Domain_heartRateCommand'
        self.EXCHANGE_COLOR = 'MindMurmur.Domain.Messages.ColorControlCommand, MindMurmur.Domain'
        self.EXCHANGE_HEART = 'MindMurmur.Domain.Messages.HeartRateCommand, MindMurmur.Domain'

        self.credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(host, port, virtualhost, self.credentials)
        self.color_props = pika.BasicProperties(type=self.EXCHANGE_COLOR, delivery_mode=2)
        self.heart_props = pika.BasicProperties(type=self.EXCHANGE_HEART, delivery_mode=2)

        return

    def publish_color(self, color):
        try:
            color_com = ColorControlCommand(color.red, color.green, color.blue)
            
            self.open_channel()
            self.active_channel.exchange_declare(exchange=self.EXCHANGE_COLOR, passive=True)
            self.active_channel.basic_publish(exchange=self.EXCHANGE_COLOR,
                                    properties=self.color_props,
                                    routing_key='',
                                    body=color_com.to_json())

            print(" [x] Sent color message %r {0}" % color)
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

            print(" [x] Sent heartbeat message %r {0}" % heartbeat)
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
