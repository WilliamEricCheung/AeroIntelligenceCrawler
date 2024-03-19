from typing import Any
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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
    day_range = 7

    def __init__(self):
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=service, options=options)

    def parse(self, response):
        self.driver.get(response.url)
        while True:
            news_list = self.driver.find_elements(By.XPATH, '//article//div//div')
            # 判断当前页面中最后一个新闻的时间是否满足day_range内，不满足则不需要再加载更多
            last_news = news_list[-1]
            last_news_date_obj = self.get_news_date(last_news.text)
            if last_news_date_obj.date() >= (datetime.datetime.now() - datetime.timedelta(days=self.day_range)).date():
                # 点击加载更多按钮
                wait = WebDriverWait(self.driver, 10)
                load_more_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@class="alm-load-more-btn more"]')))
                # 使用 ActionChains 来滚动到按钮的位置
                actions = ActionChains(self.driver)
                actions.move_to_element(load_more_button).perform()
                # 然后再点击按钮
                self.driver.execute_script("arguments[0].click();", load_more_button)
            else:
                break
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        with open(f"{self.data_path}{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt", "a") as file:
            wait = WebDriverWait(self.driver, 10)
            # 获取加载后所有新闻的链接
            # news_list = self.driver.find_elements(By.XPATH, '/T/article//div//div')
            news_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//article//div//div')))
            for news in news_list:
                news_date_obj = self.get_news_date(news.text)
                if news_date_obj is None:
                    continue
                # 因为网站上的新闻发布时间已排序，所以只需判断最新的新闻是否在day_range内，不在则退出
                if news_date_obj.date() >= (datetime.datetime.now() - datetime.timedelta(days=self.day_range)).date():
                    news_url = news.find_element(By.XPATH, './/*[self::h2 or self::h3]/a').get_attribute("href")
                    file.write(news_url + "\n")
                    yield scrapy.Request(news_url, callback=self.parse_article)
                else:
                    break

    def get_news_date(self, news_text: str) -> Any:
        news_text = news_text.replace("COMMENTARY", "").strip()
        match = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b", news_text)
        if match is None:
            return None
        return datetime.datetime.strptime(match.group(0), "%B %d, %Y")

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