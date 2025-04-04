import paho.mqtt.client as mqtt
import requests
from io import BytesIO
import time
import numpy as np
import threading
import queue
from PIL import Image, ImageOps
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

    def requestCompletion(self, prompt):
        with self.newPrompt:
            self.promptsQueue.put(prompt)
            self.newPrompt.notify()

    def requestImage(self, image):
        with self.newPrompt:
            self.imageQueue.put(image)
            self.newPrompt.notify()

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        # topic = msg.topic.split("/")
        payload = msg.payload.decode(encoding="utf-8", errors="strict")
        try:
            json_payload = json.loads(payload)
        except:
            json_payload = None
        if self.config.DEBUG_ENABLE:
            print(msg.topic + " " + payload)
        try:
            if self.bot:
                if self.config.BOT_CONTEXT_TOPIC == msg.topic:
                    self.bot.addContext(payload)

                if self.config.BOT_RESET_TOPIC == msg.topic:
                    self.bot.resetConversation()
                if self.config.BOT_COMPLETION_TOPIC == msg.topic:
                    with self.newPrompt:
                        # json_payload = json.loads(payload)
                        if "cut" in json_payload.keys():
                            self.autoCut = bool(json_payload["cut"])
                        if "prompt" in json_payload.keys():
                            self.promptsQueue.put(str(json_payload["prompt"]))
                            self.newPrompt.notify()
                if self.config.MAX_TOKENS_TOPIC == msg.topic:
                    self.bot.setMaxTokens(int(float(payload)))
                if self.config.BOT_STATUS_TOPIC == msg.topic:
                    self.botStatusText = payload
                if self.config.BOT_URL_IMAGE_TOPIC == msg.topic:
                    self.requestImage(self.getWebImage(url=payload))
                if self.config.FORMAT_AND_PRINT_TOPIC == msg.topic:
                    if self.config.DEBUG_ENABLE:
                        print("format and print!\n")
                        print(msg.payload)
                    self.printChunk(inText=payload)
                    # @TODO: this is a jank workaround. Refactor print chunk into chunker and formatter.
                    if len(self.current_line):
                        self.print(self.current_line)
            if self.config.DEVICE_STATUS_TOPIC == msg.topic:
                self.status = payload
            if self.config.DISCOVER_TOPIC == msg.topic:
                if "ip" in json_payload.keys():
                    self.printerIPAddress = json_payload["ip"]
        except TypeError as e:
            # if we get a type error, we probably were expecting json and got string.
            # Don't crash, just wait for the next message.
            pass

    def getStatus(self):
        if self.status not in self.config.STATUS_OPTIONS:
            return "faulted"
        else:
            if self.bot and self.getBotStatus() == "generating":
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
                if not self.imageQueue.empty():
                    self.printImage(self.imageQueue.get())
                    if self.autoCut:
                        self.cut()
                self.newPrompt.wait()
                time.sleep(0.5)

    def getLastSentMessageResult(self):
        return self.lastSentMessageInfo

    def setTextWidth(self, width):
        self.textWidth = width

    # @TODO: this is a jank workaround. Refactor print chunk into chunker and formatter.
    def printChunk(self, inText=""):
        self.current_line += inText
        while ("\n" in self.current_line) or (len(self.current_line) >= self.line_length):
            self.current_line = self.current_line.strip(" ")
            printTo = 0
            while "\n" in self.current_line[: self.line_length]:
                printTo = self.current_line.find("\n")
                if self.config.DEBUG_ENABLE:
                    print(self.current_line[:printTo])
                self.print(self.current_line[:printTo])
                self.current_line = self.current_line[printTo + 1 :]

            if len(self.current_line) >= self.line_length:
                # printTo = self.line_length
                printTo = self.current_line.rfind(" ", 0, self.line_length)
                if printTo == -1:
                    printTo = self.line_length
                if self.config.DEBUG_ENABLE:
                    print(self.current_line[:printTo])
                self.print(self.current_line[:printTo])
                self.current_line = self.current_line[printTo + 1 :]

    def printChars(self, chars):
        payload = {}
        payload["chars"] = chars
        payload["length"] = len(payload["chars"])
        self.client.publish("printer/chars", json.dumps(payload))

    def getWebImage(self, url):
        print("URL: ", '"', url.strip(), '"')
        try:
            response = requests.get(url.strip())
        except Exception as e:
            print("get web image failed for: " + str(e))
            self.printChunk("\n\n Get web image failed for: " + str(e))
            return ""
        img = Image.open(BytesIO(response.content))
        img = img.rotate(180)
        return img

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
            except Exception as e:
                print("connection to ", self.printerIPAddress, " failed for ", e)
                time.sleep(5)
        return False

    def disconnectFromImageServer(self):
        self.socket.close()

    def configurePrinterForImage(self, imageWidth, imageHeight):
        payload = {}
        payload["width"] = imageWidth
        payload["height"] = imageHeight
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
        if imageData:
            image = escposImage.EscposImage(imageData)
            image.auto_rotate()
            image.fit_width(512)
            image.center(512)
            self.configurePrinterForImage(image.width, image.height)
            time.sleep(0.5)
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
        else:
            self.print("\n\n Printing Image Failed! No image data.")

    def print(self, inText):
        text = inText
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
        self.print("")
        self.client.publish(self.config.FEED_TOPIC, str({"length": inLength - 1}))

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
        hosts = self.config.SERVERS  # ["router.local", "192.168.1.1", "localhost"]
        for host in hosts:
            try:
                self.client.connect(host, 1883, 60)
                break
            except:
                continue

    def __init__(
        self,
        daemon=False,
        inRobot=None,
        inConfig="config",
        inKeys="keys",
        inPrintTopic="",
        inConfigTopic="",
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
        self.client.username_pw_set(username=self.keys.USERNAME, password=self.keys.PASSWORD)
        self.connect()
        time.sleep(0.1)
        self.current_line = ""
        self.autoCut = True
        self.promptsQueue = queue.Queue()
        self.imageQueue = queue.Queue()
        self.newPrompt = threading.Condition()
        self.line_length = self.config.PRINTER_CONFIGURATION["line_length"]

        self.printerIPAddress = self.config.DEFAULT_PRINTER_IP_ADDRESS
        self.printerIPPort = self.config.DEFAULT_PRINTER_IP_PORT
        self.configurePrinter(self.config.PRINTER_CONFIGURATION)

        self.bot = None
        if not inRobot:
            pass
            # inRobot = robot.Robot()
        if inRobot:
            self.bot = inRobot  # robot.Robot()
            self.botStatusText = "ready"  # @TODO: this is kinda gross.
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
        if self.bot:
            self.botQueueThread.join()
