import wineBottle
import windowsBarcodeScanner as barcodeScanner
import database


cellarDB = database.Database(database_name="wine_list")
scanner = barcodeScanner.BarcodeScanner(pixelWidth=1280, pixelHeight=720)

upc = 852848000007
bottle1 = wineBottle.WineBottle(jsonPackage=scanner.lookupUPC(upc))
print(bottle1.getData())
cellarDB.insert_bottle(table="bottles", data=bottle1.getData())
