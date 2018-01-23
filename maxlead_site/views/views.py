import os,sched
from datetime import *
import time,re
from django.db.models import Count
from django.shortcuts import render
from maxlead_site.models import UserAsins,AsinReviews,Reviews
from maxlead import settings
from maxlead_site.common.user_secuirty import UserSecuirty
from maxlead_site.common.npextractor import NPExtractor
from django.http import HttpResponseRedirect

# 第一个参数确定任务的时间，返回从某个特定的时间到现在经历的秒数
# 第二个参数以某种人为的方式衡量时间
schedule = sched.scheduler(time.time, time.sleep)

def update_kewords(aid = ''):
    review_time = settings.REVIEW_TIME+300
    schedule.enter(review_time, 0, update_kewords)

    aid_list = UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid'))
    positive_keywords = {}
    negative_keywords = {}
    if aid:
        review_contents = Reviews.objects.filter(asin=aid).filter(created=date.today()).filter(
            score__gte=3).values('content')
        nega_review_contents = Reviews.objects.filter(asin=aid).filter(created=date.today()).exclude(
            score__gte=3).values('content')
        asin_reviews = AsinReviews.objects.filter(aid=aid).filter(created=date.today()).all()
        if asin_reviews:
            if review_contents:
                review_contents = list(review_contents)
            posi_text = ''
            nega_text = ''
            for posi in review_contents:
                if posi['content']:
                    posi_text += posi['content'] + '\n'
            for nega in nega_review_contents:
                if nega['content']:
                    nega_text += nega['content'] + '\n'
            posi_obj = NPExtractor(posi_text)
            nega_obj = NPExtractor(nega_text)
            posi_line = posi_obj.extract()
            nega_line = nega_obj.extract()
            if posi_obj:
                for val in set(posi_line):
                    i = posi_text.count(val)
                    if i >= 2:
                        positive_keywords.update({i: val})
            if nega_line:
                for val in set(nega_line):
                    n = nega_text.count(val)
                    if n >= 2:
                        negative_keywords.update({n: val})
            if positive_keywords:
                asin_reviews.update(positive_keywords=str(positive_keywords))
            if negative_keywords:
                asin_reviews.update(negative_keywords=str(negative_keywords))
        return True

    for aid in list(aid_list):
        review_contents = Reviews.objects.filter(asin=aid['aid']).filter(created=date.today()).filter(
            score__gte=3).values('content')
        nega_review_contents = Reviews.objects.filter(asin=aid['aid']).filter(created=date.today()).exclude(
            score__gte=3).values('content')
        asin_reviews = AsinReviews.objects.filter(aid=aid['aid']).filter(created=date.today()).all()
        if asin_reviews:
            if review_contents:
                review_contents = list(review_contents)
            posi_text = ''
            nega_text = ''
            for posi in review_contents:
                if posi['content']:
                    posi_text += posi['content']+'\n'
            for nega in nega_review_contents:
                if nega['content']:
                    nega_text += nega['content']+'\n'
            posi_obj = NPExtractor(posi_text)
            nega_obj = NPExtractor(nega_text)
            posi_line = posi_obj.extract()
            nega_line = nega_obj.extract()
            if posi_obj:
                for val in set(posi_line):
                    i = posi_text.count(val)
                    if i >= 2:
                        positive_keywords.update({i:val})
            if nega_line:
                for val in set(nega_line):
                    n = nega_text.count(val)
                    if n >= 2:
                        negative_keywords.update({n:val})
            if positive_keywords:
                asin_reviews.update(positive_keywords=str(positive_keywords))
            if negative_keywords:
                asin_reviews.update(negative_keywords=str(negative_keywords))

def perform_command():
    # 安排inc秒后再次运行自己，即周期运行
    review_time = settings.REVIEW_TIME
    schedule.enter(review_time, 0, perform_command)

    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
    if res:
        for val in res:
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % \
                      val['aid']
            os.system(cmd_str)
        os.chdir(settings.ROOT_PATH)

def perform_command1():
    # 安排inc秒后再次运行自己，即周期运行
    s_time = settings.SPIDER_TIME
    schedule.enter(s_time, 0, perform_command1)

    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
    if res:
        for val in res:
            cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % \
                       val['aid']
            cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % \
                       val['aid']
            cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % \
                       val['aid']
            cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % \
                       val['aid']
            os.system(cmd_str1)
            os.system(cmd_str2)
            os.system(cmd_str3)
            os.system(cmd_str4)
        os.chdir(settings.ROOT_PATH)

def update_kewords1():
    aid_list = UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid'))
    positive_keywords = {}
    negative_keywords = {}
    for aid in list(aid_list):
        review_contents = Reviews.objects.filter(asin=aid['aid']).filter(created=date.today()).filter(
            score__gte=3).values('content')
        nega_review_contents = Reviews.objects.filter(asin=aid['aid']).filter(created=date.today()).exclude(
            score__gte=3).values('content')
        asin_reviews = AsinReviews.objects.filter(aid=aid['aid']).filter(created=date.today()).all()
        if asin_reviews:
            if review_contents:
                review_contents = list(review_contents)
            posi_text = ''
            nega_text = ''
            for posi in review_contents:
                if posi['content']:
                    posi_text += posi['content']+'\n'
            for nega in nega_review_contents:
                if nega['content']:
                    nega_text += nega['content']+'\n'
            posi_obj = NPExtractor(posi_text)
            nega_obj = NPExtractor(nega_text)
            posi_line = posi_obj.extract()
            nega_line = nega_obj.extract()
            if posi_obj:
                for val in set(posi_line):
                    i = posi_text.count(val)
                    if i >= 2:
                        positive_keywords.update({i:val})
            if nega_line:
                for val in set(nega_line):
                    n = nega_text.count(val)
                    if n >= 2:
                        negative_keywords.update({n:val})
            if positive_keywords:
                asin_reviews.update(positive_keywords=str(positive_keywords))
            if negative_keywords:
                asin_reviews.update(negative_keywords=str(negative_keywords))

def RunReview(request):
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.system('scrapyd-deploy')
    # enter用来安排某事件的发生时间，从现在起第n秒开始启动
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
    if res:
        for val in res:
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % val['aid']
            os.system(cmd_str)
    os.chdir(settings.ROOT_PATH)

    review_time = settings.REVIEW_TIME
    schedule.enter(review_time, 0, perform_command)
    # # 持续运行，直到计划时间队列变成空为止
    schedule.run()

    return render(request, 'spider/home.html')

def Spiders(request):
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.system('scrapyd-deploy')
    # enter用来安排某事件的发生时间，从现在起第n秒开始启动
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
    if res:
        for val in res:
            cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % \
                      val['aid']
            cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % \
                      val['aid']
            cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % \
                      val['aid']
            cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % \
                       val['aid']
            os.system(cmd_str1)
            os.system(cmd_str2)
            os.system(cmd_str3)
            os.system(cmd_str4)

    s_time = settings.SPIDER_TIME
    os.chdir(settings.ROOT_PATH)
    schedule.enter(s_time, 0, perform_command1)
    # # 持续运行，直到计划时间队列变成空为止
    schedule.run()

    return render(request, 'spider/home.html')

# RunReview = staff_member_required(RunReview)

class test(UserSecuirty):

    def __init__(self):
        UserSecuirty.user_secuity(self)


    def user_info(self):
        UserSecuirty.user_secuity(self)
        if self.user_info:
            url = '/admin/login/?next=/%s' % re.sub(r'https?://[^/]+?/','',self.get_raw_uri())
            return HttpResponseRedirect(url)

        return render(self, 'spider/home.html')

    # user_info = staff_member_required(user_info)

def test1(request):
    update_kewords()
    return render(request, 'spider/home.html')