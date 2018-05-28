import os,sched
from datetime import *
import time
from maxlead import settings
from django.http import HttpResponse

# 第一个参数确定任务的时间，返回从某个特定的时间到现在经历的秒数
# 第二个参数以某种人为的方式衡量时间
schedule = sched.scheduler(time.time, time.sleep)

def perform_command():
    # 安排inc秒后再次运行自己，即周期运行
    spiders_time = settings.STOCHS_TIME
    schedule.enter(spiders_time, 0, perform_command)

    work_path = settings.STOCHS_SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=hanover_spider'
    cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=stockbot -d spider=twu_spider'
    os.popen(cmd_str1)
    os.popen(cmd_str2)
    os.chdir(settings.ROOT_PATH)

def stock_spiders(request):
    schedule.enter(60, 0, perform_command)
    # 持续运行，直到计划时间队列变成空为止
    print('Spiders is runing!Time:%s' % datetime.now())
    schedule.run()
    return HttpResponse(request, 'Spiders is runing!Time:%s' % datetime.now())