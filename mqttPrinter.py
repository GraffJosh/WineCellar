import paho.mqtt.client as mqtt
import time


class mqttPrinter:
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # self.client.subscribe("/homeassistant/current/bedroom_speaker_volume")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        topic = msg.topic.split("/")
        print(msg.topic + " " + str(msg.payload))

    def printText(self, inText):
        self.client.publish(self.printTopic, inText)

    def configurePrinter(self, inConfig={}):
        self.config = inConfig
        for topic, value in inConfig:
            self.client.publish(self.configTopic + topic, value)

    def for_canonical(self, f):
        return lambda k: f(l.canonical(k))

    def __init__(
        self, inConfig="config.py", inPrintTopic="printer/printText", inConfigTopic="printer/config"
    ) -> None:
        self.printTopic = inPrintTopic
        self.configTopic = inConfigTopic
        self.config = __import__(inConfig)

        self.configurePrinter(inConfig.printerConfiguration)
        while True:
            self.client = mqtt.Client()
            self.client.max_inflight_messages_set(1)
            self.client.max_queued_messages_set(1)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.username_pw_set(
                username=self.config.mqtt_username, password=self.config.mqtt_password
            )
            try:
                self.client.connect("homeassistant.local", 1883, 60)
            except:
                try:
                    self.client.connect("192.168.1.103", 1883, 60)
                except:
                    self.client.connect("192.168.1.105", 1883, 60)

            time.sleep(0.1)
            self.printText("Client Online!")
            self.client.loop_forever()
