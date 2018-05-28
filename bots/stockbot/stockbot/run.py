# -*- coding: utf-8 -*-

from scrapy import cmdline

# name = 'watcher_spider'
# asin = 'B00P17WZRS'
# cmd = 'scrapy crawl {0} -a asin={1}'.format(name,asin)

name = 'hanover_spider'
cmd = 'scrapy crawl {0}'.format(name)
cmdline.execute(cmd.split())
