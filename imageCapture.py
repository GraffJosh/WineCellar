import time
import io
from picamera2 import Picamera2, Preview
from PIL import Image
from frame_server import FrameServer


class ImageCapture:
    def __init__(self, pixelWidth=640, pixelHeight=480, video=False) -> None:
        time.sleep(1)
        self.stream = io.BytesIO()
        self.video = video
        self.cameraControls = {}
        if video:
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(
                main={"size": (pixelWidth, pixelHeight)},
                lores={"size": (pixelWidth, pixelHeight)},
                display="lores",
            )
            self.picam2.video_configuration.controls.FrameDurationLimits = (10000, 10000)
            self.picam2.configure(config)
        else:
            self.picam2 = Picamera2()
            capture_config = self.picam2.create_still_configuration(
                main={"size": (pixelWidth, pixelHeight)},
                lores={"size": (pixelWidth, pixelHeight)},
                display="lores",
            )
            self.setCameraBrightness(1.25)
            self.setCameraContrast(4)
            self.picam2.configure(capture_config)

        self.picam2.start()
        time.sleep(2)

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

    # def setControls(self):
    #     self.set_controls(self.cameraControls)

    def captureImage(self):
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
