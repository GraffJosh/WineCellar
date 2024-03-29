from gpiozero import Button, LED
import time

PIN_RED_LED = 14
PIN_BLUE_LED = 15
PIN_GREEN_LED = 23
PIN_SWITCH = 24
red_led = LED(PIN_RED_LED)
red_led.on()

DEBUG = True

# these imports are below the LED init above to provide status on startup.
import imageCapture
import mqttPrinter


class CameraPrinter:
    def __init__(self, daemon=True, pixelWidth=512, pixelHeight=512, video=False) -> None:
        self.red_led = red_led
        self.blue_led = LED(PIN_BLUE_LED)
        self.green_led = LED(PIN_GREEN_LED)
        self.green_led.off()
        self.red_led.on()
        self.blue_led.off()

        self.daemon = daemon
        self.printer = mqttPrinter.MqttPrinter()
        self.camera = imageCapture.ImageCapture(pixelWidth=pixelWidth, pixelHeight=pixelHeight)
        self.shutter = Button(PIN_SWITCH, bounce_time=0.1)
        self.status = "ready"
        self.handleLED()

        self.shutter.when_pressed = self.handleShutter
        self.shutter.when_held = self.handleShutterHeld
        if self.daemon:
            self.loop()
        # self.shutter.when_released = led.off

    def captureAndPrint(self):
        self.printer.print("\n")
        image = self.camera.getNewImage()
        self.camera.frameHeight
        self.camera.frameWidth
        if not self.printer.printImage(image):
            self.status = "faulted"
        else:
            self.status = "ready"
        self.printer.cut()

    def printReceipt(self):
        # self.printer.print("\n")
        # if not self.printer.printImage(self.camera.getNewImage()):
        #     self.status = "faulted"
        # else:
        #     self.status = "ready"
        # self.printer.printChunk(
        #     "Thank you for visiting JPG Industries!\r\nCome Again Soon!\r\n------------------------------------------\r\n ORDER C10         AA008763         18:42\r\n------------------------------------------\r\n\r\n\r\nBeverage: unknown              $nan\r\nBeverage: unknown              $nan\r\n            total: $nan\r\n"
        # )
        self.printer.requestCompletion("Tell me what you are")

    # self.printer.cut()

    def setStatus(self, status):
        self.status = status

    def getStatus(self):
        if self.printer:
            printerStatus = self.printer.getStatus()
        if self.status != "ready":
            return self.status
        else:
            return printerStatus

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

    def handleShutterHeld(self) -> None:
        if DEBUG:
            print("Handle Shutter!")
        self.printReceipt()

    def loop(self):
        while self.daemon:
            self.handleLED()
            time.sleep(0.10)

    def __del__(self):
        self.status = "faulted"
        self.handleLED()
