import wineBottle
import windowsBarcodeScanner as barcodeScanner
import database


cellarDB = database.Database(database_name="wine_list")
scanner = barcodeScanner.BarcodeScanner(pixelWidth=1280, pixelHeight=720)

upc_1 = 852848000007
db_results = cellarDB.lookupUPC("bottles", upc_1)
if len(db_results) > 0:
    for bottle in db_results:
        wineBottle.WineBottle(bottle).print()
else:
    new_bottle = wineBottle.WineBottle(jsonPackage=scanner.lookupUPC(upc_1))
    print(new_bottle.getData())
    cellarDB.insert_bottle(table="bottles", data=new_bottle.getData())
