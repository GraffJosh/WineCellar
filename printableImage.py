import numpy as np
from pil import image
import math

ESC = 0x1B


class PrintableImage:
    """
    Container for image data ready to be sent to the printer
    The transformation from bitmap data to PrintableImage data is explained at the link below:
    http://nicholas.piasecki.name/blog/2009/12/sending-a-bit-image-to-an-epson-tm-t88iii-receipt-printer-using-c-and-escpos/
    """

    def __init__(self, data, height):
        self.data = data
        self.height = height

    @classmethod
    def from_image(cls, image):
        """
        Create a PrintableImage from a PIL Image
        :param image: a PIL Image
        :return:
        """
        (w, h) = image.size

        # Thermal paper is 512 pixels wide
        if w > 512:
            ratio = 512.0 / w
            h = int(h * ratio)
            image = image.resize((512, h), Image.ANTIALIAS)
        if image.mode != "1":
            image = image.convert("1")

        pixels = np.array(list(image.getdata())).reshape(h, w)

        # Add white pixels so that image fits into bytes
        extra_rows = int(math.ceil(h / 24)) * 24 - h
        extra_pixels = np.ones((extra_rows, w), dtype=bool)
        pixels = np.vstack((pixels, extra_pixels))
        h += extra_rows
        nb_stripes = h / 24
        pixels = pixels.reshape(nb_stripes, 24, w).swapaxes(1, 2).reshape(-1, 8)

        nh = int(w / 256)
        nl = w % 256
        data = []

        pixels = np.invert(np.packbits(pixels))
        stripes = np.split(pixels, nb_stripes)

        for stripe in stripes:
            data.extend([ESC, 42, 33, nl, nh])  # *  # double density mode

            data.extend(stripe)
            data.extend([27, 74, 48])  # ESC  # J

        # account for double density mode
        height = h * 2
        return cls(data, height)

    def append(self, other):
        """
        Append a Printable Image at the end of the current instance.
        :param other: another PrintableImage
        :return: PrintableImage containing data from both self and other
        """
        self.data.extend(other.data)
        self.height = self.height + other.height
        return self
