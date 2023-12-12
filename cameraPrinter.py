import imageCapture
import mqttPrinter
from gpiozero import Button


class cameraPrinter:
    def __init__(self, pixelWidth=512, pixelHeight=800, video=False) -> None:
        self.printer = mqttPrinter.MqttPrinter()
        self.camera = imageCapture.ImageCapture(pixelWidth=pixelWidth, pixelHeight=pixelHeight)
        self.shutter = Button(2)

    def captureAndPrint(self):
        self.printer.printImage(self.camera.getNewImage())
