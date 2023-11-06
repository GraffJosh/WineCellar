import wineBottle
import barcodeScanner as barcodeScanner
import database


cellarDB = database.Database(database_name="wine_list")
scanner = barcodeScanner.BarcodeScanner(pixelWidth=1280, pixelHeight=720)
last_codes = scanner.getCode()
last_bottles = []

if len(last_codes) > 0:
    for code in last_codes:
        last_bottles.append(wineBottle.WineBottle(scanner.lookupUPC(code)))
else:
    print("No barcodes detected")

for bottle in last_bottles:
    print(bottle.getData())
    cellarDB.insert_bottle("bottles", bottle.getData())


# print(mydb)
