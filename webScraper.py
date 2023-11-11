from bs4 import BeautifulSoup
import requests
import cloudscraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import re
import time


class WebScraper:
    def __init__(self) -> None:
        # self.scraper = cloudscraper.create_scraper(
        #     browser={"browser": "chrome", "platform": "windows", "desktop": True}, delay=10
        # )  # returns a CloudScraper instance
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36"
        options.add_argument(f"user-agent={user_agent}")
        print("Getting Wine Info..........")
        self.driver = webdriver.Chrome(options=options)
        self.driver.get("https://www.vivino.com")
        pass

    # def search(self, inUPC):
    #     # Extract the songtext only and save it in file\
    #     url = "https://www.cellartracker.com/pickproducer.asp?szSearch={}&PickWine=on#".format(
    #         inUPC
    #     )

    #     html_content = self.scraper.get(url).text
    #     soup = BeautifulSoup(html_content, "lxml")
    #     print(soup.prettify())
    #     # search on page for div class block songbook and extract songtext between <p>
    #     wine_table = soup.find("table", attrs={"class": "add_search_results"})
    #     for item in wine_table:
    #         print(item)
    #     print(wine_table)
    #     wine_table_data = wine_table.find("tr")  # contains 2 rows
    #     for item in wine_table_data:
    #         print(item)

    #     # Get all the headings of Lists
    #     headings = []
    #     for td in wine_table_data[0].find_all("td"):
    #         # remove any newlines and extra spaces from left and right
    #         headings.append(td.b.text.replace("\n", " ").strip())

    def search(self, search):
        time.sleep(2)
        search_bar = self.driver.find_element("name", "q")
        # search_bar = self.driver.find_element(By.XPATH, "//form[input/@name ='search']")
        # search_bar = WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.XPATH, "//*[@type='text']"))
        # )
        search_bar.send_keys(search + "\n")
        # WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.XPATH, "(//*[@value='Google Search'])[2]"))
        # ).click()
        time.sleep(2)
        bottles = self.driver.find_element("xpath", "//*[@data-vintage]").text.split("\n")
        print(bottles)
        description = bottles[0]
        winery = bottles[1]
        text = bottles[2]
        rating = bottles[3]
        text2 = bottles[4]
        text3 = bottles[5]
        price = bottles[6]

        wine_info = {
            "description": description,
            # "vintage": vintage,
            "price": price,
            "rating": rating,
            # "variety": variety,
            # "appelation": appelation,
            "winery": winery,
        }
        # print(wine_info)
        return wine_info
