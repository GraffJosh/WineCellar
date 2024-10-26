import json, requests


class BarcodeScanner:
    def __init__(
        self, pixelWidth=1280, pixelHeight=720, scanArea=0.75, timeout=15, video=False
    ) -> None:
        pass
        # self.camera = imageCapture.ImageCapture(
        #     pixelWidth=pixelWidth, pixelHeight=pixelHeight, video=False
        # )
        # self.scanner = zbar.Scanner()
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
