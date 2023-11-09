import json, requests
from datetime import date as datettimedate


def name():
    return "Web"


def search(upc):
    url = "https://api.upcitemdb.com/prod/trial/lookup?upc=%s" % (upc)
    response = requests.get(url)
    response.raise_for_status()  # check for errors

    # Load JSON data into a Python variable.
    jsonData = json.loads(response.text)
    try:
        data = jsonData["items"][0]
    except IndexError:
        print("data incorrect? ")
        print("JSONRAW: ", jsonData)

    data = {
        "upc": data["upc"],
        "title": data["title"],
        "brand": data["brand"],
        "price": data["offers"][0]["price"],
        "image": data["images"][0],
        "link": data["offers"][0]["link"],
        "date": datettimedate.today(),
        "data": data,
        "new": True,
    }
    return data
