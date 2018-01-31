# -*- coding: utf-8 -*-

from scrapy import cmdline


name = 'review_spider'
asin = 'B074NZH73Z'
cmd = 'scrapy crawl {0} -a asin={1}'.format(name,asin)
cmdline.execute(cmd.split())
