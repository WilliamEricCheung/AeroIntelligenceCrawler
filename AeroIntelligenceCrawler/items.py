# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import datetime

import scrapy
from elasticsearch_dsl.connections import connections
from scrapy.loader.processors import MapCompose
from w3lib.html import remove_tags

from models.es_types import Article

es = connections.create_connection(Article._doc_type.using)


class AerointelligencecrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


class ArticleItem(scrapy.Item):
    title = scrapy.Field()
    insert_at = scrapy.Field(
        input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()

    def save_to_es(self):
        article = Article()
        article.title_en = self['title_en']
        article.text_en = remove_tags(self["text_en"])
        article.create_date = self["create_date"]
        article.url = self["url"]
        article.published_from = self["published_from"]
        article.insert_at = self["insert_at"]
        article.save()

        return
