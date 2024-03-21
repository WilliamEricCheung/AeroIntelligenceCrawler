from typing import Any
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import os
import re
import datetime
import pytz

from AeroIntelligenceCrawler.items import ArticleItem

class AirandspaceforcesSpider(scrapy.Spider):
    name = "airandspaceforces"
    allowed_domains = ["airandspaceforces.com"]
    start_urls = ["https://airandspaceforces.com/news/"]
    data_path = "./AeroIntelligenceCrawler/data/"
    day_range = 1

    def __init__(self):
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=service, options=options)

    def parse(self, response):
        # 当已经有1天内的新闻链接文件时，直接读取文件中的链接
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        current_time = datetime.datetime.now()
        file_exists = False
        for file_name in os.listdir(self.data_path):
            file_path = os.path.join(self.data_path, file_name)
            if os.path.isfile(file_path):
                modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                time_difference = current_time - modified_time
            if time_difference.total_seconds() < 86400 * self.day_range:
                with open(file_path, "r") as file:
                    if file.read().strip():
                        file_exists = True
                        print("*** File exists, reading from file ***")
                        with open(file_path, "r") as file:
                            for line in file:
                                yield scrapy.Request(line.strip(), callback=self.parse_article)
                        break
        # 当没有1天内的新闻链接文件时，爬取新的链接
        if not file_exists:
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
            with open(f"{self.data_path}{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt", "a") as file:
                wait = WebDriverWait(self.driver, 10)
                news_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//article//div//div')))
                for news in news_list:
                    news_date_obj = self.get_news_date(news.text)
                    if news_date_obj is None:
                        continue
                    if news_date_obj.date() >= (current_time - datetime.timedelta(days=self.day_range)).date():
                        news_url = news.find_element(By.XPATH, './/*[self::h2 or self::h3]/a').get_attribute("href")
                        file.write(news_url + "\n")
                        yield scrapy.Request(news_url, callback=self.parse_article)
                    else:
                        break
    # 提取标签内文本时间
    def get_news_date(self, news_text: str) -> Any:
        news_text = news_text.replace("COMMENTARY", "").strip()
        match = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b", news_text)
        if match is None:
            return None
        return datetime.datetime.strptime(match.group(0), "%B %d, %Y")

    # 处理每条新闻链接
    def parse_article(self, response):
        # self.driver.get(response.url)
        # TODO 处理每个网页的新闻内容

        # 存储到ElasticSearch中
        yield ArticleItem(url=response.url, title_en="title_en", content_en="text_en", publish_date=datetime.datetime.now(pytz.utc))
        # yield {
        #     'title': "title_en",
        #     'text': "text_en",
        #     'date': datetime.datetime.now()
        # }

    def closed(self, reason):
        self.driver.close()