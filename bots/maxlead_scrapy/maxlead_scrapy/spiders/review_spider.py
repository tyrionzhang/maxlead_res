# -*- coding: utf-8 -*-

import scrapy,time,datetime
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
        urls = "https://www.amazon.com/product-reviews/%s/ref=cm_cr_dp_d_show_all_top?ie=UTF8&reviewerType=all_reviews&th=1&psc=1&qid=%s&aid=%s"
        super(ReviewSpider, self).__init__(*args, **kwargs)
        time_str = int(time.time())
        if asin == '88':
            res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
            if res:
                for re in list(res):
                    time_str += 1
                    asin = urls % (re['aid'].strip(), time_str, re['aid'].strip())
                    self.start_urls.append(asin)
        elif asin == '77':
            self.res =list( UserAsins.objects.values('aid').annotate(count=Count('aid')).filter(is_use=True, is_done=0))
            if self.res:
                for v in self.res:
                    time_str += 1
                    urls1 = urls % (v['aid'].strip(), time_str, v['aid'].strip())
                    self.start_urls.append(urls1)
        else:
            asin_li = asin.split(',')
            for v in asin_li:
                if v:
                    time_str += 1
                    urls1 = urls % (v.strip(), time_str, v.strip())
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
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(800, 800))
        display.start()
        chrome_options = Options()
        chrome_options.add_argument('-headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=settings.CHROME_PATH,
                                  service_log_path=settings.LOG_PATH)
        driver.get(response.url)
        driver.implicitly_wait(100)
        next_page = driver.find_elements_by_css_selector('.a-last a')
        check_next = 0
        while next_page:
            if check_next == 1:
                # next_page[0].click()
                next_page = next_page[0].get_attribute('href')
                self.asin_id = next_page.split('/')[5][0:10]
                next_page = next_page + '&mytype=maxlead'
                driver.get(next_page)
                driver.implicitly_wait(100)
                next_page = driver.find_elements_by_css_selector('.a-last a')
            check_next = 1

            req_res = driver.find_elements_by_css_selector('#cm_cr-review_list .review')
            if check:
                item = AsinReviewsItem()
                item['aid'] = asin_id
                item['avg_score'] = 0
                item['avg_score'] = driver.find_elements_by_css_selector('.averageStarRatingNumerical .arp-rating-out-of-text')
                if not item['avg_score']:
                    item['avg_score'] = driver.find_elements_by_css_selector('.averageStarRating span')
                if item['avg_score']:
                    item['avg_score'] = item['avg_score'][0].text[0: 3]
                item['total_review'] = 0
                item['total_review'] = driver.find_elements_by_css_selector('.averageStarRatingIconAndCount .totalReviewCount')

                if not item['total_review']:
                    item['total_review'] = driver.find_elements_by_css_selector('.totalReviewCount')
                if item['total_review']:
                    item['total_review'] = item['total_review'][0].text.replace(',','')
                yield item
            for review in req_res:
                item = ReviewsItem()
                item['name'] = review.find_elements_by_css_selector('.a-profile-content .a-profile-name')[0].text
                item['asin'] = asin_id
                item['title'] = review.find_elements_by_css_selector('.review-title')[0].text
                item['content'] = review.find_elements_by_css_selector('.review-text')[0].text
                item['review_link'] = "https://www.amazon.com" + review.find_elements_by_css_selector('.review-title')[0].get_attribute('href')
                item['score'] = review.find_elements_by_css_selector('.a-link-normal')[0].get_attribute('title')[0:1]
                item['variation'] = review.find_elements_by_css_selector('.review-format-strip .cr-widget-AsinVariation')
                if not item['variation']:
                    item['variation'] = review.find_elements_by_css_selector('.review-format-strip .a-color-secondary')
                if item['variation']:
                    item['variation'] = item['variation'][0].text.replace('\n','')
                item['image_urls'] = []
                for img_re in review.find_elements_by_css_selector('.review-image-container .review-image-tile'):
                    item['image_urls'].append(img_re.get_attribute('src'))

                vp = review.find_elements_by_css_selector('.review-format-strip .a-link-normal span')
                if not vp:
                    vp = review.find_elements_by_css_selector('.review-format-strip .a-declarative span')
                if vp is not None and vp[0].text == 'Verified Purchase':
                    item['is_vp'] = 1
                else:
                    item['is_vp'] = 0
                try:
                    review_date = time.strptime(review.find_elements_by_css_selector('.review-date')[0].text[3:40],"%B %d, %Y")
                except:
                    review_date = time.strptime(review.find_elements_by_css_selector('.review-date')[0].text, "%B %d, %Y")
                item['review_date'] = time.strftime("%Y-%m-%d", review_date)
                yield item
        else:
            re = AsinReviews.objects.filter(aid=asin_id,created__icontains=datetime.datetime.now().strftime('%Y-%m-%d'))
            if re:
                re.update(is_done=1)
        display.stop()
        driver.quit()

    def parse_details(self, response):
        item = response.meta.get('item', None)
        if item:
            # populate more `item` fields
            return item
        else:
            self.log('No item received for %s' % response.url,
                     level=log.WARNING)