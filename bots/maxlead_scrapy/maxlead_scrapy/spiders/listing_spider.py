# -*- coding: utf-8 -*-

import scrapy,time,os,re
from bots.maxlead_scrapy.maxlead_scrapy.items import ListingsItem
from maxlead_site.models import UserAsins,Listings
from django.db.models import Count


class ListingSpider(scrapy.Spider):

    name = "listing_spider"
    start_urls = []
    url = "https://www.amazon.com/dp/%s/ref=sr_1_16?s=home-garden&ie=UTF8&qid=%d&sr=1-16&keywords=shower+head&th=1&psc=1"
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
        item['brand'] = response.css('div#titleSection a#brand::text').extract_first()
        if not item['brand']:
            item['brand'] = response.css('div#bylineInfo_feature_div a#bylineInfo::text').extract_first()
        item['brand'] = item['brand'].replace('\n','').strip()
        item['feature'] = ''
        des_li = response.css('div#feature-bullets li span.a-list-item::text').extract()
        if des_li:
            for val in des_li:
                val = re.sub(r"\n|\t",'',val)
                item['feature'] += val + '\n'

        des_res = re.sub("\n", ",",
                          response.css("div#productDescription").xpath("string(p)").extract_first(default="").strip())
        item['description'] = des_res

        item['buy_box'] = []
        buyBoxs = response.css('div#merchant-info a::text').extract()
        item['buy_box'] = 'Ours'
        item['price'] = response.css('tr#priceblock_ourprice_row span#priceblock_ourprice::text').extract_first()
        if not item['price']:
            item['price'] = response.css('tr#priceblock_dealprice_row span#priceblock_dealprice::text').extract_first()

        review = response.css('span#acrCustomerReviewText::text').extract_first().split(' ')
        item['total_review'] = review[0]
        score = response.css('span#acrPopover::attr("title")').extract_first().split(' ')
        item['rvw_score'] = score[0]
        category_rank1 = response.css('li#SalesRank::text').extract()
        if category_rank1:
            item['category_rank'] = category_rank1[1].replace('\n','').split(' (')[0]
            rank_list = response.css('ul.zg_hrsr li.zg_hrsr_item')
            if rank_list:
                rank_list_item = ''
                for res in rank_list:
                    rank_list_item += '|'+res.css('span.zg_hrsr_rank::text').extract_first()+' in '
                    for i,val in enumerate(res.css('a::text').extract(),1):
                        if i == len(res.css('a::text').extract()):
                            rank_list_item += val
                        else:
                            rank_list_item+=val +' > '

                item['category_rank'] = item['category_rank']+rank_list_item
        else:
            rank_el = response.css('table#productDetails_detailBullets_sections1 tr:nth-child(3) td span span::text').extract()
            if rank_el:
                rank_item = ''
                item['category_rank'] = rank_el[0].split(' (')[0]
                rank_span = response.css('table#productDetails_detailBullets_sections1 tr:nth-child(3) td span span')
                for n,rank_a in enumerate(rank_span,0):
                    if not n==0:
                        a = rank_a.css('a::text').extract()
                        for s,val in enumerate(a,1):
                            if s == len(a):
                                item['category_rank'] += val
                            elif s == 1:
                                item['category_rank'] += '|' + rank_el[2] + val + ' > '
                            else:
                                item['category_rank'] += val + ' > '

        item['inventory'] = 0
        item['image_urls'] = []
        img_el = response.css('div#altImages ul.a-unordered-list li.item')
        res = img_el[0].css('span.a-button-text img::attr("src")').extract_first()
        if res:
            name_res = os.path.basename(res).split('._SS40_')
            filename = name_res[0] + name_res[1]
            if not os.path.splitext(filename)[1] == '.png':
                res = os.path.dirname(res) + '/' + filename
                listing = Listings.objects.filter(asin=asin_id)
                item['image_urls'].append(res)
                if listing:
                    listing = listing.latest('created')
                    us = res.split('/')[3:]
                    image_file_name = '_'.join(us)
                    if not os.path.basename(listing.image_names) == image_file_name:
                        item['image_date'] = time.strftime('%Y-%m-%d',time.localtime(time.time()))
                    else:
                        item['image_date'] = listing.image_date
                else:
                    item['image_date'] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        # for img_re in response.css('div#altImages ul.a-unordered-list li.item'):
        #     res = img_re.css('span.a-button-text img::attr("src")').extract_first()
        #     if res:
        #         name_res = os.path.basename(res).split('._SS40_')
        #         filename = name_res[0]+name_res[1]
        #         if not os.path.splitext(filename)[1] == '.png':
        #             res = os.path.dirname(res)+'/'+filename
        #             item['image_urls'].append(res)
        yield item