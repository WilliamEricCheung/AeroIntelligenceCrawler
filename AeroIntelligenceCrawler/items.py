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
    _id = scrapy.Field()
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
    homepage_image = scrapy.Field()
    homepage_image_description_en = scrapy.Field()
    homepage_image_description_cn = scrapy.Field()
