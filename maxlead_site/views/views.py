import os,sched
from datetime import *
import time
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from maxlead_site.models import UserAsins,AsinReviews,Reviews
from maxlead_site.views import commons
from maxlead import settings

# 第一个参数确定任务的时间，返回从某个特定的时间到现在经历的秒数
# 第二个参数以某种人为的方式衡量时间
schedule = sched.scheduler(time.time, time.sleep)

def update_kewords():
    review_time = settings.REVIEW_TIME+300
    schedule.enter(review_time, 0, update_kewords)

    aid_list = UserAsins.objects.filter(is_use=True).values('aid')
    positive_keywords = ''
    negative_keywords = ''
    for aid in list(aid_list):
        review_contents = Reviews.objects.filter(asin=aid['aid']).filter(created=date.today()).filter(
            score__gte=3).values('content')
        nega_review_contents = Reviews.objects.filter(asin=aid['aid']).filter(created=date.today()).exclude(
            score__gte=3).values('content')
        asin_reviews = AsinReviews.objects.filter(aid=aid['aid']).filter(created=date.today()).all()
        if asin_reviews:
            if review_contents:
                review_contents = list(review_contents)
            posi_line_list = commons.get_diff_str(review_contents)
            nega_line_list = commons.get_diff_str(nega_review_contents)

            if posi_line_list:
                for posi in set(posi_line_list):
                    if posi_line_list.count(posi) >= 2:
                        positive_keywords += posi + '||'
            if nega_line_list:
                for nega in set(nega_line_list):
                    if nega_line_list.count(nega) >= 2:
                        negative_keywords += nega + '||'
            if positive_keywords:
                asin_reviews.update(positive_keywords=positive_keywords)
            if negative_keywords:
                asin_reviews.update(negative_keywords=negative_keywords)

def perform_command():
    # 安排inc秒后再次运行自己，即周期运行
    review_time = settings.REVIEW_TIME
    schedule.enter(review_time, 0, perform_command)

    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.system('curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider')


def RunReview(request):
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.system('scrapyd-deploy')
    # enter用来安排某事件的发生时间，从现在起第n秒开始启动
    perform_command()
    review_time = settings.REVIEW_TIME
    review_key = review_time+300
    schedule.enter(review_time, 0, perform_command)
    schedule.enter(review_key, 0, update_kewords)
    # 持续运行，直到计划时间队列变成空为止
    schedule.run()

    return render(request, 'spider/home.html')

RunReview = staff_member_required(RunReview)
