import os,sched
from datetime import *
import time
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from maxlead_site.models import UserAsins,AsinReviews,Reviews
from maxlead import settings

# 第一个参数确定任务的时间，返回从某个特定的时间到现在经历的秒数
# 第二个参数以某种人为的方式衡量时间
schedule = sched.scheduler(time.time, time.sleep)

# def RunReview(request):
    # work_path = settings.SPIDER_URL
    # os.chdir(work_path)  # 修改当前工作目录
    # os.system('scrapyd-deploy')
    # os.system('curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider')

    # aid_list = UserAsins.objects.filter(is_use=True).values('aid')
    # for aid in list(aid_list):
    #     review_contents = Reviews.objects.filter(asin=aid['aid']).filter(created=date.today()).values('content')
    #     asin_reviews = AsinReviews.objects.filter(aid=aid['aid']).filter(created=date.today()).all()
    #     if review_contents:
    #         review_contents = list(review_contents)
    #     for i, content in enumerate(review_contents,0):
    #         for k, con in enumerate(review_contents,0):
    #             if not i == k:
    #                 content_line = content['content'].splitlines()
    #                 con_line = con['content'].splitlines()
    #                 d = difflib.Differ()
    #                 diff = d.compare(content_line, con_line)
    #                 print(list(diff))
    #     pass
    # review_time = settings.REVIEW_TIME
    # run()
    # global t
    # t = Timer(300.0, RunReview(request))
    # t.start()

def perform_command():
    # 安排inc秒后再次运行自己，即周期运行
    review_time = settings.REVIEW_TIME
    schedule.enter(review_time, 0, perform_command)
    os.system('curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider')


def RunReview(request):
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.system('scrapyd-deploy')
    # enter用来安排某事件的发生时间，从现在起第n秒开始启动
    review_time = settings.REVIEW_TIME
    schedule.enter(review_time, 0, perform_command)
    # 持续运行，直到计划时间队列变成空为止
    schedule.run()
    return render(request, 'spider/home.html')

RunReview = staff_member_required(RunReview)
