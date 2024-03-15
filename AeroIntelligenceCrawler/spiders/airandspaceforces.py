from typing import Any
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from newspaper import Article
from webdriver_manager.chrome import ChromeDriverManager
import datetime

class AirandspaceforcesSpider(scrapy.Spider):
    name = "airandspaceforces"
    allowed_domains = ["airandspaceforces.com"]
    start_urls = ["https://airandspaceforces.com/news"]

    def __init__(self):
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=service, options=options)

    def parse(self, response):
        self.driver.get(response.url)
        for news_link in self.driver.find_elements_by_xpath('//a[contains(@href, "/news/")]'):
            news_url = news_link.get_attribute('href')
            yield scrapy.Request(news_url, callback=self.parse_article)

    def parse_article(self, response):
        article = Article(response.url)
        article.download()
        article.parse()
        if article.publish_date and article.publish_date > datetime.datetime.now() - datetime.timedelta(days=7):
            yield {
                'title': article.title,
                'text': article.text,
                'date': article.publish_date
            }

    def closed(self, reason):
        self.driver.close()