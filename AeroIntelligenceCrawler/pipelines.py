# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import ArticleItem
from elasticsearch_dsl import connections


class AerointelligencecrawlerPipeline:
    def process_item(self, item, spider):
        # print(item)
        return item

class ElasticsearchPipeline(object):
    def open_spider(self, spider):
        self.client = connections.create_connection(hosts=["http://localhost:9200"])

    def close_spider(self, spider):
        pass
    #将数据写入到es中
    def process_item(self,item,spider):
        # self.client.index(index="article", id=item['url'] ,body=dict(item))
        # 当不存在这个id的文档时，就插入一个新的文档，存在时就更新这个文档
        self.client.update(index="article", id=item['url'], body={"doc": dict(item), "doc_as_upsert": True})
        return item