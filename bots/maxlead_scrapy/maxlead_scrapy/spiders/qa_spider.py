# -*- coding: utf-8 -*-

import scrapy,time,datetime
import random
from maxlead_site.models import UserAsins
from django.db.models import Count
from bots.maxlead_scrapy.maxlead_scrapy.items import AnswersItem
from maxlead_site.models import Questions

class QaSpider(scrapy.Spider):

    name = "qa_spider"
    start_urls = []

    def __init__(self, asin=None, *args, **kwargs):
        urls = "https://www.amazon.com/ask/questions/asin/%s/?th=1&psc=1&qid=%s&aid=%s"
        super(QaSpider, self).__init__(*args, **kwargs)
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
                time_str += 1
                urls1 = urls % (v.strip() ,time_str, v.strip())
                self.start_urls.append(urls1)


    def parse(self, response):
        res_asin = response.url.split('/')
        for qa_a in response.css('div.askInlineWidget div.askTeaserQuestions>.a-spacing-base'):
            qa_url = qa_a.css('.a-spacing-base .a-link-normal::attr("href")').extract_first()
            question = qa_a.css('.a-spacing-base .a-link-normal::text').extract_first().replace('\n','').strip()
            votes = int(qa_a.css('ul.voteAjax span.count::text').extract_first())
            count_el = response.css('div.askPaginationHeaderMessage span::text').extract_first()
            asin_id = res_asin[6]
            qa_data = Questions(question=question, asin=asin_id, votes=votes)
            qa_data.id
            if count_el:
                count = count_el.split('of ')
                qa_data.count = count[1].split(' ')[0]
            qa_data.save()
            qa_url = qa_url + '?qa_id=%s' % qa_data.id
            qa_page = response.urljoin(qa_url)
            time.sleep(2)
            yield scrapy.Request(qa_page, callback=self.get_answer)

        next_page = response.css('div#askPaginationBar li.a-last a::attr("href")').extract_first()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            re = Questions.objects.filter(asin=res_asin[6],created__icontains=datetime.datetime.now().strftime('%Y-%m-%d'))
            if re:
                re.update(is_done=1)

    def get_answer(self,response):
        qa_sp = response.url.split('?')[-1]
        qa_id = qa_sp.split('=')[-1]
        asked = response.css('div.a-spacing-base div.a-text-left::text').extract_first()
        qa_obj = Questions.objects.filter(id=qa_id)
        if asked:
            asked = asked.replace('\n','').strip()
            qa_obj.update(asked=asked)
        for asw in response.css('div.askAnswersAndComments>.a-section'):
            item = AnswersItem()
            item['person'] = asw.css('span.a-color-tertiary::text').extract_first()
            if item['person']:
                item['person'] = item['person'].replace('\n','').strip()
            item['answer'] = asw.css('span::text').extract_first()
            item['question'] = list(qa_obj)[0]
            yield item