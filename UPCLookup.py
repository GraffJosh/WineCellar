import wineBottle
import barcodeScanner as barcodeScanner
import wineBottle
import database
import webDB
import reviewer
import config

cellarDB = database.Database(database_name="wine_list", default_table="bottles")
scanner = barcodeScanner.BarcodeScanner(pixelWidth=1280, pixelHeight=720)
sommelier = reviewer.Reviewer(
    inApiKey=config.openAI_apiKey,
    inOrganization=config.openAI_organization,
)
search_providers = [cellarDB, webDB]
configuration_message = {
    "role": "system",
    "content": "You are a relaxed sommelier, who keeps reviews short, sweet, and interesting.",
}

bottles = []
upc_codes = []
while True:
    # reset out newest list of bottles.
    last_bottles = []
    # returns when scanner gets a code.
    last_codes = scanner.getCode(inTimeout=-1)
    print("Last codes: ", last_codes)
    # begin UPC lookup Loop
    if len(last_codes) > 0:
        for code in last_codes:
            code = code.strip("0")
            # if we haven't seen the code in this session, go look it up.
            if code not in upc_codes:
                # We have seen it now.
                upc_codes.append(code)
                # lookup the UPC in the database and then online.
                for provider in search_providers:
                    found_bottles = provider.search(code)
                    print(found_bottles)
                    if found_bottles:
                        print("Bottle found in ", provider.name())
                        break
                    else:
                        print("bottle not found in ", provider.name())

                # searchedBottlesDicts = cellarDB.lookupUPC(inTable="bottles", upc=code)
                # if we got any hits, add them to our list.
                if len(found_bottles) > 0:
                    for bottle in found_bottles:
                        if bottle["upc"] is not None:
                            last_bottles.append(wineBottle.WineBottle(inDict=bottle))
                else:
                    print("Bottle lookup failed!")
                    last_bottles.append(wineBottle.WineBottle(upc=str(code), new=True))
    else:
        print("No barcodes detected")

    # after we saw some bottles, we can look at the bottles we've seen.
    for bottle in last_bottles:
        if bottle.new:
            if bottle.title is not "":
                review_message = {
                    "role": "user",
                    "content": "Please provide tasting notes on: {}".format(bottle.title),
                }
                bottle.review = sommelier.getReview(
                    {bottle.title: [configuration_message, review_message]}
                )
            cellarDB.put(inTable="bottles", inDict=bottle.getData())
            print("A new bottle!: ", bottle.title)
        else:
            print("An old favorite, obviously. Enjoy: ", bottle.title)
        print(bottle.review)
        # put it into out main list. We don't need to print out all of the bottles we have seen every time.
        bottles.append(bottle)
