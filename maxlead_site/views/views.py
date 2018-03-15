import os,sched
from datetime import *
import time,re
from django.db.models import Count
from django.shortcuts import render
from maxlead_site.models import UserAsins
from maxlead import settings
from maxlead_site.common.user_secuirty import UserSecuirty
from maxlead_site.common.excel_world import read_csv_file
import queue
import math
import threading
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.http import HttpResponse

# 第一个参数确定任务的时间，返回从某个特定的时间到现在经历的秒数
# 第二个参数以某种人为的方式衡量时间
schedule = sched.scheduler(time.time, time.sleep)

def perform_command():
    # 安排inc秒后再次运行自己，即周期运行
    review_time = settings.REVIEW_TIME
    schedule.enter(review_time, 0, perform_command)

    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
    if res:
        for i,val in enumerate(res,1):
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % \
                      val['aid']
            os.popen(cmd_str)
        os.chdir(settings.ROOT_PATH)
    return True

def perform_command1():
    # 安排inc秒后再次运行自己，即周期运行
    s_time = settings.SPIDER_TIME
    schedule.enter(s_time, 0, perform_command1)

    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
    if res:
        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % 88
        os.popen(cmd_str1)
        for i,val in enumerate(res,1):
            cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % \
                       val['aid']
            cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % \
                       val['aid']
            cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % \
                       val['aid']
            os.popen(cmd_str2)
            os.popen(cmd_str3)
            os.popen(cmd_str4)
        os.chdir(settings.ROOT_PATH)
    return True

def get_asin_spiders():
    schedule.enter(86400, 0, get_asin_spiders)
    print(datetime.now())
    listing_aid = UserAsins.objects.filter(is_use=1,listing_time__lt=datetime.now().strftime('%Y-%m-%d'))
    qa_aid = UserAsins.objects.filter(is_use=1,qa_time__lt=datetime.now().strftime('%Y-%m-%d'))
    review_aid = UserAsins.objects.filter(is_use=1,review_time__lt=datetime.now().strftime('%Y-%m-%d'))
    wa_aid = UserAsins.objects.filter(is_use=1,watcher_time__lt=datetime.now().strftime('%Y-%m-%d'))
    catr_aid = UserAsins.objects.filter(is_use=1,catrank_time__lt=datetime.now().strftime('%Y-%m-%d'))
    if listing_aid:
        for asin in listing_aid:
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % asin.aid
            os.popen(cmd_str)
    if qa_aid:
        for asin in qa_aid:
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % asin.aid
            os.popen(cmd_str)
    if review_aid:
        for asin in review_aid:
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % asin.aid
            os.popen(cmd_str)
    if wa_aid:
        for asin in wa_aid:
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % asin.aid
            os.popen(cmd_str)
    if catr_aid:
        for asin in catr_aid:
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % asin.aid
            os.popen(cmd_str)
    return True

def Spiders2(request):
    s_time = settings.SPIDER_TIME
    review_time = settings.REVIEW_TIME
    schedule.enter(review_time, 0, perform_command)
    schedule.enter(s_time, 0, perform_command1)
    # schedule.enter(3600, 0, get_asin_spiders)
    # # 持续运行，直到计划时间队列变成空为止
    print('Spiders is runing!Time:%s' % datetime.now())
    schedule.run()


    return render(request, 'spider/home.html')

def Spiders(request):
    schedule.enter(1, 0, get_asin_spiders)
    # # 持续运行，直到计划时间队列变成空为止
    schedule.run()

    return render(request, 'spider/home.html')

def Spiders1(request):
    perform_command2()
    return render(request, 'spider/home.html')


def perform_command2():
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
    if res:
        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % 88
        os.popen(cmd_str1)
        for i,val in enumerate(res,1):
            cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % \
                       val['aid']
            cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % \
                       val['aid']
            cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % \
                       val['aid']
            os.popen(cmd_str2)
            os.popen(cmd_str3)
            os.popen(cmd_str4)
        os.chdir(settings.ROOT_PATH)
    return True

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
    try:
        real_ip = request.META['HTTP_X_FORWARDED_FOR']
        regip = real_ip.split(",")[0]
    except:
        try:
            regip = request.META['REMOTE_ADDR']
        except:
            regip = ""
    regip += '<br>%s' % request.META.get('HTTP_USER_AGENT')

    print(regip)
    return HttpResponse(regip)

def export_users(request):
    re = read_csv_file('/home/techsupp/www/staffx.csv')
    return HttpResponse(re['msg'])

def letsencrpyt(request,token_value):
    with open('/home/techsupp/www/.well-known/acme-challenge/{}'.format(token_value)) as f:
        answer = f.readline().strip()
    return answer

def qu_spiders(asins):
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    if asins:
        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % asins
        os.popen(cmd_str1)
        for i, val in asins.split('|'):
            cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % \
                       val
            cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % \
                       val
            cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % \
                       val
            os.popen(cmd_str2)
            os.popen(cmd_str3)
            os.popen(cmd_str4)

    return

def qu_review_spiders(asins):
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    if asins:
        for i, val in asins.split('|'):
            cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % \
                       val
            os.popen(cmd_str2)
    return

def que_to():
    q = queue.PriorityQueue()
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
    total_count = len(res)
    total_page = math.ceil(total_count / 10)
    paginator = Paginator(res, 10)

    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    for page in range(total_page):
        data = paginator.page(page + 1)
        asins = ''
        for k,aid in enumerate(data,1):
            if k == len(data):
                asins+=aid['aid']
            else:
                asins+=aid['aid']+'|'
        q.put(qu_spiders(asins))
        q.put(qu_review_spiders(asins))
    os.chdir(settings.ROOT_PATH)

    workers = [threading.Thread(target=process_job, args=(q,)),
               threading.Thread(target=process_job, args=(q,))]

    for w in workers:
        w.setDaemon(True)
        w.start()

    q.join()

def process_job(q):
    while True:
        q.get()
        q.task_done()

def QuSpiders(request):
    schedule.enter(1, 0, que_to)
    # # 持续运行，直到计划时间队列变成空为止
    schedule.run()

    return render(request, 'spider/home.html')

def perform_command3():
    s_time = settings.SPIDER_TIME
    schedule.enter(s_time, 0, perform_command3)
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % 88
    os.popen(cmd_str)
    cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % 88
    os.popen(cmd_str1)
    cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % 88
    cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % 88
    cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % 88
    os.popen(cmd_str2)
    os.popen(cmd_str3)
    os.popen(cmd_str4)
    os.chdir(settings.ROOT_PATH)
    return True

def Spiders3(request):
    schedule.enter(1, 0, perform_command3)
    # # 持续运行，直到计划时间队列变成空为止
    schedule.run()

    return render(request, 'spider/home.html')
