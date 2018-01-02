# -*- coding: utf-8 -*-
import json,datetime
from django.shortcuts import render,HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from maxlead_site.models import Listings,UserAsins,MenberGroups
from maxlead_site.views.app import App
from maxlead_site.common.excel_world import get_excel_file

class Listing:

    @csrf_exempt
    def index(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        listKwd = self.GET.get('listKwd','')
        searchCol = self.GET.get('searchCol','title')
        buybox = self.GET.get('buybox','')
        status = self.GET.get('status','')
        revstatus = self.GET.get('revstatus','')
        liststatus = self.GET.get('liststatus','')

        asins = []
        user_asins = UserAsins.objects.values('aid').annotate(count=Count('aid'))
        if user.role == 2:
            user_asins = user_asins.filter()

        elif user.role == 0:
            user_asins = user_asins.filter(user=user.user)
        elif user.role == 1:
            groups = MenberGroups.objects.filter(user=user.user)
            user_list = User.objects.filter(group=groups)
            user_asins = user_asins.filter(user=user_list)

        if user_asins:
            if status:
                user_asins = user_asins.filter(is_use=status)
            if revstatus:
                user_asins = user_asins.filter(review_watcher=revstatus)
            if liststatus:
                user_asins = user_asins.filter(listing_watcher=liststatus)

            for val in user_asins:
                asins.append(val['aid'])
            listings = Listings.objects.values('asin').annotate(count=Count('asin')).filter(asin__in=asins)

            if buybox:
                listings = listings.filter(buy_box=buybox)
            if listKwd and searchCol:
                if searchCol == 'SKU':
                    listings = listings.filter(sku__icontains=listKwd)
                if searchCol == 'ASIN':
                    listings = listings.filter(asin__icontains=listKwd)
                if searchCol == 'title':
                    listings = listings.filter(title__icontains=listKwd)
                if searchCol == 'brand':
                    listings = listings.filter(brand__icontains=listKwd)
                if searchCol == 'seller':
                    listings = listings.filter(buy_box_res__icontains=listKwd)
            listings = listings.all()

            limit = int(self.GET.get('limit', 1))
            total_count = listings.count()
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
                    'status': status,
                    'revstatus': revstatus,
                    'liststatus': liststatus,
                    'limit': limit
                })
            paginator = Paginator(listings, limit)
            page = self.GET.get('page')
            try:
                list_data = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                list_data = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                list_data = paginator.page(paginator.num_pages)
            res = []
            if list_data:
                for v in list_data:
                    listing = Listings.objects.filter(asin=v['asin']).order_by('-created')[:2]
                    buy_box_res = eval(listing[0].buy_box_res)
                    if buy_box_res:
                        buy_box_res = buy_box_res[0]
                    else:
                        buy_box_res = ''
                    category_rank = listing[0].category_rank
                    if category_rank:
                        category_rank = category_rank.split('|')[0]

                    if len(listing) == 2:
                        price2 = float(listing[0].price[1:]) - float(listing[1].price[1:])
                        total_review2 = int(listing[0].total_review) - int(listing[1].total_review)
                        rvw_score2 = float(listing[0].rvw_score) - float(listing[1].rvw_score)
                    else:
                        price2 = ''
                        total_review2 = ''
                        rvw_score2 = ''

                    last_check_data = listing[0].user_asin.last_check
                    last_check = ''
                    if last_check_data:
                        last_check = last_check_data.strftime("%Y-%m-%d %H:%M:%S")

                    re = {
                        'id':listing[0].id,
                        'title':listing[0].title,
                        'asin':listing[0].asin,
                        'sku':listing[0].sku,
                        'brand':listing[0].brand,
                        'price':listing[0].price,
                        'price2':price2,
                        'total_review':listing[0].total_review,
                        'total_review2':total_review2,
                        'rvw_score2':rvw_score2,
                        'rvw_score':float(listing[0].rvw_score),
                        'category_rank':category_rank.split('in')[1],
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
                'total_page': int(total_count/limit),
                'page': page,
                'searchCol': searchCol,
                'buybox': buybox,
                'listKwd': listKwd,
                'status': status,
                'revstatus': revstatus,
                'liststatus': liststatus,
                'limit': limit,
            }

            return render(self, 'listings/listing.html', data)

    @csrf_exempt
    def save_user_asin(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        if self.method == 'POST':
            ids = self.POST.get('ids','')
            newASIN = self.POST.get('newASIN')
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

            newASIN = newASIN.split('|')
            if newSKU:
                newSKU = newSKU.split('|')
            keywords = kwdSet1+'|'+kwdSet2+'|'+kwdSet3
            cat = cat1+'|'+cat2+'|'+cat3

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
                        userAsin.keywords = keywords
                        userAsin.user_id = user.user.id
                        userAsin.cat = cat
                        userAsin.review_watcher = revWatcher
                        userAsin.listing_watcher = listWatcher
                        userAsin.is_use = status

                        querysetlist.append(userAsin)
                UserAsins.objects.bulk_create(querysetlist)
                return HttpResponse(json.dumps({'code': 1, 'msg': u'添加成功！'}), content_type='application/json')
            else:
                userAsin_obj = UserAsins.objects.filter(id__in=eval(ids)).all()
                if userAsin_obj:
                    if newSKU:
                        userAsin_obj.update(sku=newSKU[0])
                    userAsin_obj.update(keywords=keywords,cat=cat,review_watcher=revWatcher,listing_watcher=listWatcher,
                                        is_use=status,ownership=ownership,last_check=datetime.datetime.now())

                return HttpResponse(json.dumps({'code': 1, 'msg': u'修改成功！'}), content_type='application/json')

    @csrf_exempt
    def ajax_get_asins(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 1, 'msg': u'用户未登录！'}), content_type='application/json')
        ids = self.POST.get('ids')
        asins = UserAsins.objects.values('aid','sku').filter(id__in=eval(ids)).all()
        aid_str = ''
        sku_str = ''
        for val in asins:
            aid_str += val['aid']+'|'
            sku_str += val['sku']+'|'

        return HttpResponse(json.dumps({'code':1,'aid_str': aid_str, 'sku_str': sku_str}), content_type='application/json')

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
