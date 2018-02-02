# -*- coding: utf-8 -*-

from scrapy import cmdline


name = 'listing_spider'
asin = 'B017W77F06'
cmd = 'scrapy crawl {0} -a asin={1}'.format(name,asin)
cmdline.execute(cmd.split())
