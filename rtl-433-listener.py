import random
import subprocess
import json
import datetime
from threading import Thread
import time
from paho.mqtt import client as mqtt_client
import logging
import sys

# Print to console
root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)
logging.debug("Logging started")

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

def on_disconnect(client, userdata, rc):
    logging.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)

def connect_mqtt():
	broker = 'm24.cloudmqtt.com'
	port = 12337
	client_id = f'python-mqtt-{random.randint(0, 1000)}'
	username = 'iahriamf'
	password = '7f6KRT6vejOz'
	def on_connect(client, userdata, flags, rc):
		if rc == 0:
			print("Connected to MQTT Broker!")
		else:
			print("Failed to connect, return code %d\n", rc)
	# Set Connecting Client ID
	client = mqtt_client.Client(client_id)
	client.username_pw_set(username, password)
	client.on_connect = on_connect
	client.on_disconnect = on_disconnect
	client.connect(broker, port)
	return client

# sending to api
def sendToApi(data):
	logging.info(f"Rang doorbell ID {data['id']} at {data['time']}")
	# result = <send_to_api(parsed_json)> # here your http.post
	# print(result)
	topic = "doorbell/%s" % data["id"]
	msg = json.dumps({
		"time": data["time"],
		"id": data["id"],
	})
	result = client.publish(topic, msg)
	# result: [0, 1]
	status = result[0]
	if status == 0:
		logging.info(f"Sent `{msg}` to topic `{topic}`")
	else:
		logging.error(f"Failed to send message to topic {topic}")
		print(f"Failed to send message to topic {topic}")



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

client = connect_mqtt()

for result in execute(['/usr/local/bin/rtl_433', '-f','868.300M', '-F', 'json', '-Y', 'classic']):
	# Parse the json
	parsed_json = json.loads(result)

	# I'm starting a new thread to avoid data loss. So I can listen to the weather station's output and send it async to the api
	thread = Thread(target = sendToApi, args = (parsed_json,))
	thread.start()
