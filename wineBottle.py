from datetime import date


class WineBottle:
    def __init__(self, upc="", title="", brand="", price="", image="", link="") -> None:
        self.upc = upc
        self.title = title
        self.brand = brand
        self.price = price
        self.image = image
        self.link = link
        self.data = ""
        self.date = date.today()
        print("init winebottle, title: ", self.title)

    def __init__(self, jsonPackage="") -> None:
        self.data = jsonPackage["items"][0]
        self.upc = self.data["upc"]
        self.title = self.data["title"]
        self.brand = self.data["brand"]
        self.price = self.data["offers"][0]["price"]
        self.image = self.data["images"][0]
        self.link = self.data["offers"][0]["link"]
        self.date = date.today()

    def print(self):
        print("init winebottle, title: ", self.title)

    def getData(self):
        return self.__dict__
