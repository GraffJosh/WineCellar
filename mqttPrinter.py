import paho.mqtt.client as mqtt
import time
import numpy as np
import textwrap
from PIL import Image


class MqttPrinter:
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # self.client.subscribe("/homeassistant/current/bedroom_speaker_volume")

    def on_disconnect(self, userdata, flags, rc):
        print("MQTT Client disconnected?")
        self.connect()

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        topic = msg.topic.split("/")
        print(msg.topic + " " + str(msg.payload))

    def getLastSentMessageResult(self):
        return self.lastSentMessageInfo

    def setTextWidth(self, width):
        self.textWidth = width

    def print(self, inText):
        text = textwrap.fill(
            inText,
            width=self.textWidth,
            initial_indent="",
            subsequent_indent="",
            expand_tabs=True,
            replace_whitespace=True,
            fix_sentence_endings=True,
            break_long_words=True,
            drop_whitespace=True,
            break_on_hyphens=True,
            tabsize=8,
            max_lines=None,
        )
        self.lastSentMessageInfo = self.client.publish(
            self.config.PRINT_TOPIC, str({"text": str(text + "\r\n")})
        )

    def printAndCut(self, inText):
        self.print(inText=inText)
        self.feed(inLength=7)
        self.cut()

    def printImage(self, filename):
        image = Image.open(filename)
        image.convert(mode="L", dither=3)
        pix = np.array(image)
        pix = np.delete(pix, 0, 2)
        pix = np.delete(pix, 0, 2)
        pix = np.delete(pix, 0, 2)

        # pix = pix.reshape(600, 600)
        width = pix.shape[0]
        height = pix.shape[1]
        print(pix.shape)
        pix = pix.flatten()
        # pix = pix[0]
        print(pix)

        self.client.publish(
            self.config.IMAGE_TOPIC,
            payload=str({"image": list(pix), "width": width, "height": height}),
        )

    def cut(self):
        self.client.publish(self.config.CUT_TOPIC, str({"cut": "True"}))

    def feed(self, inLength=0):
        self.client.publish(self.config.FEED_TOPIC, str({"length": inLength}))

    def configurePrinter(self, inConfig={}):
        for key, value in inConfig.items():
            self.client.publish(
                self.config.CONFIG_TOPIC, payload=str('{"' + key + '":' + str(value) + "}")
            )

    def for_canonical(self, f):
        return lambda k: f(l.canonical(k))

    def connect(self):
        hosts = ["homeassistant.local", "192.168.1.103", "192.168.1.105"]
        for host in hosts:
            try:
                self.client.connect(host, 1883, 60)
                break
            except:
                continue

    def __init__(self, inConfig="config", inPrintTopic="", inConfigTopic="") -> None:
        self.config = __import__(inConfig)
        self.textWidth = 42
        self.lastSentMessageInfo = None
        self.client = mqtt.Client()
        self.client.max_inflight_messages_set(1)
        self.client.max_queued_messages_set(1)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.username_pw_set(
            username=self.config.mqtt_username, password=self.config.mqtt_password
        )
        self.connect()
        time.sleep(0.1)

        self.configurePrinter(self.config.PRINTER_CONFIGURATION)
        # self.print("Client Online!")

        # self.client.loop_forever()
