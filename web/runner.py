import os
import subprocess
import sys


class Runner():

    def __init__(self):
        self.base_path = os.path.dirname(os.path.realpath(__file__))

    def run(self, name):
        script_name = os.path.join(self.base_path), 'run_' + name + '.ps1'
        if sys.argv[1] == 'test':
            return 0
        return subprocess.call(['start', script_name])
