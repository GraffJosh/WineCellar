import mysql.connector
from mysql.connector import errorcode
import json, requests
import logging
import time
from datetime import date


class Database:
    def __init__(
        self,
        host="sliver.local",
        user="rpiScanner",
        password="scannerUserPassword",
        database_name="",
        logger_name="",
    ) -> None:
        self.config = {
            "user": user,
            "password": password,
            "host": host,
            "database": database_name,
            "raise_on_warnings": True,
        }

        if logger_name == "":
            logger_name = __name__
        # Set up logger
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Log to console
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Also log to a file
        file_handler = logging.FileHandler("sql-errors.log")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.cnx = self.connect(config=self.config)

    def connect(self, config="", attempts=3, delay=2):
        if config == "":
            config = self
        attempt = 1
        # Implement a reconnection routine
        while attempt < attempts + 1:
            try:
                return mysql.connector.connect(**config)
            except (mysql.connector.Error, IOError) as err:
                if attempts is attempt:
                    # Attempts to reconnect failed; returning None
                    self.logger.info("Failed to connect, exiting without a connection: %s", err)
                    return None
                self.logger.info(
                    "Connection failed: %s. Retrying (%d/%d)...",
                    err,
                    attempt,
                    attempts - 1,
                )
                # progressive reconnect delay
                time.sleep(delay**attempt)
                attempt += 1
        return None

    def disconnect(self):
        self.cnx.close()

    def insert_bottle(self, table, data):
        cursor = self.cnx.cursor()
        add_bottle = (
            "INSERT IGNORE INTO {} "
            "(upc, title, brand, price, image, link, date) "
            "VALUES (%(upc)s, %(title)s,%(brand)s,%(price)s,%(image)s,%(link)s,%(date)s)"
        ).format(table)
        print()
        print("data: ", data)
        print()
        try:
            cursor.execute(add_bottle, data)
        except mysql.connector.errors.DatabaseError:
            print("You've already added this bottle!")

        # commit the changes
        self.cnx.commit()
        cursor.close()

    def lookupUPC(self, table, upc):
        cursor = self.cnx.cursor()
        query = ("SELECT * FROM {} WHERE " "UPC={}").format(table, upc)
        cursor.execute(query)

        print()
        print("data: ", cursor)
        bottles = []
        for upc, title, brand, price, image, link, date, data in cursor:
            bottles.append(
                {
                    "upc": upc,
                    "title": title,
                    "brand": brand,
                    "price": price,
                    "image": image,
                    "link": link,
                    "date": date,
                    "data": data,
                    "new": False,
                }
            )
        if len(bottles) < 1:
            print("Bottle not found in Database!")
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
            upc = data["upc"]
            title = data["title"]
            brand = data["brand"]
            price = data["offers"][0]["price"]
            image = data["images"][0]
            link = data["offers"][0]["link"]
            bottles.append(
                {
                    "upc": upc,
                    "title": title,
                    "brand": brand,
                    "price": price,
                    "image": image,
                    "link": link,
                    "date": date.today(),
                    "data": data,
                    "new": True,
                }
            )

        # commit the changes
        cursor.close()
        return bottles

    def __del__(self):
        self.disconnect()
