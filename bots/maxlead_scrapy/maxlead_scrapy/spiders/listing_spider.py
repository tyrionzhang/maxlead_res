# -*- coding: utf-8 -*-

import scrapy,time,os,re,datetime
import random
from bots.maxlead_scrapy.maxlead_scrapy.items import ListingsItem
from maxlead_site.models import UserAsins,Listings
from django.db.models import Count


class ListingSpider(scrapy.Spider):

    name = "listing_spider"
    start_urls = []
    res = []

    def __init__(self, asin=None, user=None,*args, **kwargs):
        sr = random.randint(1,16)
        url = "https://www.amazon.com/dp/%s/ref=sr_1_%s?ie=UTF8&qid=%d&sr=1-%s&keywords=%s&th=1&psc=1"
        super(ListingSpider, self).__init__(*args, **kwargs)
        if asin == '99':
            self.res = list(UserAsins.objects.filter(is_use=True, is_done=0).values('aid').annotate(count=Count('aid')))
        elif asin == '88':
            self.res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
        elif asin == '100':
            self.res = list(UserAsins.objects.filter(is_use=True,user_id=int(user)).exclude(listing_time__icontains=datetime.datetime.now().
                                                        strftime("%Y-%m-%d")).values('aid').annotate(count=Count('aid')))
        else:
            urls1 = url % (asin, sr, int(time.time()), sr, asin)
            self.start_urls.append(urls1)
        if self.res:
            for v in self.res:
                if not re.search(r'-',v['aid']):
                    urls1 = url % (v['aid'], sr, int(time.time()), sr, v['aid'])
                    self.start_urls.append(urls1)

    def parse(self, response):
        res_asin = response.url.split('/')
        asin_id = res_asin[4]
        item = ListingsItem()
        item['title'] = response.css('span#productTitle::text').extract_first()
        if not item['title']:
            item['title'] = response.css('div#titleSection span#productTitle::text').extract_first()
        print('Title is:%s' % item['title'])
        if item['title']:
            for val in self.res:
                if val['aid'] == asin_id:
                    sku_res = UserAsins.objects.filter(aid=val['aid'])
                    item['sku'] = sku_res[0].sku
                    user_asin = UserAsins.objects.get(id=sku_res[0].id)
                    item['user_asin'] = user_asin
                    buy_box = sku_res[0].ownership


            item['title'] = item['title'].replace('\n','').strip()
            item['asin'] = asin_id
            item['answered'] = ''
            qac = response.css('a.askATFLink span::text').extract_first()
            if qac:
                item['answered'] = qac.replace('\n','').strip().split(' answered')[0]
            item['brand'] = response.css('a#brand::text').extract_first()
            if not item['brand']:
                item['brand'] = response.css('div#bylineInfo_feature_div a#bylineInfo::text').extract_first()
            item['brand'] = item['brand'].replace('\n','').strip()
            item['shipping'] = response.css('span#price-shipping-message b::text').extract_first()
            if not item['shipping']:
                item['shipping'] = response.css('a#creturns-policy-anchor-text::text').extract_first()
            if item['shipping']:
                item['shipping'] = item['shipping'].replace('\n','').strip()
            else:
                item['shipping'] = ''
            prime = response.css('span#primeUpsellPopover i').extract_first()
            if prime:
                item['prime'] = 1
            item['feature'] = ''
            des_li = response.css('div#feature-bullets li span.a-list-item::text').extract()
            if des_li:
                for val in des_li:
                    val = re.sub(r"\n|\t",'',val)
                    item['feature'] += val + '\n'

            des_res = re.sub("\n", ",",
                              response.css("div#productDescription").xpath("string(p)").extract_first(default="").strip())
            item['description'] = des_res

            item['buy_box_res'] = []
            buyBoxs = response.css('#merchant-info a::text').extract()
            buyBox_link = response.css('#merchant-info a::attr(href)').extract()
            if buyBox_link:
                item['buy_box_link'] = 'https://www.amazon.com%s' % buyBox_link[0]
            if not buyBoxs:
                buyBoxs = re.sub("\n", ",",
                              response.css("div#availability-brief").xpath("string(span[2])").extract_first(default="").strip())
                if buyBoxs:
                    a = buyBoxs.split('sold by')
                    if len(a)>2:
                        buyBoxs = a[1].split('and')
            if buyBoxs:
                for v in buyBoxs:
                    item['buy_box_res'].append(v)
            if 'Brandline' in item['buy_box_res']:
                item['buy_box'] = 'Ours'
            else:
                item['buy_box'] = 'Others'
            item['price'] = response.css('tr#priceblock_ourprice_row span#priceblock_ourprice::text').extract_first()
            if not item['price']:
                item['price'] = response.css('tr#priceblock_dealprice_row span#priceblock_dealprice::text').extract_first()

            review = response.css('span#acrCustomerReviewText::text').extract_first()
            item['total_review'] = 0
            if review:
                item['total_review'] = review.split(' ')[0].replace(',','')
            qa = response.css('a#askATFLink span::text').extract_first()
            item['total_qa'] = 0
            if qa:
                item['total_qa'] = qa.replace('\n','').strip().split(' ')[0].replace(',','')
            score = response.css('span#acrPopover::attr("title")').extract_first()
            item['rvw_score'] = 0
            if score:
                item['rvw_score'] = score.split(' ')[0]
            category_rank1 = response.css('li#SalesRank::text').extract()
            category_rank2 = response.css('tr#SalesRank td.value::text').extract()
            item['category_rank'] = ''
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
            elif category_rank2:
                item['category_rank'] = category_rank2[0].replace('\n', '').split(' (')[0]
                rank_list = response.css('ul.zg_hrsr li.zg_hrsr_item')
                if rank_list:
                    rank_list_item = ''
                    for res in rank_list:
                        rank_list_item += '|' + res.css('span.zg_hrsr_rank::text').extract_first() + ' in '
                        for i, val in enumerate(res.css('a::text').extract(), 1):
                            if i == len(res.css('a::text').extract()):
                                rank_list_item += val
                            else:
                                rank_list_item += val + ' > '

                    item['category_rank'] = item['category_rank'] + rank_list_item
            else:
                th_el = response.css('table#productDetails_detailBullets_sections1 tr')
                if th_el:
                    for val in th_el:
                        th_str = val.css('th::text').extract_first()
                        if th_str and th_str.replace('\n', '').strip() == 'Best Sellers Rank':
                            rank_el = val.css('td span span::text').extract()
                            if rank_el:
                                item['category_rank'] = rank_el[0].split(' (')[0]
                                rank_span = val.css('td span span')
                                for n, rank_a in enumerate(rank_span, 0):
                                    if not n == 0:
                                        a = rank_a.css('a::text').extract()
                                        for s, val in enumerate(a, 1):
                                            if s == len(a):
                                                item['category_rank'] += val
                                            elif s == 1:
                                                item['category_rank'] += '|' + rank_el[2] + val + ' > '
                                            else:
                                                item['category_rank'] += val + ' > '

            item['inventory'] = 0
            item['image_urls'] = []
            img_el = response.css('div#altImages ul.a-unordered-list li.item')
            if not img_el:
                img_el = response.css('ol.a-carousel li.a-carousel-card')
                res = img_el[0].css('span.a-declarative img::attr("src")').extract_first()
            else:
                res = img_el[0].css('span.a-button-text img::attr("src")').extract_first()
            if res:
                name_res = os.path.basename(res).split('._')
                filename = name_res[0] + name_res[1].split('_')[-1]
                if not os.path.splitext(filename)[1] == '.png':
                    res = os.path.dirname(res) + '/' + filename
                    listing = Listings.objects.filter(asin=asin_id)
                    item['image_urls'].append(res)
                    if listing:
                        listing = listing.latest('created')
                        us = res.split('/')[3:]
                        image_file_name = '_'.join(us)
                        image_file_name = image_file_name.replace('%2','')
                        if not os.path.basename(listing.image_names) == image_file_name:
                            item['image_date'] = time.strftime('%Y-%m-%d',time.localtime(time.time()))
                        else:
                            item['image_date'] = listing.image_date
                    else:
                        item['image_date'] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            with_deal1 = response.css('tr#priceblock_dealprice_row td.a-span12 span::text').extract_first()
            with_deal2 = response.css('tr#priceblock_dealprice_row a#creturns-policy-anchor-text::text').extract_first()
            item['lightning_deal'] = ''
            if with_deal1:
                item['lightning_deal'] += with_deal1
                if with_deal2:
                    item['lightning_deal'] += '&'+with_deal2.replace('\n', '').strip()
            deal = response.css('div#deal_availability span::text').extract()
            if deal:
                deals = ''
                for v in deal:
                    deals += v
                item['lightning_deal'] += deals

            promotion = response.css('div#quickPromoBucketContent li::text').extract()
            if promotion:
                promotions = ''
                for v in promotion:
                    if v.replace('\n','').strip():
                        promotions += v
                if promotions:
                    item['promotion'] = promotions
            yield item
            res = UserAsins.objects.filter(aid=asin_id)
            if res:
                res.update(is_done=1,listing_time=datetime.datetime.now())


