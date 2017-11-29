import os,difflib
from datetime import *
from threading import Timer
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from maxlead_site.models import UserAsins,AsinReviews,Reviews
from maxlead import settings

def RunReview(request):
    # work_path = settings.SPIDER_URL
    # os.chdir(work_path)  # 修改当前工作目录
    # os.system('scrapyd-deploy')
    # os.system('curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider')

    aid_list = UserAsins.objects.filter(is_use=True).values('aid')
    for aid in list(aid_list):
        review_contents = Reviews.objects.filter(asin=aid['aid']).filter(created=date.today()).values('content')
        asin_reviews = AsinReviews.objects.filter(aid=aid['aid']).filter(created=date.today()).all()
        if review_contents:
            review_contents = list(review_contents)
        for i, content in enumerate(review_contents,0):
            for k, con in enumerate(review_contents,0):
                if not i == k:
                    content_line = content['content'].splitlines()
                    con_line = con['content'].splitlines()
                    d = difflib.Differ()
                    diff = d.compare(content_line, con_line)
                    print(list(diff))
        pass

    # t = Timer(settings.REVIEW_TIME, RunReview(request))
    # t.start()

    return render(request, 'spider/home.html')


RunReview = staff_member_required(RunReview)
