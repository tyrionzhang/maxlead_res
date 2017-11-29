#-*-coding:utf-8-*-

from maxlead import settings
import os, json

# Create your tviews here.

def RunReview():
    work_path = settings.SPIDER_URL
    os.chdir(work_path)  # 修改当前工作目录
    os.system('scrapyd')
    output = os.popen('scrapyd-deploy')
    re = json.loads(output.read())
    if re['status'] == 'ok':
        os.popen('curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider')
