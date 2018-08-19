import os
import subprocess


class Runner():

    def __init__(self):
        self.base_path = os.path.dirname(os.path.realpath(__file__))

    def run(self, name):
        script_name = os.path.join(self.base_path), 'run_' + name + '.ps1'
        return subprocess.call(['start', script_name])
