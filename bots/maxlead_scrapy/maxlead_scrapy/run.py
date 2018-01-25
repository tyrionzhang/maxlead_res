# -*- coding: utf-8 -*-

from scrapy import cmdline


name = 'watcher_spider'
asin = 'B071YL74H2'
cmd = 'scrapy crawl {0} -a asin={1}'.format(name,asin)
cmdline.execute(cmd.split())
