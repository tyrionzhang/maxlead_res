# -*- coding: utf-8 -*-

from scrapy import cmdline


name = 'qa_spider'
asin = 'B0771J6DSB'
cmd = 'scrapy crawl {0} -a asin={1}'.format(name,asin)
cmdline.execute(cmd.split())
