import argparse

from osc_server import ThreadingOscUDPServer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="0.0.0.0", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=7000, help="The port to listen on")
    args = parser.parse_args()

    server = ThreadingOscUDPServer((args.ip, args.port))
    print("Serving on {}".format(server.server_address))

    server.serve_forever()
