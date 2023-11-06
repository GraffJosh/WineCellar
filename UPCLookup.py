import json, requests
import wineBottle
import mysql.connector
from mysql.connector import errorcode
import logging
import time


def lookupUPC(upc):
    url = "https://api.upcitemdb.com/prod/trial/lookup?upc=%s" % (upc)
    response = requests.get(url)
    response.raise_for_status()  # check for errors

    # Load JSON data into a Python variable.
    jsonData = json.loads(response.text)
    return jsonData


upc = 852848000007
wineBottle = wineBottle.WineBottle(jsonPackage=lookupUPC(upc))
mydb = mysql.connector.connect(
    host="sliver.local", user="rpiScanner", password="scannerUserPassword"
)

config = {
    "user": "rpiScanner",
    "password": "scannerUserPassword",
    "host": "sliver.local",
    "database": "wine_bottle",
    "raise_on_warnings": True,
}

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Log to console
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also log to a file
file_handler = logging.FileHandler("cpy-errors.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def connect_to_mysql(config, attempts=3, delay=2):
    attempt = 1
    # Implement a reconnection routine
    while attempt < attempts + 1:
        try:
            return mysql.connector.connect(**config)
        except (mysql.connector.Error, IOError) as err:
            if attempts is attempt:
                # Attempts to reconnect failed; returning None
                logger.info("Failed to connect, exiting without a connection: %s", err)
                return None
            logger.info(
                "Connection failed: %s. Retrying (%d/%d)...",
                err,
                attempt,
                attempts - 1,
            )
            # progressive reconnect delay
            time.sleep(delay**attempt)
            attempt += 1
    return None


connect_to_mysql(config=config)
print(mydb)
