# -*- coding: utf-8 -*-

from scrapy import cmdline


name = 'listing_spider'
asin = 'B00BOYG4WE'
cmd = 'scrapy crawl {0} -a asin={1}'.format(name,asin)
cmdline.execute(cmd.split())
