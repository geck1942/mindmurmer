import argparse
import logging
import socketserver
import sys

from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage


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


class OscUDPServer(socketserver.UDPServer):
    def __init__(self, server_address):
        super().__init__(server_address, OscUDPHandler)


class ThreadingOscUDPServer(socketserver.ThreadingMixIn, OscUDPServer):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="0.0.0.0", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=7000, help="The port to listen on")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s')

    server = ThreadingOscUDPServer((args.ip, args.port))
    print("Serving on {}".format(server.server_address))

    server.serve_forever()
