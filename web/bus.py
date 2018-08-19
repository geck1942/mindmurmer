import datetime
import logging
import sys

from rabbit_controller import MeditationStateCommand, HeartRateCommand

MAX_MESSAGES = 500  # Number of messages to keep for web UI


epoch = datetime.datetime.utcfromtimestamp(0)

def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0

def pretty_message(m, now):
    return [unix_time_millis(m[0]), str(m[1])]

class Bus():

    def __init__(self, rabbit):
        self.rabbit = rabbit
        self.heart_rate_messages = []
        self.state_messages = []
        self.heart_rate = None
        self.state = None

        if sys.argv[1] != 'test':
            channel = self.rabbit.open_channel()
            self.bus.subscribe_meditation(self.process_meditation_state_command, existing_channel=channel)
            self.bus.subscribe_heart_rate(self.process_heart_rate_command, existing_channel=channel)
            logging.info("web: waiting for meditation state and heart rates messages..")
            channel.start_consuming()

    def process_meditation_state_command(self, channel, method, properties, body):
        logging.info(("received meditation command with body \"{body}\"").format(body=body))

        command = MeditationStateCommand.from_string(body)

        state = command.get_state()
        timestamp = command.get_timestamp()
        self.state_messages.insert(0, (timestamp, state))

        # Remove old messages to not run out of memory
        self.state_messages = self.state_messages[-MAX_MESSAGES:]

        self.state = state

    def process_heart_rate_command(self, channel, method, properties, body):
        logging.info(("received heart rate command with body \"{body}\"").format(body=body))

        command = HeartRateCommand.from_string(body)

        heart_rate = command.get_heart_rate()
        timestamp = command.get_timestamp()
        self.heart_rate_messages.insert(0, (timestamp, heart_rate))

        # Remove old messages to not run out of memory
        self.heart_rate_messages = self.heart_rate_messages[-MAX_MESSAGES:]

        self.heart_rate = heart_rate

    def get_heart_rate_history(self):
        now = datetime.datetime.now()
        return [pretty_message(m, now) for m in self.heart_rate_messages]

    def get_state_history(self):
        now = datetime.datetime.now()
        return [pretty_message(m, now) for m in self.state_messages]

    def get_heart_rate(self):
        return self.heart_rate or 'No Heart Rate Seen On MQ Bus, Has Webserver Just Started?'

    def get_state(self):
        return self.state or 'No Meditation State Seen On MQ Bus, Has Webserver Just Started?'

    def send_heart_rate(self, heart_rate):
        if sys.argv[1] == 'test':
            self.heart_rate = heart_rate
            self.heart_rate_messages.insert(0, (datetime.datetime.now(), heart_rate))
        else:
            self.rabbit.publish_heart(heart_rate)

    def send_state(self, state):
        if sys.argv[1] == 'test':
            self.state = state
            self.state_messages.insert(0, (datetime.datetime.now(), state))
        else:
            self.rabbit.publish_state(state)
