import random
import paho.mqtt.client as paho
import os
import socket
import ssl
from time import sleep
from random import uniform
import json
from config import Config

import logging

# Refactored original source - https://github.com/mariocannistra/python-paho-mqtt-for-aws-iot

class PubSub(object):
	def __init__(self, listener = False, topic = "default"):
		self.connect = False
		self.listener = listener
		self.topic = topic
		self.logger = logging.getLogger()

	def __on_connect(self, client, userdata, flags, rc):
		self.connect = True
		self.logger.info("Connected")
		if self.listener:
			self.mqttc.subscribe(self.topic)

		self.logger.debug("{0}".format(rc))

	def __on_message(self, client, userdata, msg):
		self.logger.info("{0}, {1} - {2}".format(userdata, msg.topic, msg.payload))

	def __on_log(self, client, userdata, level, buf):
		self.logger.debug("{0}, {1}, {2}, {3}".format(client, userdata, level, buf))

	def bootstrap_mqtt(self):
		client_id = f'python-mqtt-{random.randint(0, 1000)}'
		self.mqttc = paho.Client(client_id, clean_session=True, userdata=None, protocol=paho.MQTTv311, transport="tcp")
		
		self.mqttc.on_connect = self.__on_connect
		self.mqttc.on_message = self.__on_message
		self.mqttc.on_log = self.__on_log

		awshost = Config.awshost
		awsport = Config.awsport

		caPath = Config.certificates["rootCAPath"]
		certPath = Config.certificates["deviceCertPath"]
		keyPath = Config.certificates["privateKeyPath"]

		self.mqttc.tls_set(caPath, 
			certfile=certPath, 
			keyfile=keyPath, 
			cert_reqs=ssl.CERT_REQUIRED, 
			tls_version=ssl.PROTOCOL_TLSv1_2, 
			ciphers=None)

		result_of_connection = self.mqttc.connect(awshost, awsport, keepalive=120)

		if result_of_connection == 0:
			self.connect = True

		return self

	def start(self):
		self.mqttc.loop_start()

	def send(self, topic, message):
		if self.connect == True:
			self.mqttc.publish(topic, json.dumps(message), qos=1)
		else:
			self.logger.error("Not connected to broker")