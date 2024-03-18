from typing import Any
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from newspaper import Article
from webdriver_manager.chrome import ChromeDriverManager
import os
import re
import datetime

class AirandspaceforcesSpider(scrapy.Spider):
    name = "airandspaceforces"
    allowed_domains = ["airandspaceforces.com"]
    start_urls = ["https://airandspaceforces.com/category/air/"]
    data_path = "./AeroIntelligenceCrawler/data/"

    def __init__(self):
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=service, options=options)

    def parse(self, response):
        self.driver.get(response.url)
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        with open(f"{self.data_path}{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt", "a") as file:
            for news in self.driver.find_elements(By.XPATH, '//article//div//div'):
                news_text = news.text.replace("COMMENTARY", "").strip()
                print("****news_text: ", news_text)
                match = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b", news_text)
                news_date = match.group(0) if match else None
                print("****news_date: ", news_date)
                if news_date is None:
                    continue
                # news_date_str = news_date.split("|")[0].strip()
                # print("news_date_str: ", news_date_str)
                news_date_obj = datetime.datetime.strptime(news_date, "%B %d, %Y")
                if news_date_obj.date() >= (datetime.datetime.now() - datetime.timedelta(days=2)).date():
                    news_url = news.find_element(By.XPATH, './h2/a').get_attribute("href")
                    print("news_url: ", news_url)
                    file.write(news_url + "\n")
                    yield scrapy.Request(news_url, callback=self.parse_article)

    def parse_article(self, response):
        article = Article(response.url)
        article.download()
        article.parse()
        print("article.publish_date: ", article.publish_date)
        print("article.title: ", article.title)
        print("article.text: ", article.text)
        yield {
            'title': article.title,
            'text': article.text,
            'date': article.publish_date
        }

    def closed(self, reason):
        self.driver.close()