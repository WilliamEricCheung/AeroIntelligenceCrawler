from elasticsearch_dsl import Document, Date, Completion, Keyword, Text
from elasticsearch_dsl.connections import connections
from datetime import datetime

connections.create_connection(hosts="localhost:9210")


class Article(Document):
    title_en = Text(analyzer='snowball', fields={'raw': Keyword()})
    text_en = Text(analyzer='snowball')
    create_date = Date()
    url = Keyword()
    published_from = Keyword()
    insert_at = Date()

    # suggest = Completion(analyzer="ik_smart", filter=["lowercase"])
    # title = Text(analyzer="ik_max_word")
    # front_image_url = Keyword()
    # front_image_path = Keyword()

    class Index:
        name = "article"

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
