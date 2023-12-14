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
import escposImage
import socket


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i : i + n]


class MqttPrinter:
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        for topic in self.config.SUBSCRIBE_TOPICS:
            self.client.subscribe(topic)
        self.status = "ready"

    def on_disconnect(self, userdata, flags, rc):
        print("MQTT Client disconnected? Reason: ", str(rc))
        self.status = "faulted"
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
        if self.config.DISCOVER_TOPIC == msg.topic:
            self.printerDiscover = json.loads(payload)
            if "ip" in self.printerDiscover.keys():
                self.printerIPAddress = self.printerDiscover["ip"]
        if self.config.BOT_STATUS_TOPIC == msg.topic:
            self.botStatusText = payload

    def getStatus(self):
        if self.status not in self.config.STATUS_OPTIONS:
            return "faulted"
        else:
            if self.getBotStatus() == "generating":
                self.status = "generating"
            return self.status

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

    # def printImage(self, filename):
    #     image = Image.open(filename)
    #     image.convert(mode="L", dither=3)
    #     pix = np.array(image)
    #     pix = np.delete(pix, 0, 2)
    #     pix = np.delete(pix, 0, 2)
    #     pix = np.delete(pix, 0, 2)

    #     # pix = pix.reshape(600, 600)
    #     width = pix.shape[0]
    #     height = pix.shape[1]
    #     pix = pix.flatten()
    #     image_bytes = pix.tobytes("C")
    #     self.client.publish(
    #         self.config.IMAGE_TOPIC,
    #         payload=str({"image": image_bytes, "width": width, "height": height}),
    #     )

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

    def printChars(self, chars):
        payload = {}
        payload["chars"] = chars
        payload["length"] = len(payload["chars"])
        self.client.publish("printer/chars", json.dumps(payload))

    def printImage(self):
        imageWidth = 512
        highDensity = True
        if highDensity:
            densityConfig = 33
            densityMultiplier = 3
        else:
            densityConfig = 0
            densityMultiplier = 1
        nL = imageWidth & 0x00FF
        nH = (imageWidth & 0xFF00) >> 8
        imageWidth = imageWidth * densityMultiplier
        print("expected number of bytes: ", (nH << 8 | nL), hex(nH), hex(nL))
        # self.print("\n")
        self.printChars([27, 85, 255])  # unidirectional printing
        self.printChars([27, 51, 1])  # set line spacing?
        self.printChars([27, 42, densityConfig, nL, nH])  # image header
        # self.printChars([27, 51, 16])
        line = []
        value = 0xFF
        for pixel in range(imageWidth):
            line.append(value)
            if value > 0:
                value = value - 1
            else:
                value = 0xFF
        total_len = 0
        for chunk in divide_chunks(line, 128):
            total_len += len(chunk)
            print(total_len)
            self.printChars(chars=chunk)  # send data
            # time.sleep(1)

        print("printLine")
        time.sleep(0.5)
        self.printChars([13, 10])
        self.printChars([27, 85, 0])  # unidirectional printing
        self.printChars([27, 51, 20])  # set line spacing?
        # self.printChars([27, 50])
        # self.printChars([27, 100, 7])
        # self.printChars([27, 50])  # reset line spacing?

    def socketImage(self, line):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        imageWidth = 512
        highDensity = True
        if highDensity:
            densityConfig = 33
            densityMultiplier = 3
        else:
            densityConfig = 0
            densityMultiplier = 1

        imageWidth = imageWidth * densityMultiplier
        line = []
        value = 0xFF
        for pixel in range(imageWidth):
            line.append(value)
            if value > 0:
                value = value - 1
            else:
                value = 0xFF

        payload = {}
        payload["listen"] = "true"
        self.client.publish("printer/tcp/async", json.dumps(payload))
        payload = {}
        payload["width"] = 512
        payload["density"] = "true"
        self.client.publish("printer/image", json.dumps(payload))
        time.sleep(2)
        s.connect((self.printerIPAddress, self.printerIPPort))
        for i in range(10):
            print("sending: ", len(bytes(line)), " bytes")
            s.sendall(bytes(line))
            time.sleep(0)

    def sendImageBytesToServer(self, data):
        self.socket.sendall(data)

    def connectToImageServer(self):
        attempts = 0
        while attempts < self.config.RETRIES_MAX:
            attempts += 1
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.printerIPAddress, self.printerIPPort))
                return True
            except BaseException as e:
                print("connection to ", self.printerIPAddress, " failed for ", e)
                time.sleep(5)
        return False

    def disconnectFromImageServer(self):
        self.socket.close()

    def configurePrinterForImage(self):
        payload = {}
        payload["width"] = 512
        payload["density"] = "true"
        payload["status"] = 1
        self.client.publish("printer/image", json.dumps(payload))

    def printImageComplete(self):
        print("printImageComplete")
        payload = {}
        payload["status"] = 0
        self.client.publish("printer/image", json.dumps(payload))
        self.disconnectFromImageServer()

    def printImage(self, imageData):
        image = escposImage.EscposImage(imageData)
        image.auto_rotate()
        image.fit_width(512)
        image.center(512)
        self.configurePrinterForImage()
        time.sleep(1)
        if self.connectToImageServer():
            i = 0
            for line in image.to_column_format(True):
                i = i + 1
                self.sendImageBytesToServer(line)
            time.sleep(i / 6)
            self.printImageComplete()
            return True
        else:
            self.print("\n\n Printing Image Failed! Probably couldn't get the IP Address? Idk.")
            return False

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

    def getBotStatus(self):
        return self.botStatusText

    def connect(self):
        hosts = ["homeassistant.local", "192.168.1.103", "192.168.1.105", "localhost"]
        for host in hosts:
            try:
                self.client.connect(host, 1883, 60)
                break
            except:
                continue

    def __init__(
        self, daemon=False, inConfig="config", inKeys="keys", inPrintTopic="", inConfigTopic=""
    ) -> None:
        self.config = __import__(inConfig)
        self.keys = __import__(inKeys)
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
            username=self.keys.mqtt_username, password=self.keys.mqtt_password
        )
        self.connect()
        time.sleep(0.1)
        self.current_line = ""
        self.autoCut = True
        self.promptsQueue = queue.Queue()
        self.newPrompt = threading.Condition()
        self.line_length = self.config.PRINTER_CONFIGURATION["line_length"]

        self.printerIPAddress = self.config.DEFAULT_PRINTER_IP_ADDRESS
        self.printerIPPort = self.config.DEFAULT_PRINTER_IP_PORT
        self.configurePrinter(self.config.PRINTER_CONFIGURATION)

        self.bot = robot.Robot()
        # self.print("Client Online!")
        self.botQueueThread = threading.Thread(target=self.botQueue)
        self.botQueueThread.setDaemon(True)
        self.botQueueThread.start()
        if daemon:
            self.client.loop_forever()
        else:
            self.client.loop_start()

    def __del__(self):
        if self.client:
            self.client.loop_stop()
        self.botQueueThread.join()
