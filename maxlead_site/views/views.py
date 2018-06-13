import os,sched
from datetime import *
import time,re
import queue
import threading
import operator
from django.db.models import Count
from django.shortcuts import render
from maxlead import settings
from maxlead_site.common.user_secuirty import UserSecuirty
from maxlead_site.common.excel_world import read_csv_file
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from maxlead_site.models import UserAsins,AsinReviews,Reviews,AsinReviewsBackcup,ReviewsBackcup,Questions,QuestionsBackcup
from maxlead_site.models import Answers,AnswersBackcup,ListingWacherBackcup,ListingWacher,Listings,ListingsBackcup,CategoryRank,CategoryRankBackcup

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
            cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % \
                       val['aid']
            cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % \
                       val['aid']
            os.popen(cmd_str3)
            os.popen(cmd_str4)
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
            os.popen(cmd_str2)

        os.chdir(settings.ROOT_PATH)
    return True

def Spiders2(request):
    schedule.enter(32400, 0, perform_command)
    schedule.enter(36000, 0, perform_command1)
    # 持续运行，直到计划时间队列变成空为止
    print('Spiders is runing!Time:%s' % datetime.now())
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

def back_up_table():
    schedule.enter(864000, 0, back_up_table)
    now =datetime.now()
    date = now + timedelta(days=-9)
    review_date = now + timedelta(days=-21)
    asin_reviews = AsinReviews.objects.filter(created__lt=review_date)
    reviews = Reviews.objects.filter(created__lt=review_date)
    questions = Questions.objects.filter(created__lt=review_date)
    answers = Answers.objects.filter(created__lt=review_date)
    listingWachers = ListingWacher.objects.filter(created__lt=review_date)
    listings = Listings.objects.filter(created__lt=date)
    categoryranks = CategoryRank.objects.filter(created__lt=date)
    if asin_reviews:
        querysetlist = []
        for val in asin_reviews:
            querysetlist.append(AsinReviewsBackcup(ar_id=val.id,aid=val.aid,positive_keywords=val.positive_keywords,negative_keywords=val.negative_keywords,
                                            avg_score=val.avg_score,total_review=val.total_review,is_done=val.is_done,created=val.created))
        ob = AsinReviewsBackcup.objects.bulk_create(querysetlist)
        if ob:
            asin_reviews.delete()
    if reviews:
        querysetlist = []
        for val in reviews:
            querysetlist.append(ReviewsBackcup(rid=val.id,name=val.name,asin=val.asin,title=val.title,variation=val.variation,content=val.content,
                                review_link=val.review_link,score=val.score,is_vp=val.is_vp,review_date=val.review_date,
                                created=val.created,image_names=val.image_names,image_thumbs=val.image_thumbs,image_urls=val.image_urls))
        ob = ReviewsBackcup.objects.bulk_create(querysetlist)
        if ob:
            reviews.delete()
    if answers:
        querysetlist = []
        for val in answers:
            querysetlist.append(AnswersBackcup(qid=val.question_id, person=val.person, answer=val.answer,created=val.created))
        ob = AnswersBackcup.objects.bulk_create(querysetlist)
        if ob:
            answers.delete()
    if questions:
        querysetlist = []
        for val in questions:
            querysetlist.append(QuestionsBackcup(qid=val.id,question=val.question,asin=val.asin,asked=val.asked,votes=val.votes,
                                                 count=val.count,is_done=val.is_done,created=val.created))
        ob = QuestionsBackcup.objects.bulk_create(querysetlist)
        if ob:
            questions.delete()
    if listingWachers:
        querysetlist = []
        for val in listingWachers:
            querysetlist.append(ListingWacherBackcup(asin=val.asin,seller=val.seller,seller_link=val.seller_link,price=val.price,
                                                     shipping=val.shipping,fba=val.fba,prime=val.prime,winner=val.winner,
                                                     images=val.images,created=val.created))
        ob = ListingWacherBackcup.objects.bulk_create(querysetlist)
        if ob:
            listingWachers.delete()
    if listings:
        querysetlist = []
        for val in listings:
            querysetlist.append(ListingsBackcup(user_asin=val.user_asin_id,title=val.title,answered=val.answered,asin=val.asin,
                                                sku=val.sku,brand=val.brand,shipping=val.shipping,prime=val.prime,description=val.description,
                                                feature=val.feature,promotion=val.promotion,lightning_deal=val.lightning_deal,
                                                buy_box=val.buy_box,buy_box_link=val.buy_box_link,buy_box_res=val.buy_box_res,
                                                price=val.price,total_review=val.total_review,total_qa=val.total_qa,rvw_score=val.rvw_score,
                                                category_rank=val.category_rank,inventory=val.inventory,is_review_watcher=val.is_review_watcher,
                                                is_listing_watcher=val.is_listing_watcher,created=val.created,image_date=val.image_date,
                                                image_names=val.image_names,image_thumbs=val.image_thumbs,image_urls=val.image_urls))
        ob = ListingsBackcup.objects.bulk_create(querysetlist)
        if ob:
            listings.delete()
    if categoryranks:
        querysetlist = []
        for val in categoryranks:
            querysetlist.append(CategoryRankBackcup(user_asin=val.user_asin,asin=val.asin,cat=val.cat,keywords=val.keywords,
                                                    rank=val.rank,is_ad=val.is_ad,created=val.created))
        ob = CategoryRankBackcup.objects.bulk_create(querysetlist)
        if ob:
            categoryranks.delete()
    return True

def back_upTable(request):
    schedule.enter(1, 0, back_up_table)
    schedule.run()

def export_users(request):
    re = read_csv_file('/home/techsupp/www/staffx.csv')
    return HttpResponse(re['msg'])

def letsencrpyt(request,token_value):
    with open('/home/techsupp/www/.well-known/acme-challenge/{}'.format(token_value)) as f:
        answer = f.readline().strip()
    return answer

class perform_command_que(threading.Thread):
    def __init__(self, t_name, queue,aids):
        threading.Thread.__init__(self,name=t_name)
        self.data = queue
        self.aids = aids
        self.t_name = t_name

    def run(self):
        work_path = settings.SPIDER_URL
        os.chdir(work_path)
        os.popen('scrapyd-deploy')

        while 1:
            try:
                val_even = self.data.get(1)
                if val_even == 1:
                    for val in self.aids:
                        cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % val['aid']
                        cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % val['aid']
                        cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % val['aid']
                        os.popen(cmd_str3)
                        os.popen(cmd_str4)
                        os.popen(cmd_str)
                    os.chdir(settings.ROOT_PATH)
                    self.data.put(2)
                    time.sleep(10)
            except:
                print('%s:%s finished!' % (time.time(), self.getName()))
                break

class perform_command_que1(threading.Thread):
    def __init__(self, t_name, queue,aids):
        threading.Thread.__init__(self,name=t_name)
        self.data = queue
        self.aids = aids
        self.t_name = t_name

    def run(self):
        work_path = settings.SPIDER_URL
        os.chdir(work_path)
        os.popen('scrapyd-deploy')

        while 1:
            try:
                val_even = self.data.get(2)
                if val_even == 2:
                    for val in self.aids:
                        cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % val['aid']
                        os.popen(cmd_str2)

                    os.chdir(settings.ROOT_PATH)
                    self.data.put(3)
                    time.sleep(10)
            except:
                print('%s:%s finished!' % (time.time(), self.getName()))
                break

class perform_command_que3(threading.Thread):
    def __init__(self, t_name, queue,aids):
        threading.Thread.__init__(self,name=t_name)
        self.data = queue
        self.aids = aids
        self.t_name = t_name

    def run(self):
        work_path = settings.SPIDER_URL
        os.chdir(work_path)
        os.popen('scrapyd-deploy')
        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % 88
        os.popen(cmd_str1)
        os.chdir(settings.ROOT_PATH)
        self.data.put(1)
        time.sleep(10)

def run_command_queue(request):
    q = queue.Queue()
    res = list(UserAsins.objects.filter(is_use=True).values('aid').annotate(count=Count('aid')))

    tname = 'reviews_done'
    rname = 'rank_done'
    lname = 'listing_done'
    lis = perform_command_que3(lname, q, res)
    reviews = perform_command_que(tname, q, res)
    ranks = perform_command_que1(rname, q, res)
    lis.start()
    reviews.start()
    ranks.start()
    lis.join()
    reviews.join()
    ranks.join()
    return render(request, 'spider/home.html')

