import paho.mqtt.client as mqtt
import time
import numpy as np
import textwrap
import threading
import queue
import struct
from PIL import Image
import json
import robot


class MqttPrinter:
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        for topic in self.config.SUBSCRIBE_TOPICS:
            self.client.subscribe(topic)

    def on_disconnect(self, userdata, flags, rc):
        print("MQTT Client disconnected?")
        time.sleep(5)
        self.client.reconnect()

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        # topic = msg.topic.split("/")
        payload = msg.payload.decode(encoding="utf-8", errors="strict")
        print(msg.topic + " " + payload)
        if self.config.COMPLETION_TOPIC == msg.topic:
            with self.newPrompt:
                json_payload = json.loads(payload)
                if "cut" in json_payload.keys():
                    self.autoCut = bool(json_payload["cut"])
                if "prompt" in json_payload.keys():
                    self.promptsQueue.put(str(json_payload["prompt"]))
                    self.newPrompt.notify()

        # if "printText" == msg.topic:
        #     self.print(str(msg.payload))

        if self.config.MAX_TOKENS_TOPIC == msg.topic:
            print(payload)
            self.bot.setMaxTokens(int(float(payload)))
        if self.config.DEVICE_STATUS_TOPIC == msg.topic:
            self.status = payload
        if self.config.BOT_STATUS_TOPIC == msg.topic:
            self.botStatusText = payload

    def botQueue(self) -> None:
        with self.newPrompt:
            while True:
                # self.newPrompt.clear()
                if not self.promptsQueue.empty():
                    self.feed(3)
                    self.bot.respondTo(
                        inText=self.promptsQueue.get(),
                        inPrintFunction=self.printChunk,
                        inStatusFunction=self.botStatus,
                    )
                    if self.autoCut:
                        self.cut()
                self.newPrompt.wait()
                time.sleep(0.5)

    def getLastSentMessageResult(self):
        return self.lastSentMessageInfo

    def setTextWidth(self, width):
        self.textWidth = width

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
        pix = pix.flatten()
        image_bytes = pix.tobytes("C")
        self.client.publish(
            self.config.IMAGE_TOPIC,
            payload=str({"image": image_bytes, "width": width, "height": height}),
        )

    def printChunk(self, inText=""):
        self.current_line += inText
        while ("\n" in self.current_line) or (len(self.current_line) >= self.line_length):
            self.current_line = self.current_line.strip(" ")
            printTo = 0
            if "\n" in self.current_line:
                printTo = self.current_line.find("\n")
                self.print(self.current_line[:printTo])
                self.current_line = self.current_line[printTo + 1 :]
            if len(self.current_line) >= self.line_length:
                # printTo = self.line_length
                printTo = self.current_line.rfind(" ", 0, self.line_length)
                if printTo == -1:
                    printTo = self.line_length
                self.print(self.current_line[:printTo])
                self.current_line = self.current_line[printTo + 1 :]

    def print(self, inText):
        text = inText
        # text = textwrap.fill(
        #     text,
        #     width=self.textWidth,
        #     initial_indent="",
        #     subsequent_indent="",
        #     expand_tabs=False,
        #     replace_whitespace=False,
        #     fix_sentence_endings=True,
        #     break_long_words=True,
        #     drop_whitespace=True,
        #     break_on_hyphens=True,
        #     tabsize=8,
        #     max_lines=None,
        # )
        # self.statusPrinting()
        self.lastSentMessageInfo = self.client.publish(
            self.config.PRINT_TOPIC, str({"text": str(text + "\r\n")})
        )

    def printAndCut(self, inText):
        self.printChunk(inText=inText)
        self.cut()

    def cut(self):
        if len(self.current_line):
            self.print(self.current_line)
            self.current_line = ""
        self.feed(inLength=7)
        self.client.publish(self.config.CUT_TOPIC, str({"cut": "True"}))

    def feed(self, inLength=0):
        self.client.publish(self.config.FEED_TOPIC, str({"length": inLength}))

    def configurePrinter(self, inConfig={}):
        for key, value in inConfig.items():
            self.client.publish(
                self.config.CONFIG_TOPIC, payload=str('{"' + key + '":' + str(value) + "}")
            )

    def botStatus(self, status):
        self.client.publish(self.config.BOT_STATUS_TOPIC, payload=status)

    def connect(self):
        hosts = ["homeassistant.local", "192.168.1.103", "192.168.1.105"]
        for host in hosts:
            try:
                self.client.connect(host, 1883, 60)
                break
            except:
                continue

    def __init__(self, daemon=False, inConfig="config", inPrintTopic="", inConfigTopic="") -> None:
        self.config = __import__(inConfig)
        self.textWidth = 40
        self.lastSentMessageInfo = None
        self.status = "ready"
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
        self.current_line = ""
        self.autoCut = True
        self.promptsQueue = queue.Queue()
        self.newPrompt = threading.Condition()
        self.line_length = self.config.PRINTER_CONFIGURATION["line_length"]

        self.bot = robot.Robot()

        self.configurePrinter(self.config.PRINTER_CONFIGURATION)
        # self.print("Client Online!")
        self.botQueueThread = threading.Thread(target=self.botQueue)
        self.botQueueThread.setDaemon(True)
        self.botQueueThread.start()
        if daemon:
            self.client.loop_forever()
        else:
            self.client.loop_start()

    def __del__(self):
        self.client.loop_stop()
        self.botQueueThread.join()
