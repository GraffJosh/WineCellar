from datetime import date


class WineBottle:
    def __init__(self, inDict={}, upc="", title="", brand="", price="", image="", link="", inReview="", new=None) -> None:
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
        if inDict:
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
            # "data": str(self.data),
        }
