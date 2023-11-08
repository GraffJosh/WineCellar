import mysql.connector
from mysql.connector import errorcode
import json, requests
import logging
import time
from datetime import date as datettimedate


class Database:
    def __init__(
        self,
        host="sliver.local",
        user="rpiScanner",
        password="scannerUserPassword",
        database_name="",
        logger_name="",
        default_table=None,
    ) -> None:
        self.config = {
            "user": user,
            "password": password,
            "host": host,
            "database": database_name,
            "raise_on_warnings": True,
        }

        self.default_table = default_table
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
            config = self.config
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

    def get(self, inTable=None, inCol=None, inCondition=None):
        self.connect()
        cursor = self.cnx.cursor(buffered=True)
        commandList = []
        results = []
        commandStr = "SELECT * FROM {} ".format(inTable)
        conditionStr = ""
        if inCondition:
            for condition in inCondition:
                conditionStr = "WHERE {}='{}'".format(inCol, condition)
                commandList.append(commandStr + conditionStr)

        for command in commandList:
            print(command)
            cursor.execute(command)
            results.append(cursor.fetchone())
        return results
        pass

    def put(self, inTable=None, inDict={}):
        self.connect()
        if not inTable:
            inTable = self.default_table
        commandStr = "INSERT IGNORE INTO {} ".format(inTable)
        colsStr = "("
        colsStr = colsStr + ", ".join(list(inDict.keys())) + ") "
        valsStr = "VALUES ('"
        valsStr = valsStr + "', '".join(map(str, list(inDict.values()))) + "')"

        cursor = self.cnx.cursor()
        commandStr = (commandStr + colsStr + valsStr).encode("unicode_escape")
        print(commandStr)
        try:
            cursor.execute(commandStr)
        except mysql.connector.errors.DatabaseError as errorText:
            print("You've already added this item! ", errorText)

        # commit the changes
        self.cnx.commit()
        cursor.close()
        pass

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

    def searchUPC(self, upc):
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
        return data

    def lookupUPC(self, inTable, upc):
        results = self.get(inTable=inTable, inCol="upc", inCondition=[upc])
        bottles = []
        for upc, title, brand, price, image, link, date, data in results:
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
            data = self.searchUPC(upc=upc)
            if data:
                bottles.append(
                    {
                        "upc": data["upc"],
                        "title": data["title"],
                        "brand": data["brand"],
                        "price": data["offers"][0]["price"],
                        "image": data["images"][0],
                        "link": data["offers"][0]["link"],
                        "date": date.today(),
                        "data": data,
                        "new": True,
                    }
                )
            else:
                print("Bottle not found online!")
                bottles.append(
                    {
                        "upc": upc,
                        "title": None,
                        "brand": None,
                        "price": None,
                        "image": None,
                        "link": None,
                        "date": date.today(),
                        "data": None,
                        "new": True,
                    }
                )
        # commit the changes
        return bottles

    def __del__(self):
        self.disconnect()
