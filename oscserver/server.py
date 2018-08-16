import argparse
import logging
import numpy as np
import socketserver
import sys
import signal

from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage
from collections import deque
from statsmodels.tsa import arima_model
from threading import Thread, Lock, Event

from rabbit_controller import RabbitController

QUEUE_SIZE = 300  # band powers are calculated at 10hz, storing a 30 seconds worth of data in dequeue

EMIT_STAGE_PERIOD_SECONDS = 3 * 60  # evaluating stages every 3 minutes
ARIMA_PARAMS = (4, 0, 1)
LOWER_THRESHOLD = -0.04
UPPER_THRESHOLD = 0.01

logger = logging.getLogger(__name__)


class suppress_stdout:
    def __enter__(self):
        self.stdout = sys.stdout
        sys.stdout = None

    def __exit__(self, type, value, traceback):
        sys.stdout = self.stdout


class OscUDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        dgram = self.request[0]
        with suppress_stdout():
            message = OscBundle(dgram).content(0) \
                if OscBundle.dgram_is_bundle(dgram) \
                else OscMessage(dgram)
        logger.info('{address} {params}'.format(address=message.address, 
                                                params=message.params))
        if message.address == '/muse/elements/alpha_absolute':
            print('got alpha ' + str(message.params))
            self.server.queue.append(np.mean(message.params[1:3]))  # storing mean value of abs_alpha in
            #  channels 2 and 3
        elif message.address == '/muse/elements/blink':
            self.server.increment_blink()
        elif message.address == '/muse/acc':
            pass
            # think how to store accelerometer data, we'll need it to detect if person moved too much


class OscUDPServer(socketserver.UDPServer):
    def __init__(self, server_address):
        super().__init__(server_address, OscUDPHandler)


class ThreadingOscUDPServer(socketserver.ThreadingMixIn, OscUDPServer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, self._signal_handler)
        self.rabbit = RabbitController('localhost', 5672, 'guest', 'guest', '/')
        self.queue = deque(maxlen=QUEUE_SIZE)  # we only use append, therefore no need in queue.Queue
        self.blink_events = 0  # counter of blink events
        self.state = None
        self.lock = Lock()
        self._stop = Event()
        self._timer_thread = None
        self.start_emitting_state_messages()

    def increment_blink(self):
        with self.lock:
            self.blink_events += 1

    def _signal_handler(self, _, unused_frame):
        self._stop.set()

    def start_emitting_state_messages(self):
        self.state = 1
        self.rabbit.publish_state(self.state)
        Thread(target=self.predict_next_level, daemon=True).start()

    def predict_next_level(self):
        while not self._stop.is_set():
            self._stop.wait(EMIT_STAGE_PERIOD_SECONDS)
            data = np.array(self.queue, dtype=np.float64)
            model = arima_model.ARIMA(data, order=ARIMA_PARAMS)
            model = model.fit(disp=0)
            forecast = model.predict(start=1, end=20)
            data_filtered = data[np.where(np.logical_and(np.greater_equal(data, np.percentile(data, 5)),
                                                         np.less_equal(data, np.percentile(data, 95))))]
            mean_diff = np.mean(forecast) - np.mean(data_filtered)
            # add more logic there considering movement and blinks
            if mean_diff > UPPER_THRESHOLD:
                self.state = min(self.state + 1, 5)
            elif mean_diff < LOWER_THRESHOLD:
                self.state = max(self.state - 1, 1)
            self.rabbit.publish_state(self.state)
            with self.lock:
                self.blink_events = 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="0.0.0.0", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=7000, help="The port to listen on")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s %(levelname)-8s %(message)s')

    server = ThreadingOscUDPServer((args.ip, args.port))
    print("Serving on {}".format(server.server_address))

    server.serve_forever()
