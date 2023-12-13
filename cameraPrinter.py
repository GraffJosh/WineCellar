import imageCapture
import mqttPrinter
import time
from gpiozero import Button, LED

PIN_RED_LED = 14
PIN_BLUE_LED = 15
PIN_GREEN_LED = 18
PIN_SWITCH = 23
DEBUG = True


class CameraPrinter:
    def __init__(self, daemon=True, pixelWidth=1000, pixelHeight=512, video=False) -> None:
        self.daemon = daemon
        self.printer = mqttPrinter.MqttPrinter()
        self.camera = imageCapture.ImageCapture(pixelWidth=pixelWidth, pixelHeight=pixelHeight)
        self.shutter = Button(PIN_SWITCH)
        self.red_led = LED(PIN_RED_LED)
        self.blue_led = LED(PIN_BLUE_LED)
        self.green_led = LED(PIN_GREEN_LED)

        self.shutter.when_pressed = self.handleShutter
        # self.shutter.when_released = led.off

    def captureAndPrint(self):
        self.printer.printImage(self.camera.getNewImage())

    def getStatus(self):
        printerStatus = self.printer.getStatus()
        cameraStatus = "ready"
        if printerStatus != "ready":
            return printerStatus
        else:
            return cameraStatus

    def handleLED(self):
        status = self.getStatus()
        if status == "ready":
            self.green_led.on()
            self.red_led.off()
            self.blue_led.off()
        if status == "printing" or status == "generating":
            self.green_led.off()
            self.red_led.off()
            self.blue_led.on()
        if status == "faulted":
            self.green_led.off()
            self.red_led.on()
            self.blue_led.off()

    def handleShutter(self) -> None:
        if DEBUG:
            print("Handle Shutter!")
        self.captureAndPrint()

    def loop(self):
        while self.daemon:
            self.handleLED()
            time.sleep(0.10)
