import os,sched
from datetime import *
import time,re
from django.db.models import Count
from django.shortcuts import render
from maxlead_site.models import UserAsins,UserProfile
from maxlead import settings
from maxlead_site.common.user_secuirty import UserSecuirty
from maxlead_site.common.excel_world import read_csv_file
from maxlead_site.common.common import get_asins
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
    schedule.enter(3600, 0, get_asin_spiders)
    print(datetime.now())
    user = UserProfile.objects.get(user_id=1)
    asins = get_asins(user, status=1, type=1, is_done=1)
    if asins:
        work_path = settings.SPIDER_URL
        os.chdir(work_path)
        os.popen('scrapyd-deploy')
        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % 99
        os.popen(cmd_str1)
        for i, val in enumerate(asins, 1):
            cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % val
            cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % val
            cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % val
            cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % val
            os.popen(cmd_str)
            os.popen(cmd_str2)
            os.popen(cmd_str3)
            os.popen(cmd_str4)
        os.chdir(settings.ROOT_PATH)
    return True

def Spiders2(request):
    s_time = settings.SPIDER_TIME
    review_time = settings.REVIEW_TIME
    schedule.enter(review_time, 0, perform_command)
    schedule.enter(s_time, 0, perform_command1)
    schedule.enter(3600, 0, get_asin_spiders)
    # # 持续运行，直到计划时间队列变成空为止
    print('Spiders is runing!Time:%s' % datetime.now())
    schedule.run()


    return render(request, 'spider/home.html')

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