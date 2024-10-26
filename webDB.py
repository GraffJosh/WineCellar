import json, requests
from datetime import date as datettimedate


def name():
    return "Web"


def search(upc):
    url = "https://api.upcitemdb.com/prod/trial/lookup?upc=%s" % (upc)
    response = requests.get(url)
    response.raise_for_status()  # check for errors
    results = []
    # Load JSON data into a Python variable.
    jsonData = json.loads(response.text)
    try:
        data = jsonData["items"]
    except IndexError:
        print("data incorrect? ")
        print("JSONRAW: ", jsonData)
    for item in data:
        results.append({
            "upc": item["upc"],
            "title": item["title"],
            "brand": item["brand"],
            "price": item["offers"][0]["price"],
            "image": item["images"][0],
            "link": item["offers"][0]["link"],
            "date": datettimedate.today(),
            "data": item,
            "new": True,
        })
    return results
