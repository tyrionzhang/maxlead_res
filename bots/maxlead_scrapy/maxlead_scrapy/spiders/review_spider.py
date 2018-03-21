# -*- coding: utf-8 -*-

import scrapy,time,datetime
from bots.maxlead_scrapy.maxlead_scrapy.items import AsinReviewsItem,ReviewsItem
from maxlead_site.models import UserAsins,AsinReviews
from scrapy import log
from django.db.models import Count


class ReviewSpider(scrapy.Spider):

    name = "review_spider"
    start_urls = []
    asin_id = ''

    def __init__(self, asin=None, *args, **kwargs):
        urls = "https://www.amazon.com/product-reviews/%s/ref=cm_cr_dp_d_show_all_top?ie=UTF8&reviewerType=all_reviews&th=1&psc=1"
        super(ReviewSpider, self).__init__(*args, **kwargs)
        if asin == '88':
            res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
            if res:
                for re in list(res):
                    asin = urls % re['aid']
                    self.start_urls.append(asin)
        else:
            urls1 = urls % asin
            self.start_urls.append(urls1)

    def parse(self, response):
        str = response.url[-7:]
        res_asin = response.url.split('/')
        if str == 'maxlead':
            asin_id = self.asin_id
            check = 0
        else:
            check = 1
            asin_id = res_asin[4]
        req_res = response.css('div#cm_cr-review_list div.review')
        if check:
            item = AsinReviewsItem()
            item['aid'] = asin_id
            item['avg_score'] = response.css('div.averageStarRatingNumerical span.arp-rating-out-of-text::text').extract_first()
            if not item['avg_score']:
                item['avg_score'] = response.css('i.averageStarRating span::text').extract_first()
            if item['avg_score']:
                item['avg_score'] = item['avg_score'][0: 3]
            item['total_review'] = response.css('div.averageStarRatingIconAndCount span.totalReviewCount::text').extract_first()

            if not item['total_review']:
                item['total_review'] = response.css('span.totalReviewCount::text').extract_first()
            if item['total_review']:
                item['total_review'] = item['total_review'].replace(',','')
            yield item
        for review in req_res:
            item = ReviewsItem()
            item['name'] = review.css('span.review-byline a.author::text').extract_first()
            item['asin'] = asin_id
            item['title'] = review.css('a.review-title::text').extract_first()
            item['content'] = review.css('span.review-text::text').extract_first()
            item['review_link'] = "https://www.amazon.com" + review.css('a.review-title::attr("href")').extract_first()
            item['score'] = review.css('i.review-rating span::text').extract_first()[0:1]
            item['variation'] = review.css('div.review-format-strip a.a-color-secondary::text').extract_first()
            item['image_urls'] = []
            for img_re in review.css('div.review-image-container img.review-image-tile::attr("data-src")').extract():
                item['image_urls'].append(img_re)

            vp = review.css('div.review-format-strip .a-link-normal span::text').extract_first()
            if vp is not None and vp == 'Verified Purchase':
                item['is_vp'] = 1
            else:
                item['is_vp'] = 0
            review_date = time.strptime(review.css('span.review-date::text').extract_first()[3:40],"%B %d, %Y")
            item['review_date'] = time.strftime("%Y-%m-%d", review_date)
            yield item

        next_page = response.css('li.a-last a::attr("href")').extract_first()
        if next_page is not None:
            self.asin_id = next_page.split('/')[3][0:10]
            next_page = next_page + '&mytype=maxlead'
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            re = AsinReviews.objects.filter(aid=asin_id,created__icontains=datetime.datetime.now().strftime('%Y-%m-%d'))
            if re:
                re.update(is_done=1)

    def parse_details(self, response):
        item = response.meta.get('item', None)
        if item:
            # populate more `item` fields
            return item
        else:
            self.log('No item received for %s' % response.url,
                     level=log.WARNING)