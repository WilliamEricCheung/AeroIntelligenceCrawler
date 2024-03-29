import scrapy


class DefenseSpider(scrapy.Spider):
    name = "defense"
    allowed_domains = ["defense.gov"]
    start_urls = ["https://defense.gov/News"]

    def parse(self, response):
        pass
