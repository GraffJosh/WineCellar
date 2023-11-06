import io
import time
import json, requests
import imageCapture
from PIL import Image, ImageDraw, ImageFont
import zbar

from pyzbar.pyzbar import decode


class BarcodeScanner:
    def __init__(
        self, pixelWidth=1280, pixelHeight=720, scanArea=0.75, timeout=15, video=False
    ) -> None:
        pass
        self.camera = imageCapture.ImageCapture(
            pixelWidth=pixelWidth, pixelHeight=pixelHeight, video=False
        )
        self.scanner = zbar.Scanner()
        self.timeout = timeout
        self.pixelWidth = pixelWidth
        self.pixelHeight = pixelHeight
        self.scanArea = scanArea

    def lookupUPC(self, upc):
        url = "https://api.upcitemdb.com/prod/trial/lookup?upc=%s" % (upc)
        response = requests.get(url)
        response.raise_for_status()  # check for errors

        # Load JSON data into a Python variable.
        jsonData = json.loads(response.text)
        return jsonData

    def getCode(self):
        decoded_barcodes = []
        return_barcodes = []
        i = 0

        while len(decoded_barcodes) < 1 and i < self.timeout:  # len(decoded_barcodes) < 1:
            i += 1
            last_image = self.camera.getNewImage()
            crop_dist = (1 - self.scanArea) / 2
            area = (
                self.pixelWidth * crop_dist,
                self.pixelHeight * crop_dist,
                (self.pixelWidth - (self.pixelWidth * crop_dist)),
                (self.pixelHeight - (self.pixelHeight * crop_dist)),
            )
            last_image = last_image.crop(area)
            decoded_barcodes = decode(last_image)
            if len(decoded_barcodes) > 0:
                # print(type(decoded_barcodes[0]))
                for code in decoded_barcodes:
                    if code.type == "EAN13":
                        return_barcodes.append(code.data.decode())

        if i >= self.timeout:
            self.camera.saveImage(filename="debug_image.jpg", image=last_image)
        return return_barcodes

    # camera.saveImage("testimage.jpg")


# font = ImageFont.truetype(
#     font="/usr/share/fonts/truetype/freefont/FreeSans.ttf", size=20
# )  # Set 'arial.ttf' for Windows
# draw = ImageDraw.Draw(im=last_image)
# for d in decode(last_image):
#     draw.rectangle(
#         ((d.rect.left, d.rect.top), (d.rect.left + d.rect.width, d.rect.top + d.rect.height))
#     )
#     draw.polygon(
#         d.polygon,
#     )

#     draw.multiline_text((d.rect.left, d.rect.top + d.rect.height), d.data.decode(), fill=None)
#     # draw.text((d.rect.left, d.rect.top + d.rect.height), d.data.decode(), (255, 0, 0), font=font)

# last_image.save("barcode_qrcode_pillow.jpg")
