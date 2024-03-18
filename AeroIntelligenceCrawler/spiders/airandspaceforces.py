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

from AeroIntelligenceCrawler.items import ArticleItem

class AirandspaceforcesSpider(scrapy.Spider):
    name = "airandspaceforces"
    allowed_domains = ["airandspaceforces.com"]
    start_urls = ["https://airandspaceforces.com/category/air/"]
    data_path = "./AeroIntelligenceCrawler/data/"
    day_range = 2

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
                match = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b", news_text)
                news_date = match.group(0) if match else None
                if news_date is None:
                    continue
                news_date_obj = datetime.datetime.strptime(news_date, "%B %d, %Y")
                # 因为网站上的新闻发布时间已排序，所以只需判断最新的新闻是否在day_range内，不在则退出
                if news_date_obj.date() >= (datetime.datetime.now() - datetime.timedelta(days=self.day_range)).date():
                    news_url = news.find_element(By.XPATH, './h2/a').get_attribute("href")
                    file.write(news_url + "\n")
                    yield scrapy.Request(news_url, callback=self.parse_article)
                else:
                    continue

    def parse_article(self, response):
        article = Article(response.url)
        article.download()
        article.parse()
        yield ArticleItem(title_en=article.title, text_en=article.text, publish_date=article.publish_date)
        yield {
            'title': article.title,
            'text': article.text,
            'date': article.publish_date
        }

    def closed(self, reason):
        self.driver.close()