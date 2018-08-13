import logging
import time

from rabbit_controller import RabbitController

log_format = ('%(asctime)s %(filename)s %(lineno)s %(process)d %(levelname)s: %(message)s')
log_level = logging.INFO
logging.basicConfig(format=log_format, level=log_level)

bus = RabbitController('localhost', 5672, 'guest', 'guest', '/')

def set_to_stage(stage):
	bus.publish_sound(stage)

def play_heartbet():
	bus.publish_sound(-1)

logging.info("requesting to set mode to 0")
set_to_stage(0)
logging.info("requested to set mode to 0")

for i in range(4):
	time.sleep(2)
	play_heartbet()

logging.info("requesting to set mode to 0, nothing should change")
set_to_stage(0)
logging.info("requested to set mode to 0")

logging.info("requesting to set mode to 1")
set_to_stage(1)
logging.info("requested to set mode to 1")
time.sleep(20)

for i in range(4):
	time.sleep(2)
	play_heartbet()

logging.info("requesting to set mode to 0")
set_to_stage(0)
logging.info("requested to set mode to 0")
time.sleep(20)

for i in range(4):
	time.sleep(2)
	play_heartbet()

for i in range(1, 6):
	logging.info("requesting to set mode to {!s}".format(i))
	set_to_stage(i)
	logging.info("requested to set mode to {!s}".format(i))
	time.sleep(20)

	for m in range(4):
		time.sleep(2)
		play_heartbet()

	logging.info("requesting to set mode to {!s}".format(i - 1))
	set_to_stage(i - 1)
	logging.info("requested to set mode to {!s}".format(i - 1))
	time.sleep(20)

	for j in range(4):
		time.sleep(2)
		play_heartbet()

connection.close()