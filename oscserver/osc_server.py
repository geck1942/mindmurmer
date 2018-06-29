import socketserver
import time

from osc_bundle import OscBundle
from osc_message import OscMessage


class OscUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        dgram = self.request[0]
        message = OscBundle(dgram).content(0) \
            if OscBundle.dgram_is_bundle(dgram) \
            else OscMessage(dgram)
        print(int(round(time.time() * 1000)) / 1000.0,
              message.address,
              message.params)


class OscUDPServer(socketserver.UDPServer):
    def __init__(self, server_address):
        super().__init__(server_address, OscUDPHandler)


class ThreadingOscUDPServer(socketserver.ThreadingMixIn, OscUDPServer):
    pass
