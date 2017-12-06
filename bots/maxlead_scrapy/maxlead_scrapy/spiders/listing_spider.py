# -*- coding: utf-8 -*-

import scrapy,time,os
from bots.maxlead_scrapy.maxlead_scrapy.items import ListingsItem
from maxlead_site.models import UserAsins
from django.db.models import Count


class ListingSpider(scrapy.Spider):

    name = "listing_spider"
    start_urls = []
    url = "https://www.amazon.com/dp/%s/ref=sr_1_16?s=home-garden&ie=UTF8&qid=%d&sr=1-16&keywords=shower+head"
    res = list(UserAsins.objects.filter(is_use=True).values('aid','review_watcher','listing_watcher','sku').annotate(count=Count('aid')))
    if res:
        for re in res:
            asin = url % (re['aid'], int(time.time()))
            start_urls.append(asin)

    def parse(self, response):
        res_asin = response.url.split('/')
        asin_id = res_asin[4]
        item = ListingsItem()
        for val in self.res:
            if val['aid'] == asin_id:
                item['sku'] = val['sku']

        item['title'] = response.css('div#titleSection span#productTitle::text').extract_first().replace('\n','').strip()
        item['asin'] = asin_id
        item['brand'] = response.css('div#titleSection a#brand::text').extract_first().replace('\n','').strip()
        buyBoxs = response.css('div#availability_feature_div span#merchant-info a::text').extract()
        item['buy_box'] = 'Ours'
        item['price'] = response.css('tr#priceblock_ourprice_row span#priceblock_ourprice::text').extract_first()

        review = response.css('span#acrCustomerReviewText::text').extract_first().split(' ')
        item['total_review'] = review[0]
        score = response.css('span#acrPopover::attr("title")').extract_first().split(' ')
        item['rvw_score'] = score[0]
        item['category_rank'] = response.css('li#SalesRank::text').extract_first()
        if item['category_rank']:
            item['category_rank'] = item['category_rank'].replace('\n','').split(' (')[0]
        else:
            item['category_rank'] = response.css('tr#SalesRank td.value::text').extract_first()
            if item['category_rank']:
                item['category_rank'] = item['category_rank'].replace('\n', '').split(' (')[0]
        item['inventory'] = 0
        item['image_urls'] = []
        for img_re in response.css('div#altImages ul.a-unordered-list li.item'):
            res = img_re.css('span.a-button-text img::attr("src")').extract_first()
            if res:
                item['image_urls'].append(res)
        yield item