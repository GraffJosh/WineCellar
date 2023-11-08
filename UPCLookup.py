import wineBottle
import barcodeScanner as barcodeScanner
import wineBottle
import database


cellarDB = database.Database(database_name="wine_list")
scanner = barcodeScanner.BarcodeScanner(pixelWidth=1280, pixelHeight=720)
last_bottles = []
upc_codes = []
while True:
    last_codes = scanner.getCode(inTimeout=-1)
    print("Last codes: ", last_codes)
    if len(last_codes) > 0:
        for code in last_codes:
            if code not in upc_codes:
                upc_codes.append(code)
                db_entries = cellarDB.lookupUPC(table="bottles", upc=code)
                if len(db_entries) > 0:
                    for db_entry in db_entries:
                        last_bottles.append(wineBottle.WineBottle(inDict=db_entry))
                else:
                    print("bottle not found by DB")
    else:
        print("No barcodes detected")

    for bottle in last_bottles:
        if bottle.new:
            cellarDB.put(table="bottles", data=bottle.getData())
            print("New bottle! ", bottle.title, " Enjoy!")
            bottle.print()
        else:
            print("An old favorite, obviously. Enjoy: ", bottle.title)
    # print(mydb)
