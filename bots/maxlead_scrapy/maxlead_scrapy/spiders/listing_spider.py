# -*- coding: utf-8 -*-

import scrapy,time,os,re,datetime
import random
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bots.stockbot.stockbot import settings
from bots.maxlead_scrapy.maxlead_scrapy.items import ListingsItem
from maxlead_site.models import UserAsins,Listings
from django.db.models import Count
from django.utils import timezone
from maxlead_site.common.common import get_asins
from maxlead_site.models import UserProfile


class ListingSpider(scrapy.Spider):

    name = "listing_spider"
    start_urls = []
    res = []

    def __init__(self, asin=None, user=None, *args, **kwargs):
        sr = random.randint(1,16)
        url = "https://www.amazon.com/dp/%s/ref=sr_1_%s?ie=UTF8&qid=%d&sr=1-%s&keywords=%s&th=1&psc=1&aid=%s"
        super(ListingSpider, self).__init__(*args, **kwargs)
        if asin == '99':
            self.res = list(UserAsins.objects.filter(is_use=True, is_done=0).values('aid').annotate(count=Count('aid')))
        elif asin == '88':
            self.res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
        elif asin == '100':
            user = UserProfile.objects.get(user_id=int(user))
            aid_list = get_asins(user)
            self.res = list(UserAsins.objects.filter(is_use=True,aid__in=aid_list).exclude(listing_time__icontains=(datetime.
                                                        datetime.now()-datetime.timedelta(days=1)).strftime("%Y-%m-%d")).
                                                        exclude(listing_time__icontains=datetime.datetime.now().strftime("%Y-%m-%d")).
                                                        values('aid').annotate(count=Count('aid')))
        elif asin == '77':
            self.res =list( UserAsins.objects.values('aid').annotate(count=Count('aid')).filter(is_use=True, is_done=0))
        else:
            asin_li = asin.split(',')
            for v in asin_li:
                if v:
                    self.res.append({'aid':v})
        if self.res:
            time_str = int(time.time())
            for v in self.res:
                time_str += 1
                if not re.search(r'-',v['aid']):
                    urls1 = url % (v['aid'].strip(), sr, time_str, sr, v['aid'].strip(), v['aid'].strip())
                    self.start_urls.append(urls1)

    def parse(self, response):
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(800, 800))
        display.start()
        profile = webdriver.FirefoxProfile()
        profile.set_preference("permissions.default.image", 2)
        profile.set_preference("network.http.use-cache", False)
        profile.set_preference("browser.cache.memory.enable", False)
        profile.set_preference("browser.cache.disk.enable", False)
        profile.set_preference("browser.sessionhistory.max_total_viewers", 3)
        profile.set_preference("network.dns.disableIPv6", True)
        profile.set_preference("Content.notify.interval", 750000)
        profile.set_preference("content.notify.backoffcount", 3)
        profile.set_preference("network.http.pipelining", True)
        profile.set_preference("network.http.proxy.pipelining", True)
        profile.set_preference("network.http.pipelining.maxrequests", 32)

        firefox_options = Options()
        firefox_options.add_argument('-headless')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(firefox_options=firefox_options, executable_path=settings.FIREFOX_PATH,
                                   firefox_profile=profile)
        driver.get(response.url)
        driver.implicitly_wait(100)
        time.sleep(3)
        res_asin = response.url.split('/')
        asin_id = res_asin[4]
        item = ListingsItem()
        title = driver.find_elements_by_id('productTitle')
        if title:
            item['title'] = title[0].text
            sku_res = UserAsins.objects.filter(aid=asin_id)
            item['sku'] = sku_res[0].sku
            item['user_asin'] = sku_res[0]
            buy_box = sku_res[0].ownership
            item['title'] = item['title'].replace('\n', '').strip()
            item['asin'] = asin_id
            item['answered'] = ''
            qac = driver.find_elements_by_css_selector('.askATFLink span')
            if qac:
                item['answered'] = qac[0].text.replace('\n', '').strip().split(' answered')[0]
            brand = driver.find_elements_by_id('brand')
            if not brand:
                brand = driver.find_elements_by_id('bylineInfo')
            if brand:
                item['brand'] = brand[0].text.replace('\n', '').strip()
            shipping = driver.find_elements_by_css_selector('#price-shipping-message b')
            if not shipping:
                item['shipping'] = driver.find_elements_by_id('creturns-policy-anchor-text')
            if shipping:
                item['shipping'] = shipping[0].text.replace('\n', '').strip()
            else:
                item['shipping'] = ''
            prime = driver.find_elements_by_css_selector('#primeUpsellPopover i')
            if prime:
                item['prime'] = 1
            item['feature'] = ''
            des_li = driver.find_elements_by_css_selector('#feature-bullets li .a-list-item')
            if des_li:
                for val in des_li:
                    val = re.sub(r"\n|\t", '', val.text)
                    item['feature'] += val + '\n'

            des_res = driver.find_elements_by_id("productDescription")
            if des_res:
                des_res = re.sub("\n", ",", driver.find_element_by_css_selector("#productDescription p").text.strip())
                item['description'] = des_res

            item['buy_box_res'] = []
            buyBoxs = driver.find_elements_by_css_selector('#merchant-info a')
            if buyBoxs:
                item['buy_box_link'] = 'https://www.amazon.com%s' % buyBoxs[0].get_attribute('href')
            if not buyBoxs:
                buyBoxs = driver.find_elements_by_css_selector("#availability-brief span")
                if buyBoxs:
                    buyBoxs = re.sub("\n", ",", buyBoxs[2].text.strip())
                    a = buyBoxs.split('sold by')
                    if len(a) > 2:
                        buyBoxs = a[1].split('and')
            if buyBoxs:
                for v in buyBoxs:
                    item['buy_box_res'].append(v.text)
            if 'Brandline' in item['buy_box_res']:
                item['buy_box'] = 'Ours'
            else:
                item['buy_box'] = 'Others'
            price = driver.find_elements_by_css_selector('#priceblock_ourprice_row #priceblock_ourprice')
            if not price:
                price = driver.find_elements_by_css_selector('#priceblock_dealprice_row #priceblock_dealprice')
            if price:
                item['price'] = price[0].text

            review = driver.find_elements_by_id('acrCustomerReviewText')
            item['total_review'] = 0
            if review:
                item['total_review'] = review[0].text.split(' ')[0].replace(',', '')
            qa = driver.find_elements_by_css_selector('#askATFLink span')
            item['total_qa'] = 0
            if qa:
                item['total_qa'] = qa[0].text.replace('\n', '').strip().split(' ')[0].replace(',', '')
            score = driver.find_elements_by_id('acrPopover')
            item['rvw_score'] = 0
            if score:
                item['rvw_score'] = score[0].get_attribute("title").split(' ')[0]
            category_rank1 = driver.find_elements_by_id('SalesRank')
            category_rank2 = driver.find_elements_by_css_selector('#SalesRank .value')
            item['category_rank'] = ''
            if category_rank1:
                item['category_rank'] = category_rank1[1].text.replace('\n', '').split(' (')[0]
                rank_list = driver.find_elements_by_css_selector('.zg_hrsr .zg_hrsr_item')
                if rank_list:
                    rank_list_item = ''
                    for res in rank_list:
                        rank_list_item += '|' + res.find_element_by_class_name('zg_hrsr_rank').text + ' in '
                        for i, val in enumerate(res.find_elements_by_tag_name('a'), 1):
                            if i == len(res.find_elements_by_tag_name('a')):
                                rank_list_item += val.text
                            else:
                                rank_list_item += val.text + ' > '

                    item['category_rank'] = item['category_rank'] + rank_list_item
            elif category_rank2:
                item['category_rank'] = category_rank2[0].text.replace('\n', '').split(' (')[0]
                rank_list = driver.find_elements_by_css_selector('.zg_hrsr .zg_hrsr_item')
                if rank_list:
                    rank_list_item = ''
                    for res in rank_list:
                        rank_list_item += '|' + res.find_element_by_tag_name('zg_hrsr_rank').text + ' in '
                        for i, val in enumerate(res.find_elements_by_tag_name('a'), 1):
                            if i == len(res.find_elements_by_tag_name('a')):
                                rank_list_item += val.text
                            else:
                                rank_list_item += val.text + ' > '

                    item['category_rank'] = item['category_rank'] + rank_list_item
            else:
                th_el = driver.find_elements_by_css_selector('#productDetails_detailBullets_sections1 tr')
                if th_el:
                    for val in th_el:
                        th_str = val.find_element_by_tag_name('th').text
                        if th_str and th_str.replace('\n', '').strip() == 'Best Sellers Rank':
                            rank_el = val.find_elements_by_css_selector('td span span')
                            if rank_el:
                                item['category_rank'] = rank_el[0].text.split(' (')[0]
                                rank_span = val.find_elements_by_css_selector('td span span')
                                for n, rank_a in enumerate(rank_span, 0):
                                    if not n == 0:
                                        a = rank_a.find_elements_by_tag_name('a')
                                        for s, val in enumerate(a, 1):
                                            if s == len(a):
                                                item['category_rank'] += val.text
                                            elif s == 1:
                                                item['category_rank'] += '|' + rank_el[2] + val.text + ' > '
                                            else:
                                                item['category_rank'] += val.text + ' > '

            item['inventory'] = 0
            item['image_urls'] = []
            img_el = driver.find_elements_by_css_selector('#altImages .a-unordered-list .item')
            if not img_el:
                img_el = driver.find_elements_by_css_selector('.a-carousel .a-carousel-card')
                res = img_el[0].find_element_by_css_selector('.a-declarative img').get_attribute('src')
            else:
                res = img_el[0].find_element_by_css_selector('.a-button-text img').get_attribute('src')
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
                        image_file_name = image_file_name.replace('%2', '')
                        if not os.path.basename(listing.image_names) == image_file_name:
                            item['image_date'] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                        else:
                            item['image_date'] = listing.image_date
                    else:
                        item['image_date'] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            with_deal1 = driver.find_elements_by_css_selector('#priceblock_dealprice_row .a-span12 span')
            with_deal2 = driver.find_elements_by_css_selector('#priceblock_dealprice_row #creturns-policy-anchor-text')
            item['lightning_deal'] = ''
            if with_deal1:
                item['lightning_deal'] += with_deal1[0].text
                if with_deal2:
                    item['lightning_deal'] += '&' + with_deal2[0].text.replace('\n', '').strip()
            deal = driver.find_elements_by_css_selector('#deal_availability span')
            if deal:
                deals = ''
                for v in deal:
                    deals += v.text
                item['lightning_deal'] += deals

            promotion = driver.find_elements_by_css_selector('#quickPromoBucketContent li')
            if promotion:
                promotions = ''
                for v in promotion:
                    promotions += v.text.replace('\n', '').strip()
                if promotions:
                    item['promotion'] = promotions
            yield item
            res = UserAsins.objects.filter(aid=asin_id)
            if res:
                res.update(is_done=1, listing_time=timezone.now())
        driver.close()
        display.stop()
