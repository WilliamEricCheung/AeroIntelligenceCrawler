from typing import Any
import scrapy
from scrapy.http import JsonRequest
from urllib.parse import urlparse
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
import json

from AeroIntelligenceCrawler.items import ArticleItem


class AirandspaceforcesSpider(scrapy.Spider):
    name = "airandspaceforces"
    source = "美国空天部队杂志"
    allowed_domains = ["airandspaceforces.com", "172.16.26.4"]
    start_urls = ["https://airandspaceforces.com/news/"]
    data_path = "./AeroIntelligenceCrawler/data/airandspaceforces/"     # 爬取列表存储路径
    # 图片这两路径不一致是因为前后端分离，前端访问的是Django的路径，后端访问的是本地路径
    image_folder = os.path.expanduser('~/Project/AeroIntelligenceDjango/AeroIntelligenceDjango/image/') # 图片存储路径
    image_path = "image/"                                         # 图片数据库里面放的路径
                      
    day_range = 3

    def __init__(self):
        service = Service(executable_path="/opt/google/chromedriver-linux64/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=service, options=options)
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        os.makedirs(self.image_folder, exist_ok=True)     

    def parse(self, response):
        # 当已经有day_range天内的新闻链接文件时，直接读取文件中的链接
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
                                yield scrapy.Request(news_url, callback=self.parse_article,
                                                     meta={'news_date': news_date})
                        break
        # 当没有day_range天内的新闻链接文件时，爬取新的链接
        if not file_exists:
            self.driver.get(response.url)
            need_load_more = True
            while need_load_more:
                wait = WebDriverWait(self.driver, 10)
                news_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//article//div//div')))
                # 判断当前页面中最后一个新闻的时间是否满足day_range内，不满足则不需要再加载更多
                last_news = news_list[-1]
                last_news_date_obj = self.get_news_date(last_news.text)
                if last_news_date_obj is None:
                    # 这种是最后一个新闻出现了COMMENTARY的情况
                    # 点击加载更多按钮
                    wait = WebDriverWait(self.driver, 20)
                    load_more_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@class="alm-load-more-btn more"]')))
                    # 使用 ActionChains 来滚动到按钮的位置
                    actions = ActionChains(self.driver)
                    actions.move_to_element(load_more_button).perform()
                    # 然后再点击按钮
                    self.driver.execute_script("arguments[0].click();", load_more_button)
                    continue
                if last_news_date_obj.date() >= (
                        datetime.datetime.now() - datetime.timedelta(days=self.day_range)).date():
                    # 点击加载更多按钮
                    wait = WebDriverWait(self.driver, 20)
                    load_more_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@class="alm-load-more-btn more"]')))
                    # 使用 ActionChains 来滚动到按钮的位置
                    actions = ActionChains(self.driver)
                    actions.move_to_element(load_more_button).perform()
                    # 然后再点击按钮
                    self.driver.execute_script("arguments[0].click();", load_more_button)
                else:
                    need_load_more = False
            # 先创建一个新的文件，再写入新的新闻链接
            news_to_yield = []
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
                        file.write(str(news_date) + " " + news_url + "\n")
                        news_to_yield.append((news_url, news_date))
                    else:
                        break
            # 再根据新闻链接爬取新闻内容
            for news_url, news_date in news_to_yield:
                yield scrapy.Request(news_url, callback=self.parse_article, meta={'news_date': news_date})

    # 处理每条新闻链接
    def parse_article(self, response):
        news_date = response.meta['news_date']
        # 获取新闻的背景图片
        homepage_image = response.css('#content > div:nth-child(2) > div:nth-child(1)').get()
        style = re.search(r'background-image:url\(\'(.*)\'\)', homepage_image).group(1)
        homepage_image_url = style
        image_name = homepage_image_url.split('/')[-1]  # 从URL中获取图片名
        homepage_image_path = os.path.join(self.image_path, image_name)
        # 使用Scrapy的Request对象来下载图片
        yield scrapy.Request(homepage_image_url, callback=self.save_image)

        # 获取新闻的背景图片描述
        homepage_image_description_en = response.css('#content > div:nth-child(2) > div:nth-child(2) > div:nth-child(1)::text').get()
        # 获取新闻的标题
        title_en = response.css('#main > h1::text').get()
        # 处理每个网页的新闻内容
        body_div = response.xpath('//*[@id="main"]/div[@class="post-body"]')
        content = []
        images = []
        tables = []
        image_counter = 1
        table_counter = 1
        for element in body_div.css('*'):
            tag = element.xpath('name()').get()
            if tag == "p":
                content.append(element.xpath("string()").get().strip() + "\n")
            elif tag == "figure":
                image_placeholder = f"<image{image_counter}>"
                image_url = element.css('img::attr(src)').get()
                # 在这里None的情况是因为有些figure标签下是iframe视频标签，直接跳过
                if image_url is not None:
                    image_description_en = element.css('figcaption::text').get() or ""
                    image_name = image_url.split('/')[-1]  # 从URL中获取图片名
                    image_path = os.path.join(self.image_path, image_name)
                    # 使用Scrapy的Request对象来下载图片
                    yield scrapy.Request(image_url, callback=self.save_image)
                    images.append({
                        "image_placeholder": image_placeholder,
                        "image_path": image_path,
                        "image_description_en": image_description_en
                    })
                    content.append(image_placeholder)
                    image_counter += 1
            elif tag == "table":
                table_placeholder = f"<table{table_counter}>"
                table_content = element.get()
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
                #   content_cn=content_cn,
                  images=images,
                  tables=tables,
                  homepage_image=homepage_image_path,
                  homepage_image_description_en=homepage_image_description_en)

    def save_image(self, response):
        # 从URL中获取图片名
        image_name = os.path.basename(urlparse(response.url).path)
        image_dir = os.path.expanduser(self.image_folder)
        os.makedirs(image_dir, exist_ok=True)  # 确保目录存在
        image_path = os.path.join(image_dir, image_name)
        with open(image_path, 'wb') as f:
            f.write(response.body)

    # 提取标签内文本时间
    def get_news_date(self, news_text: str) -> Any:
        # 缩写对照表，用于将缩写月份转换为全称月份
        month_map = {
            "Jan.": "January",
            "Feb.": "February",
            "March": "March",
            "April": "April",
            "May": "May",
            "June": "June",
            "July": "July",
            "Aug.": "August",
            "Sep.": "September",
            "Oct.": "October",
            "Nov.": "November",
            "Dec.": "December"
        }
        match = re.search(r"\b(Jan.|Feb.|March|April|May|June|July|Aug.|Sep.|Oct.|Nov.|Dec.)\s+\d{1,2},\s+\d{4}\b",
                          news_text)
        if match is None:
            return None

        date_str = match.group(0)
        for key in month_map:
            if key in date_str:
                date_str = date_str.replace(key, month_map[key])
                break

        return datetime.datetime.strptime(date_str, "%B %d, %Y")    

    def closed(self, reason):
        self.driver.close()