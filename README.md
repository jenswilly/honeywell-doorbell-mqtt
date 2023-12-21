# What is this

This is a Python script used to react to the radio signals sent out by Honeywell wireless doorbells and publish a message on an AWS IoT Core-based MQTT broker.

The idea is for a Home Assistant server to subscribe to the MQTT topic and perform actions when the doorbell is rung.

# Credit where credit is due …

This project would be nothing if not for the following:

- [GitHub: kloher/honeywell-wireless-doorbell](https://github.com/klohner/honeywell-wireless-doorbell): Information about the protocol of the doorbellls.
- [GitHub: merbanan/rtl_433](https://github.com/merbanan/rtl_433): The `rtl_433` binary interfacing with the RTL-SDR device.
- [Stackoverflow: answer to rtl_433 on raspberry pi: Send data to api via http post](https://stackoverflow.com/a/69448046/1632704): Code for running rtl_433 in a separate process and get the output as JSON
- [PyPI: paho-mqtt](https://pypi.org/project/paho-mqtt/): MQTT library for Python

# Configuration

All configuration variables should be placed in a file named `config.py` with the following syntax:

```
class Config:
	awshost = "<some ID>.iot.eu-west-1.amazonaws.com"
	awsport = 8883
	certificates = {
		"rootCAPath": "./AmazonRootCA1.pem",
		"deviceCertPath": "./<your thing name>.cert.pem",
		"privateKeyPath": "./<your thing name>.private.key",
	}
	rtl433BinaryPath = "<result from running `which rtl_433` in Terminal>"
```

# AWS MQTT Broker

## Certificates

For the root certificate, use the one named `RSA 2048 bit key: Amazon Root CA 1` from <https://docs.aws.amazon.com/iot/latest/developerguide/server-authentication.html#server-authentication-certs>.

Save it in the same folder as the Python script. It should be named `AmazonRootCA1.pem`.

The device certificates will be named as follows:

- `<thing-name>.cert.pem` for the MQTT client certificate
- `<thing-name>.private.key` for the private key

(The `<thing-name>.public.key` is not used).

## Security policies

This is important! Otherwise the MQTT client wil fail to connect/publish/subscribe.

Go to AWS IoT Core → Manage → Security → Policies and find the policy used by the Thing you're using (it will probably have a name that includes the Thing's name).

Open it and edit the policy.

In order to _connect_ to the MQTT broker, there must be a policy that allows the `iot:Connect` action. By default, only clients with specific IDs are allowed to connect. To allow another client ID to connect, add the following to the policy:

```
{
  "Effect": "Allow",
  "Action": "iot:Connect",
  "Resource": [
      "arn:aws:iot:eu-west-1:643198386594:client/python-mqtt*"
    ]
},
```

Be sure to change the ARN prefix to match the Thing ARN (if the Thing has ARN `arn:aws:iot:eu-west-1:643198386594:thing/my-thing`, use `arn:aws:iot:eu-west-1:643198386594` as prefix).

In your MQTT client, only use the _last part_ as client ID (e.g. `python-mqtt-123` in the above example).

In order to _publish_ anything, a policy must allow that topic to be published to. The following snippet allows publishing to topic `doorbell`:

```
{
  "Effect": "Allow",
  "Action": [
    "iot:Publish",
    "iot:PublishRetain"
  ],
  "Resource": "arn:aws:iot:eu-west-1:643198386594:topic/doorbell"
}
```

Again, be sure to modify the ARN prefix.

It is also possible to create conditional rules. Read more at [AWS Documentation](https://docs.aws.amazon.com/iot/latest/developerguide/iot-policies.html)

# Radio

This script uses the (rtl_433)[https://github.com/merbanan/rtl_433] to receive data from the SDR device.

Data is returned from a separate process as JSON which is then parsed.
