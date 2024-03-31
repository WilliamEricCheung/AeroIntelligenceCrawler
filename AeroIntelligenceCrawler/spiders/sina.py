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


class SinaSpider(scrapy.Spider):
    name = "sina"
    source = "新浪军事"
    allowed_domains = ["mil.news.sina.com.cn", "k.sinaimg.cn"]
    start_urls = ["https://mil.news.sina.com.cn"]
    data_path = "./AeroIntelligenceCrawler/data/sina/"  # 爬取列表存储路径
    # 图片这两路径不一致是因为前后端分离，前端访问的是Django的路径，后端访问的是本地路径
    image_folder = os.path.expanduser('~/Project/AeroIntelligenceDjango/AeroIntelligenceDjango/image/')  # 图片存储路径
    image_path = "image/"  # 图片数据库里面放的路径

    # 新浪军事只显示10天内或最多100条的新闻，所以最多只需爬取10天内的新闻
    day_range = 10

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
                wait = WebDriverWait(self.driver, 20)
                # 拉到页面最底部
                while True:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    try:
                        element = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@class="cardlist-a__more-c"]'))
                        )
                        break
                    except:
                        continue
                news_list = wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, '//div[@class="cardlist-a__list"]/div')))
                # 先获取本页的所有新闻url和时间
                for news in news_list:
                    print("***news_text: ", news.text)
                    news_date_obj = self.get_news_date(news.text)
                    if news_date_obj is None:
                        continue
                    news_date = news_date_obj.date()
                    if news_date >= (current_time - datetime.timedelta(days=self.day_range)).date():
                        news_url = news.find_element(By.XPATH, './/h3[@class="ty-card-tt"]/a').get_attribute("href")
                        news_to_yield.append((news_url, news_date))
                    else:
                        # 如果已经获取了day_range天内的新闻，就不再获取
                        need_load_more = False
                        break
                # 如果还需要接着获取下一页，点击"点击回到相关新闻顶部"的按钮
                if need_load_more:
                    try:
                        load_more_button = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//div[@class="cardlist-a__more-c"]'))
                        )
                    except TimeoutException:
                        print("***No more news to load.")
                        need_load_more = False
                    if load_more_button.text == "点击回到相关新闻顶部":
                        self.driver.execute_script("arguments[0].click();", load_more_button)
                    else:
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
        title_cn = response.xpath('//h1[@class="main-title"]/text()').get()
        # 处理每个网页的新闻内容
        body_div = response.xpath('//div[@class="article"]')
        content = []
        images = []
        image_counter = 1
        for element in body_div.css('*'):
            tag = element.xpath('name()').get()
            if tag == "p":
                content.append(element.xpath("string()").get().strip() + "\n")
            elif tag == "div":
                image_placeholder = f"<image{image_counter}>"
                image_url = element.css('img::attr(src)').get()
                if image_url is not None:
                    image_url = "https:" + image_url
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
                          title_cn=title_cn,
                          content_cn=content,
                          images=images,
                          homepage_image=homepage_image_path)

    def save_image(self, response):
        # 从URL中获取图片名
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
        # 匹配 "3月28日 18:35" 或者 "12月28日 18:35" 这种格式
        match = re.search(r"\b(\d{1,2})月(\d{1,2})日 (\d{2}:\d{2}).*?\b", news_text)
        if match is not None:
            month, day, time = match.groups()
            current_year = datetime.datetime.now().year
            date_str = f"{current_year}-{month}-{day} {time}"
            return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")

        # 匹配 "今天 10:53" 这种格式
        match = re.search(r"今天 \d{2}:\d{2}", news_text)
        if match is not None:
            time_str = match.group(0)[3:]
            today = datetime.date.today()
            return datetime.datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M")

        return None

    def closed(self, reason):
        self.driver.close()
