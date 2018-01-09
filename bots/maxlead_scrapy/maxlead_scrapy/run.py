# -*- coding: utf-8 -*-

from scrapy import cmdline


name = 'listing_spider'
cmd = 'scrapy crawl {0}'.format(name)
cmdline.execute(cmd.split())
