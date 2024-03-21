# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import scrapy

class AerointelligencecrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class ArticleItem(scrapy.Item):
    url = scrapy.Field()
    source = scrapy.Field()
    publish_date = scrapy.Field()
    title_en = scrapy.Field()
    title_cn = scrapy.Field()
    content_en = scrapy.Field()
    content_cn = scrapy.Field()
    summary = scrapy.Field()
    images = scrapy.Field()
    tables = scrapy.Field()
    tags = scrapy.Field()
    read_num = scrapy.Field()
