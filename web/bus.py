import logging

from rabbit_controller import MeditationStateCommand, HeartRateCommand

MAX_MESSAGES = 500  # Number of messages to keep for web UI


class Bus():

    def __init__(self, rabbit):
        self.rabbit = rabbit
        self.heart_rate_messages = []
        self.state_messages = []
        self.heart_rate = None
        self.state = None

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
        self.state_messages.append((timestamp, state))

        # Remove old messages to not run out of memory
        self.state_messages = self.state_messages[-MAX_MESSAGES:]

        self.state = state

    def process_heart_rate_command(self, channel, method, properties, body):
        logging.info(("received heart rate command with body \"{body}\"").format(body=body))

        command = HeartRateCommand.from_string(body)

        heart_rate = command.get_heart_rate()
        timestamp = command.get_timestamp()
        self.heart_rate_messages.append((timestamp, heart_rate))

        # Remove old messages to not run out of memory
        self.heart_rate_messages = self.heart_rate_messages[-MAX_MESSAGES:]

        self.heart_rate = heart_rate

    def get_heart_rate_history(self):
        return self.heart_rate_messages

    def get_state_history(self):
        return self.state_messages

    def get_heart_rate(self):
        return self.heart_rate or 'No Heart Rate Seen On MQ Bus, Has Webserver Just Started?'

    def get_state(self):
        return self.state or 'No Meditation State Seen On MQ Bus, Has Webserver Just Started?'

    def send_heart_rate(self, heart_rate):
        return self.rabbit.publish_heart(heart_rate)

    def send_state(self, state):
        return self.rabbit.publish_state(state)
