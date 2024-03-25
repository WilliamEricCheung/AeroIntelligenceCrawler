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


class DefensenewsSpider(scrapy.Spider):
    name = "defensenews"
    allowed_domains = ["defensenews.com"]
    start_urls = ["https://defensenews.com/air"]
    data_path = "./AeroIntelligenceCrawler/data/defensenews/"     # 爬取列表存储路径
    image_folder = os.path.expanduser('~/Project/NewsImage/')           # 图片存储路径

    def __init__(self):
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=service, options=options)
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        os.makedirs(self.image_folder, exist_ok=True)  
        
    def parse(self, response):
        pass
