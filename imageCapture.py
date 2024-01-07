import time
import io
from picamera2 import Picamera2, Preview
from PIL import Image
from frame_server import FrameServer


class ImageCapture:
    def __init__(self, pixelWidth=800, pixelHeight=600, video=False) -> None:
        self.stream = io.BytesIO()
        self.video = video
        self.cameraControls = {}
        self.frameHeight = pixelHeight
        self.frameWidth = pixelWidth

        self.picam2 = Picamera2()
        if self.video:
            config = self.picam2.create_preview_configuration(
                main={"size": (self.frameWidth, self.frameHeight)},
                lores={"size": (self.frameWidth, self.frameHeight)},
                display="lores",
            )
            self.picam2.video_configuration.controls.FrameDurationLimits = (10000, 10000)
        else:
            config = self.picam2.create_still_configuration(
                main={"size": (self.frameWidth, self.frameHeight)},
                lores={"size": (self.frameWidth, self.frameHeight)},
                display="lores",
            )
            self.picam2.set_controls({"AeExposureMode": config.controls.AeExposureModeEnum.Short})
        self.picam2.configure(config)

        # self.setCameraBrightness(1)
        # self.setCameraContrast(3)

        self.picam2.start()

        if self.video:
            self.frame_server = FrameServer(self.picam2)
            self.frame_server.start()
        # self.captureImage()

    def setCameraBrightness(self, brightness):
        self.picam2.controls.Brightness = brightness
        # self.cameraControls["Brightness"] = brightness
        # self.setControls()

    def setCameraContrast(self, contrast):
        self.picam2.controls.Contrast = contrast
        # self.cameraControls["Contrast"] = contrast
        # self.setControls()

    def setFrameSize(self, height=None, width=None):
        if not height:
            height = self.frameHeight
        if not width:
            width = self.frameWidth

        self.frameHeight = height
        self.frameWidth = width

        if self.video:
            self.picam2.video_configuration.size = (self.frameWidth, self.frameHeight)
            self.picam2.configure("video")
        else:
            self.picam2.still_configuration.size = (self.frameWidth, self.frameHeight)
            self.picam2.configure("still")

    def captureImage(self):
        success = self.picam2.autofocus_cycle()
        if self.video:
            buffer = self.frame_server.wait_for_frame()
            self.last_image = self.picam2.helpers.make_image(
                buffer, self.picam2.camera_configuration()["main"]
            )
        else:
            request = self.picam2.capture_request()
            self.last_image = request.make_image("main")  # image from the "main" stream
            metadata = request.get_metadata()
            request.release()  # requests must always be returned to libcamera

    def getLastImage(self):
        return self.last_image

    def getLastImageBW(self):
        return self.last_image.convert("L")

    def getNewImage(self):
        self.captureImage()
        return self.getLastImage()

    def saveImage(self, filename="debug_image.jpg", image=""):
        if image == "":
            self.last_image.save(filename)
        else:
            image.save(filename)

    def __del__(self):
        try:
            self.frame_server.stop()
        except AttributeError:
            pass
        self.picam2.close()
