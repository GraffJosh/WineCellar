from datetime import date


class WineBottle:
    def __init__(
        self, upc="", title="", brand="", price="", image="", link="", inReview=None, new=None
    ) -> None:
        self.upc = upc
        self.title = title
        self.brand = brand
        self.price = price
        self.image = image
        self.link = link
        self.review = inReview
        self.data = ""
        self.new = new
        self.date = date.today()
        print("init winebottle, title: ", self.title)

    # def __init__(self, inJsonPackage="", new=None) -> None:
    #     self.data = inJsonPackage["items"][0]
    #     self.upc = self.data["upc"]
    #     self.title = self.data["title"]
    #     self.brand = self.data["brand"]
    #     self.price = self.data["offers"][0]["price"]
    #     self.image = self.data["images"][0]
    #     self.link = self.data["offers"][0]["link"]
    #     self.new = new
    #     self.date = date.today()

    def __init__(self, inDict={}, new=None) -> None:
        try:
            self.upc = inDict["upc"]
            self.new = inDict["new"]
            self.data = inDict["data"]
            self.title = inDict["title"]
            self.brand = inDict["brand"]
            self.price = inDict["price"]
            self.image = inDict["image"]
            self.link = inDict["link"]
            if "review" in list(inDict.keys()):
                self.review = inDict["review"]
            self.date = inDict["date"]
        except KeyError as errortext:
            print("missing key", errortext)

    def print(self):
        print()
        print()
        print("upc: ", self.upc)
        print("title: ", self.title)
        print("brand: ", self.brand)
        print("price: ", self.price)
        print("image: ", self.image)
        print("link: ", self.link)
        print("date: ", self.date)
        print("Review: ", self.review)
        print()
        print()

    def getData(self):
        return {
            "upc": str(self.upc),
            "title": str(self.title),
            "brand": str(self.brand),
            "price": str(self.price),
            "image": str(self.image),
            "link": str(self.link),
            "date": str(self.date),
            "review": str(self.review),
            "data": str(self.data),
        }
