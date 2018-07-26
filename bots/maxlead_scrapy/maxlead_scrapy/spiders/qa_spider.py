# -*- coding: utf-8 -*-

import scrapy,time,datetime
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from maxlead_site.models import UserAsins
from django.db.models import Count
from bots.maxlead_scrapy.maxlead_scrapy.items import AnswersItem
from maxlead_site.models import Questions
from bots.stockbot.stockbot import settings

class QaSpider(scrapy.Spider):

    name = "qa_spider"
    start_urls = []

    def __init__(self, asin=None, *args, **kwargs):
        urls = "https://www.amazon.com/ask/questions/asin/%s/?th=1&psc=1"
        super(QaSpider, self).__init__(*args, **kwargs)
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
        res_asin = response.url.split('/')
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
        next_page = driver.find_elements_by_css_selector('div#askPaginationBar li.a-last a')
        elem_qa = driver.find_elements_by_css_selector('div.askInlineWidget div.askTeaserQuestions>.a-spacing-base')
        for i in range(0, len(elem_qa)):
            elem_qa = driver.find_elements_by_css_selector('div.askInlineWidget div.askTeaserQuestions>.a-spacing-base')
            qa_a = elem_qa[i]
            qa_url = qa_a.find_element_by_css_selector('.a-spacing-base .a-link-normal')
            question = qa_a.find_element_by_css_selector('.a-spacing-base .a-link-normal').text.replace('\n','').strip()
            votes = int(qa_a.find_element_by_css_selector('ul.voteAjax span.count').text)
            count_el = driver.find_element_by_css_selector('div.askPaginationHeaderMessage span').text
            asin_id = res_asin[6]
            qa_data = Questions(question=question, asin=asin_id, votes=votes)
            qa_data.id
            if count_el:
                count = count_el.split('of ')
                qa_data.count = count[1].split(' ')[0]
            qa_data.save()

            qa_url.click()
            driver.implicitly_wait(100)
            qa_id = qa_data.id
            asked = driver.find_element_by_css_selector('div.a-spacing-base div.a-text-left').text
            qa_obj = Questions.objects.filter(id=qa_id)
            if asked:
                asked = asked.replace('\n', '').strip()
                qa_obj.update(asked=asked)
            for asw in driver.find_elements_by_css_selector('div.askAnswersAndComments>.a-section'):
                item = AnswersItem()
                item['person'] = asw.find_elements_by_class_name('a-color-tertiary')
                if item['person']:
                    item['person'] = item['person'][0].text.replace('\n', '').strip()
                item['answer'] = asw.find_element_by_css_selector('span').text
                item['question'] = list(qa_obj)[0]
                yield item
            driver.back()
            driver.implicitly_wait(30)

        if next_page:
            time.sleep(3 + random.randint(3, 9))
            yield scrapy.Request(next_page[0].get_attribute('href'), callback=self.parse)
        else:
            re = Questions.objects.filter(asin=res_asin[6],created__icontains=datetime.datetime.now().strftime('%Y-%m-%d'))
            if re:
                re.update(is_done=1)
        display.stop()
        driver.quit()
