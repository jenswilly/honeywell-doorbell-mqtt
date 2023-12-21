import random
import subprocess
import json
import datetime
from threading import Thread
import time
import logging
import sys
from pubsub_iot import PubSub
from config import Config

# Print to console
root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)
logging.debug("Logging started")

# Start the MQTT client
client = PubSub(listener = False, topic = "doorbell")
client.bootstrap_mqtt()
client.start()

# sending to api
def sendToApi(data):
	logging.info(f"Rang doorbell ID {data['id']} at {data['time']}")
	# result = <send_to_api(parsed_json)> # here your http.post
	# print(result)
	topic = "doorbell"
	msg = {
		"time": data["time"],
		"id": data["id"],
	}
	client.send(topic, message=msg)

# This method creates a subprocess with subprocess.Popen and takes a List<str> as command
def execute(cmd):
	popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True)
	logging.debug(f"Started process {popen.args}. Listening")

	for stdout_line in iter(popen.stdout.readline, ""):
		yield stdout_line 
	popen.stdout.close()
	return_code = popen.wait()
	if return_code:
		raise subprocess.CalledProcessError(return_code, cmd)

for result in execute([Config.rtl433BinaryPath, '-f','868.300M', '-F', 'json', '-Y', 'classic']):
	# Parse the json
	parsed_json = json.loads(result)

	# I'm starting a new thread to avoid data loss. So I can listen to the weather station's output and send it async to the api
	thread = Thread(target = sendToApi, args = (parsed_json,))
	thread.start()
