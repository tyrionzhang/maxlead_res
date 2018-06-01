import os,sched
from datetime import *
import time
from maxlead import settings
from max_stock.models import SkuUsers,StockLogs,WarehouseStocks
from django.http import HttpResponse

# 第一个参数确定任务的时间，返回从某个特定的时间到现在经历的秒数
# 第二个参数以某种人为的方式衡量时间
schedule = sched.scheduler(time.time, time.sleep)

def _set_user_sku():
    sku_list = []
    user_skus = SkuUsers.objects.filter().all()
    if user_skus:
        for val in user_skus:
            sku_list.append(val.sku)
        file_path = os.path.join(settings.BASE_DIR, settings.THRESHOLD_TXT, 'userSkus_txt.txt')
        with open(file_path, "w+") as f:
            sku_list = str(sku_list)
            f.write(sku_list)
            f.close()
    return True

def perform_command():
    # 安排inc秒后再次运行自己，即周期运行
    spiders_time = settings.STOCHS_TIME
    schedule.enter(spiders_time, 0, perform_command)
    _set_user_sku()

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

def save_logs(data):
    logs = StockLogs()
    logs.id
    logs.user = data['user']
    logs.fun = data['fun']
    logs.description = data['description']
    res = logs.save()
    return True

def empty_data(request):
    WarehouseStocks.objects.filter().all().delete()
    return HttpResponse(request, 'Spiders is runing!Time:%s' % datetime.now())