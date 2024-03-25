# 新闻资讯爬虫项目

这是一个使用Scrapy、MongoDB和ElasticSearch构建的新闻资讯爬虫项目。

## 功能

- 爬取指定新闻网站的新闻文章
- 使用ElasticSearch进行全文搜索和索引

## 安装

1. 克隆项目到本地：

    ```shell
    git clone https://github.com/WilliamEricCheung/AeroIntelligenceCrawler
    ```

2. 进入项目目录：

    ```shell
    cd AeroIntelligenceCrawler
    ```

3. 安装依赖：

    ```shell
    echo [your-machine-root-password] | sudo -S ./install-prerequisite.sh
    pip install -r requirements.txt
    ```

## 配置

在 `settings.py` 文件中，你可以配置以下参数：

- `MONGODB_URI`：MongoDB数据库的连接URI
- `ELASTICSEARCH_HOST`：ElasticSearch的主机地址
- `ELASTICSEARCH_PORT`：ElasticSearch的端口号
- `LOG_LEVEL`: 日志级别

## 创建爬虫
```shell
scrapy genspider ifeng mil.ifeng.com/shanklist/14-35083-
```

## 运行

运行爬虫：
```shell
scrapy crawl airandspaceforces
```

每12小时爬取的定时任务（cron）设置：
```shell
crontab -e

# 例子
0 */12 * * * cd /path/to/AeroIntelligenceCrawler && python3 main.py
# 爬虫服务器上
0 */12 * * * cd ~/Project/AeroIntelligenceCrawler && python3 main.py

# Ctrl+X然后按Y然后按Enter来保存并退出编辑器
# 使用crontab -l命令来查看定时任务
```