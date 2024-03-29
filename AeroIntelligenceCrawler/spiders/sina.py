import scrapy


class SinaSpider(scrapy.Spider):
    name = "sina"
    allowed_domains = ["mil.news.sina.com.cn"]
    start_urls = ["https://mil.news.sina.com.cn"]

    def parse(self, response):
        pass
