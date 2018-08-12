import argparse
import logging
import socketserver
import sys

from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage

from rabbit_controller import RabbitController

# import RabbitController

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
        if(message.address == '/muse/elements/alpha_absolute'):
            logger.info("ALPHA: " + repr(message.params))
            server.alpha = message.params
        elif(message.address == '/muse/elements/beta_absolute'):
            logger.info("BETA:  " + repr(message.params))
            server.beta = message.params
        elif(message.address == '/muse/elements/gamma_absolute'):
            logger.info("GAMMA: " + repr(message.params))
            server.gamma = message.params
        elif(message.address == '/muse/elements/delta_absolute'):
            logger.info("DELTA: " + repr(message.params))
            server.delta = message.params
        elif(message.address == '/muse/elements/theta_absolute'):
            logger.info("THETA: " + repr(message.params))
            server.theta = message.params

            # ALL 5 values have been received
            # Send them to the RabbitMQ bus.
            server.send_eegdata()



class OscUDPServer(socketserver.UDPServer):
    def __init__(self, server_address):
        super().__init__(server_address, OscUDPHandler)


class ThreadingOscUDPServer(socketserver.ThreadingMixIn, OscUDPServer):

    def __init__(self, *args, **kwargs):
        # init EEG values
        self.alpha = [0.0] * 4
        self.beta =  [0.0] * 4
        self.gamma = [0.0] * 4
        self.delta = [0.0] * 4
        self.theta = [0.0] * 4
        self.blink = [0]
        # init rabbitMQ connection
        self.rabbit = RabbitController('localhost', 5672, 'guest', 'guest', '/')
        super().__init__(*args, **kwargs)
    
    # send values to the bus
    def send_eegdata(self):
        meditation_state = self.raw_meditation_state()
        allvalues = self.alpha + self.beta + self.gamma + self.delta + self.theta \
                  + self.blink + [meditation_state]
        self.rabbit.publish_eegdata(allvalues)
        print("DATA SENT:  " + repr(allvalues))

    # return a value from 0 (low) to 1 (deep meditation)
    # based on the waves data (timeless data)
    def raw_meditation_state(self):
        meditate = 0
        # (coeff = 5) main   values are forehead alpha and forehead theta
        meditate = meditate + (self.alpha[1] * 5) + (self.alpha[2] * 5)
        meditate = meditate + (self.theta[1] * 5) + (self.theta[2] * 5)
        # (coeff = 2) second values are frontal alpha & theta coherence
        meditate = meditate + (1 - abs(self.alpha[1] - self.theta[1])) * 2
        meditate = meditate + (1 - abs(self.alpha[2] - self.theta[2])) * 2
        # (coeff = 1) third  values are headside alpha and headside theta
        meditate = meditate + (self.alpha[0] * 1) + (self.alpha[3] * 1)
        meditate = meditate + (self.theta[0] * 1) + (self.theta[3] * 1)
        
        return meditate / 28 # 5+5+5+5 + 2+2 + 1+1+1+1


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
