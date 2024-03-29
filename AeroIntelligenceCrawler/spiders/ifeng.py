from typing import Any
import scrapy
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

from AeroIntelligenceCrawler.items import ArticleItem

class IfengSpider(scrapy.Spider):
    name = "ifeng"
    source = "凤凰网军事"
    allowed_domains = ["mil.ifeng.com", "news.ifeng.com", "x0.ifengimg.com"]
    start_urls = ["https://mil.ifeng.com/shanklist/14-35083-"]
    data_path = "./AeroIntelligenceCrawler/data/ifeng/"         # 爬取列表存储路径
    image_folder = os.path.expanduser('~/Project/NewsImage/')   # 图片存储路径

    # 凤凰网只显示14天内的新闻，所以最多只需爬取14天内的新闻
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
            while need_load_more:
                wait = WebDriverWait(self.driver, 10)
                news_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="root"]/div[5]/div[1]/div/ul/li')))
                # 判断当前页面中最后一个新闻的时间是否满足day_range内，不满足则不需要再加载更多
                last_news = news_list[-1]
                last_news_date_obj = self.get_news_date(last_news.text)
                if last_news_date_obj.date() >= (
                        datetime.datetime.now() - datetime.timedelta(days=self.day_range)).date():
                    # 点击加载更多按钮
                    wait = WebDriverWait(self.driver, 20)
                    load_more_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//a[@class="news-stream-basic-more"]')))
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
                news_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="root"]/div[5]/div[1]/div/ul/li')))
                for news in news_list:
                    news_date_obj = self.get_news_date(news.text)
                    if news_date_obj is None:
                        continue
                    news_date = news_date_obj.date()
                    if news_date >= (current_time - datetime.timedelta(days=self.day_range)).date():
                        news_url = news.find_element(By.XPATH, './a').get_attribute("href")
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
        # 获取新闻的标题
        title_cn = response.xpath('//*[@id="root"]/div/div[3]/div[1]/div[1]/div[1]/h1/text()').get()
        # 处理每个网页的新闻内容
        body_div = response.xpath('//div[@class="index_text_D0U1y"]')
        content = []
        images = []
        image_counter = 1
        for element in body_div.css('*'):
            tag = element.xpath('name()').get()
            if tag == "p":
                content.append(element.xpath("string()").get().strip() + "\n")
            elif tag == "img":
                image_placeholder = f"<image{image_counter}>"
                image_url = element.css('img::attr(data-lazyload)').get() or element.css('img::attr(src)').get()
                print("***image_url:  "+image_url)
                if image_url is not None:
                    image_name = image_url.split('/')[-1]  # 从URL中获取图片名
                    image_path = os.path.join(self.image_folder, image_name)
                    yield scrapy.Request(image_url, callback=self.save_image)
                    images.append({
                    "image_placeholder": image_placeholder,
                    "image_path": image_path
                    })
                    content.append(image_placeholder)
                    image_counter += 1
        
        homepage_image_path = images[0]["image_path"]

        # 存储到ElasticSearch中
        yield ArticleItem(url=response.url,
                  source=self.source,
                  publish_date=news_date,
                  title_cn=title_cn,
                  content_cn=content,
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
        # 匹配 "03-20 06:49" 这种格式
        match = re.search(r"\b\d{2}-\d{2} \d{2}:\d{2}\b", news_text)
        if match is not None:
            date_str = match.group(0)
            current_year = datetime.datetime.now().year
            return datetime.datetime.strptime(f"{current_year}-{date_str}", "%Y-%m-%d %H:%M")

        # 匹配 "今天 10:53" 这种格式
        match = re.search(r"今天 \d{2}:\d{2}", news_text)
        if match is not None:
            time_str = match.group(0)[3:]
            today = datetime.date.today()
            return datetime.datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M")

        return None

    def closed(self, reason):
        self.driver.close()
