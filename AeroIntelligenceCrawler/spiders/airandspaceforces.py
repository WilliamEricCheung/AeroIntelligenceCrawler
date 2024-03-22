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
    source = "美国空天部队杂志"
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
            if time_difference.total_seconds() < 86400 * self.day_range / 2:
                with open(file_path, "r") as file:
                    if file.read().strip():
                        file_exists = True
                        print("*** File exists, reading from file ***")
                        with open(file_path, "r") as file:
                            for line in file:
                                news_date_str, news_url = line.split(' ')
                                news_date = datetime.datetime.strptime(news_date_str, "%Y-%m-%d").date()
                                yield scrapy.Request(news_url, callback=self.parse_article, meta={'news_date': news_date})
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
                    news_date = news_date_obj.date()
                    if news_date >= (current_time - datetime.timedelta(days=self.day_range)).date():
                        news_url = news.find_element(By.XPATH, './/*[self::h2 or self::h3]/a').get_attribute("href")
                        file.write(str(news_date) + " " + news_url+ "\n")
                        yield scrapy.Request(news_url, callback=self.parse_article, meta={'news_date': news_date})
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
        self.driver.get(response.url)
        news_date = response.meta['news_date']
        # 获取新闻的背景图片
        # 等待元素加载
        wait = WebDriverWait(self.driver, 10)
        homepage_image = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div[2]/div[1]')))
        style = homepage_image.get_attribute("style")
        homepage_image_url = re.search(r'background-image: url\("(.*)"\);', style).group(1)
        # 获取新闻的背景图片描述
        homepage_image_description_en = self.driver.find_element(By.XPATH, '//*[@id="content"]/div[2]/div[2]/div[1]').text
        # 获取新闻的标题
        title_en = self.driver.find_element(By.XPATH, '//*[@id="main"]/h1').text
        # 处理每个网页的新闻内容
        body_div = self.driver.find_element(By.XPATH, '//*[@id="main"]/div[2]')

        content = []
        images = []
        tables = []
        image_counter = 1
        table_counter = 1
        for element in body_div.find_elements(By.XPATH, './*'):
            if element.tag_name == "p":
                content.append(element.text + "\n")
            elif element.tag_name == "figure":
                image_placeholder = f"<image{image_counter}>"
                image_path = element.find_element(By.XPATH, './img').get_attribute("src")
                image_description_en = element.find_element(By.XPATH, './figcaption').text if element.find_elements(By.XPATH, './figcaption') else ""
                images.append({
                    "image_placeholder": image_placeholder,
                    "image_path": image_path,
                    "image_description_en": image_description_en
                })
                content.append(image_placeholder)
                image_counter += 1
            elif element.tag_name == "table":
                table_placeholder = f"<table{table_counter}>"
                table_content = element.get_attribute('outerHTML')
                tables.append({
                    "table_placeholder": table_placeholder,
                    "table_content": table_content
                })
                content.append(table_placeholder)
                table_counter += 1

        # 存储到ElasticSearch中
        yield ArticleItem(url=response.url, 
                          source=self.source,
                          publish_date=news_date,
                          title_en=title_en, 
                          content_en=content, 
                          images=images,
                          tables=tables,
                          homepage_image=homepage_image_url,
                          homepage_image_description_en=homepage_image_description_en)
        # yield {
        #     'title': "title_en",
        #     'text': "text_en",
        #     'date': datetime.datetime.now()
        # }

    def closed(self, reason):
        self.driver.close()