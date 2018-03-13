import os,time
import queue
import math
import threading
from django.db.models import Count
from maxlead_site.models import UserAsins
from maxlead import settings
from django.core.paginator import Paginator
from scrapy import cmdline

def qu_spiders(asins):
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    if asins:
        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % str(asins)
        os.popen(cmd_str1)
        for i, val in enumerate(asins, 1):
            cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % \
                       val
            cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % \
                       val
            cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % \
                       val
            os.popen(cmd_str2)
            os.popen(cmd_str3)
            os.popen(cmd_str4)
        os.chdir(settings.ROOT_PATH)
    return

def qu_review_spiders(asins):
    work_path = settings.SPIDER_URL
    os.chdir(work_path)
    os.popen('scrapyd-deploy')
    if asins:
        for i, val in enumerate(asins, 1):
            cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % \
                       val
            os.popen(cmd_str2)
        os.chdir(settings.ROOT_PATH)
    return

def que_to():
    q = queue.PriorityQueue()
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))
    total_count = len(res)
    total_page = math.ceil(total_count / 10)
    paginator = Paginator(res, 10)
    for page in range(total_page):
        data = paginator.page(page + 1)
        asins = []
        for aid in data:
            asins.append(aid['aid'])
        q.put(qu_spiders(asins))
        q.put(qu_review_spiders(asins))

    workers = [threading.Thread(target=process_job, args=(q,))]

    for w in workers:
        w.setDaemon(True)
        w.start()

    q.join()

def process_job(q):
    while True:
        q.get()
        q.task_done()
