from elasticsearch_dsl import Document, Date, Nested, Keyword, Text, Integer
from elasticsearch_dsl.connections import connections
from datetime import datetime
from elasticsearch_dsl.analysis import analyzer

connections.create_connection(hosts="https://localhost:9210")

# 定义分析器
ik_analyzer = analyzer('ik_max_word')
ik_smart_analyzer = analyzer('ik_smart')

class Image(Document):
    image_placeholder = Keyword()
    image_path = Keyword()
    image_description_en = Text(analyzer=ik_analyzer, search_analyzer=ik_smart_analyzer)
    image_description_cn = Text(analyzer=ik_analyzer, search_analyzer=ik_smart_analyzer)

class Table(Document):
    table_placeholder = Keyword()
    table_content = Object(enabled=False)
    table_description_en = Text(analyzer=ik_analyzer, search_analyzer=ik_smart_analyzer)
    table_description_cn = Text(analyzer=ik_analyzer, search_analyzer=ik_smart_analyzer)

class Article(Document):
    url = Keyword()
    source = Keyword()
    publish_date = Date()
    title_en = Text(fields={'keyword': Keyword(ignore_above=256)}, analyzer=ik_analyzer, search_analyzer=ik_smart_analyzer)
    title_cn = Text(fields={'keyword': Keyword(ignore_above=256)}, analyzer=ik_analyzer, search_analyzer=ik_smart_analyzer)
    content_en = Text(analyzer=ik_analyzer, search_analyzer=ik_smart_analyzer)
    content_cn = Text(analyzer=ik_analyzer, search_analyzer=ik_smart_analyzer)
    summary = Text(analyzer=ik_analyzer, search_analyzer=ik_smart_analyzer)
    images = Nested(Image)
    tables = Nested(Table)
    tags = Keyword()
    read_num = Integer()

    class Index:
        name = 'article'

    def save(self, **kwargs):
        return super(Article, self).save(**kwargs)

if __name__ == "__main__":
    Article.init()
    # article = Article(meta={'id': 1}, title_en='Hello world!',create_date=datetime.now())
    # article.text_en = ''' looong text '''
    # article.published_from = "airandspaceforces.com"
    # article.url = "https://airandspaceforces.com/news/1"
    # article.save()
    #
    # article = Article.get(id=1)
    # print(article)
