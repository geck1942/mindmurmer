import sys


class API():

    def __init__(self, bus, runner):
        self.bus = bus
        self.runner = runner

    def run(self, name):
        exitcode = self.runner.run(name)
        if exitcode == 0:
            return True, 'Script ' + name + ' run! Exit code: ' + str(exitcode)
        else:
            return False, 'Script ' + name + ' failed! Exit code: ' + str(exitcode)

    def send_state(self, name):
        try:
            result = self.bus.send_state(name)
            return True, 'Meditation Level ' + name + ' set! Result: ' + repr(result)
        except:
            return False, 'Meditation Level ' + name + ' could not be set: ' + sys.exc_info()[:2]

    def send_heart_rate(self, name):
        try:
            result = self.bus.send_heart_rate(name)
            return True, 'Heartrate ' + name + ' set! Result: ' + repr(result)
        except:
            return False, 'Heartrate ' + name + ' could not be set: ' + sys.exc_info()[:2]
