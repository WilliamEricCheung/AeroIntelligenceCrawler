from typing import Any
import scrapy
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os
import re
import datetime

from AeroIntelligenceCrawler.items import ArticleItem
from selenium.common.exceptions import TimeoutException


class DefenseSpider(scrapy.Spider):
    name = "defense"
    source = "美国防部"
    allowed_domains = ["defense.gov"]
    start_urls = ["https://www.defense.gov/News/"]
    data_path = "./AeroIntelligenceCrawler/data/defense/"     # 爬取列表存储路径
    # 图片这两路径不一致是因为前后端分离，前端访问的是Django的路径，后端访问的是本地路径
    image_folder = os.path.expanduser('~/Project/AeroIntelligenceDjango/AeroIntelligenceDjango/image/') # 图片存储路径
    image_path = "image/"                                         # 图片数据库里面放的路径
                      
    day_range = 1

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
                news_to_yield = []
                while need_load_more:
                    wait = WebDriverWait(self.driver, 10)
                    # # 拉到页面最底部
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    news_list = wait.until(
                        EC.presence_of_all_elements_located((By.XPATH, '//div[@class="feature-template-container"]/div')))
                    # 先获取本页的所有新闻url和时间
                    for news in news_list:
                        news_date_obj = self.get_news_date(news.text)
                        if news_date_obj is None:
                            continue
                        news_date = news_date_obj.date()
                        if news_date >= (current_time - datetime.timedelta(days=self.day_range)).date():
                            news_url = news.find_element(By.XPATH, './/a[@class="link-overlay"]').get_attribute("href")
                            news_to_yield.append((news_url, news_date))
                        else:
                            # 如果已经获取了day_range天内的新闻，就不再获取
                            need_load_more = False
                            break
                    # 如果还需要接着获取下一页，点击"点击回到相关新闻顶部"的按钮
                    if need_load_more:
                        print("***Need to load more news.")
                        try:
                            next_page_button = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, '//*[@id="alist"]/div[3]/div/div[1]/div/div[7]'))
                            )
                            next_page_button.click()
                        except TimeoutException:
                            print("***No more news to load.")
                            need_load_more = False

                # 再根据新闻链接爬取新闻内容
                with open(f"{self.data_path}{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt", "a") as file:
                    for news_url, news_date in news_to_yield:
                        file.write(str(news_date) + " " + news_url + "\n")
                for news_url, news_date in news_to_yield:
                    yield scrapy.Request(news_url, callback=self.parse_article, meta={'news_date': news_date})
    
    # 处理每条新闻链接
    def parse_article(self, response):
        news_date = response.meta['news_date']
        # 获取新闻的标题
        title_en = response.xpath('//h1[@class="maintitle"]/text()').get().strip()
        # 处理每个网页的新闻内容
        body_div = response.xpath('//div[@class="body"]')
        content = []
        images = []
        image_counter = 1
        for element in body_div.xpath('.//p | .//div[@class="image-wrapper"]/img'):
            tag = element.xpath('name()').get()
            if tag == "p":
                text = element.xpath("string()").get().strip()
                if text:
                    content.append(text + "\n")
            elif tag == "img":
                image_placeholder = f"<image{image_counter}>"
                image_url = element.xpath('@src').get()
                print("***image_url:  "+image_url)
                if image_url is not None:
                    image_name = image_url.split('/')[-1]  # 从URL中获取图片名
                    image_path = os.path.join(self.image_path, image_name)
                    yield scrapy.Request(image_url, callback=self.save_image)
                    images.append({
                    "image_placeholder": image_placeholder,
                    "image_path": image_path
                    })
                    content.append(image_placeholder)
                    image_counter += 1
        
        homepage_image_path = images[0]["image_path"] if images else ""

        # 存储到ElasticSearch中
        yield ArticleItem(url=response.url,
                  source=self.source,
                  publish_date=news_date,
                  title_en=title_en,
                  content_en=content,
                  images=images,
                  homepage_image=homepage_image_path)

    def save_image(self, response):
        # 从URL中获取图片名
        print("***response.url:  "+response.url)
        image_name = os.path.basename(urlparse(response.url).path)
        image_dir = os.path.expanduser(self.image_folder)
        os.makedirs(image_dir, exist_ok=True)  # 确保目录存在
        image_path = os.path.join(image_dir, image_name)
        with open(image_path, 'wb') as f:
            f.write(response.body)

        # 检查文件是否存在并且其大小大于0
        if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
            print(f"Image {image_name} saved successfully.")
        else:
            print(f"Failed to save image {image_name}.")

    # 提取标签内文本时间
    def get_news_date(self, news_text: str) -> Any:
        # 匹配 "Release | March 29, 2024 Ericsson" 这种格式
        match = re.search(r"\b\w+ \d{1,2}, \d{4}\b", news_text)
        if match is not None:
            date_str = match.group(0)
            return datetime.datetime.strptime(date_str, "%B %d, %Y")
        return None

    def closed(self, reason):
        self.driver.close()
