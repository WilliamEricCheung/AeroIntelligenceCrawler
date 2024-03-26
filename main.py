import os.path
import sys

from scrapy.cmdline import execute

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# execute(["scrapy", "crawl", "airandspaceforces"])
execute("scrapy crawl airandspaceforces".split(" "))
execute("scrapy crawl ifeng".split(" "))
