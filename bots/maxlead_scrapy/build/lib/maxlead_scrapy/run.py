# -*- coding: utf-8 -*-

from scrapy import cmdline


name = 'twu_spider'
# asin = '88'
# cmd = 'scrapy crawl {0} -a asin={1}'.format(name,asin)
cmd = 'scrapy crawl {0}'.format(name)
cmdline.execute(cmd.split())
