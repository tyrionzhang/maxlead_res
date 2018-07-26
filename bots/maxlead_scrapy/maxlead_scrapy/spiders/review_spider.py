# -*- coding: utf-8 -*-

import scrapy,time,datetime
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bots.maxlead_scrapy.maxlead_scrapy.items import AsinReviewsItem,ReviewsItem
from maxlead_site.models import UserAsins,AsinReviews
from scrapy import log
from django.db.models import Count
from bots.stockbot.stockbot import settings


class ReviewSpider(scrapy.Spider):

    name = "review_spider"
    start_urls = []
    asin_id = ''

    def __init__(self, asin=None, *args, **kwargs):
        urls = "https://www.amazon.com/product-reviews/%s/ref=cm_cr_dp_d_show_all_top?ie=UTF8&reviewerType=all_reviews&pageSize=50&th=1&psc=1"
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
        # from pyvirtualdisplay import Display
        # display = Display(visible=0, size=(800, 800))
        # display.start()
        chrome_options = Options()
        chrome_options.add_argument('-headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(response.url)
        driver.implicitly_wait(100)
        next_page = driver.find_elements_by_css_selector('li.a-last a')
        req_res = driver.find_elements_by_css_selector('div#cm_cr-review_list div.review')
        if check:
            item = AsinReviewsItem()
            item['aid'] = asin_id
            item['avg_score'] = 0
            avg_score = driver.find_elements_by_css_selector('div.averageStarRatingNumerical span.arp-rating-out-of-text')
            if not avg_score:
                avg_score = driver.find_elements_by_css_selector('i.averageStarRating span')
            if avg_score:
                item['avg_score'] = avg_score[0].text[0: 3]
            total_review = driver.find_elements_by_css_selector('div.averageStarRatingIconAndCount span.totalReviewCount')
            if not total_review:
                total_review = driver.find_elements_by_class_name('totalReviewCount')
            if total_review:
                item['total_review'] = total_review[0].text.replace(',','')
            yield item
        for i in range(0, len(req_res)):
            driver.get(response.url)
            driver.implicitly_wait(100)
            elem_req = driver.find_elements_by_css_selector('div#cm_cr-review_list div.review')
            review = elem_req[i]
            item = ReviewsItem()
            item['name'] =  review.find_element_by_css_selector('span.review-byline a.author').text
            item['asin'] = asin_id
            item['title'] = review.find_element_by_class_name('review-title').text
            item['content'] = review.find_element_by_class_name('review-text').text
            item['review_link'] = review.find_element_by_class_name('review-title').get_attribute('href')
            item['score'] = review.find_element_by_xpath(".//*[@class='a-link-normal']").get_attribute('title')[0:1]
            variation = review.find_elements_by_css_selector('div.review-format-strip a.a-color-secondary')
            if variation:
                item['variation'] = variation[0].text
            item['image_urls'] = []
            imgs = review.find_elements_by_css_selector('div.review-image-container img.review-image-tile')
            if imgs:
                for img_re in imgs:
                    item['image_urls'].append(img_re.get_attribute('src'))

            vp = review.find_element_by_css_selector('div.review-format-strip .a-link-normal span').text
            if vp is not None and vp == 'Verified Purchase':
                item['is_vp'] = 1
            else:
                item['is_vp'] = 0
            review_date = time.strptime(review.find_element_by_class_name('review-date').text[3:40],"%B %d, %Y")
            item['review_date'] = time.strftime("%Y-%m-%d", review_date)
            yield item

        if next_page:
            next_page = next_page[0].get_attribute('href')
            time.sleep(3 + random.randint(3, 9))
            self.asin_id = next_page.split('/')[3][0:10]
            next_page = next_page + '&mytype=maxlead'
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            re = AsinReviews.objects.filter(aid=asin_id,created__icontains=datetime.datetime.now().strftime('%Y-%m-%d'))
            if re:
                re.update(is_done=1)
        # display.stop()
        driver.quit()

    def parse_details(self, response):
        item = response.meta.get('item', None)
        if item:
            # populate more `item` fields
            return item
        else:
            self.log('No item received for %s' % response.url,
                     level=log.WARNING)