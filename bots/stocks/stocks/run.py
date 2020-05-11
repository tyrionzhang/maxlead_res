# -*- coding: utf-8 -*-

from scrapy import cmdline

# name = 'watcher_spider'
# asin = 'B00P17WZRS'
# cmd = 'scrapy crawl {0} -a asin={1}'.format(name,asin)

name = 'twu_spider'
cmd = 'scrapy crawl {0}'.format(name)
# cmd = 'scrapy crawl {0} -a xlsx_file={1}'.format(name,'atl-order-0224.xlsx')
cmdline.execute(cmd.split())
