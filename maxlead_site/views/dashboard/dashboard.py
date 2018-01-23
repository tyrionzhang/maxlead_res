# -*- coding: utf-8 -*-
import json,datetime,operator
from django.shortcuts import render,HttpResponse
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count,Max
from maxlead_site.models import Listings,UserAsins,Reviews,ListingWacher,UserProfile
from maxlead_site.views.app import App
from maxlead_site.common.excel_world import get_excel_file

class Dashboard:


    def _get_asins(self,user,ownership='',listing_watcher='',review_watcher='',user_id=''):
        asins = []
        user_asins = UserAsins.objects.values('aid').annotate(count=Count('aid')).filter(is_use=1)
        if ownership:
            user_asins = user_asins.filter(ownership=ownership)
        if listing_watcher:
            user_asins = user_asins.filter(listing_watcher=listing_watcher)
        if review_watcher:
            user_asins = user_asins.filter(review_watcher=review_watcher)

        if user.role == 0:
            user_asins = user_asins.filter(user=user.user)
        elif user.role == 1:
            user_file = UserProfile.objects.filter(group=user)
            uids = []
            for val in user_file:
                uids.append(val.user_id)
            user_asins = user_asins.filter(user_id__in=uids)
        if user_id:
            user_asins = user_asins.filter(user_id=user_id)

        for val in user_asins:
            asins.append(val['aid'])

        return asins

    def _get_activity_radar(self, others_asins='', asin='', param={}):
        if param:
            actBgn = param.get('actBgn', '')
            actEnd = param.get('actEnd', '')
        activity_radar = []
        if asin:
            listing = Listings.objects.filter(asin=asin).order_by('-created')[:2]
            if param:
                if actBgn:
                    listing = listing.filter(created__gte=actBgn)
                if actEnd:
                    listing = listing.filter(created__lte=actEnd)

            if len(listing) == 2:
                if not listing[0].price == listing[1].price or not listing[0].title == listing[1].title or not listing[0]. \
                                           image_date == listing[1].image_date or not operator.eq(listing[0].description,
                                           listing[1].description) or not operator.eq(listing[0].feature, listing[1].feature) \
                                           or not operator.eq(listing[0].promotion, listing[1].promotion) or not operator.eq\
                                           (listing[0].lightning_deal, listing[1].lightning_deal):

                    if not listing[0].price == listing[1].price:
                        activity_radar.append({
                            'name':'price',
                            'text1':listing[0].price,
                            'text2':listing[1].price,
                            'created':listing[0].created.strftime('%Y-%m-%d'),
                        })

                    if not listing[0].image_date == listing[1].image_date:
                        activity_radar.append({
                            'name': 'image_date',
                            'text1': listing[0].image_date,
                            'text2': listing[1].image_date,
                            'created': listing[0].created.strftime('%Y-%m-%d'),
                        })
                    if not listing[0].title == listing[1].title:
                        activity_radar.append({
                            'name': 'title',
                            'text1': listing[0].title,
                            'text2': listing[1].title,
                            'created': listing[0].created.strftime('%Y-%m-%d'),
                        })
                    if not operator.eq(listing[0].promotion, listing[1].promotion):
                        activity_radar.append({
                            'name': 'promotion',
                            'text1': listing[0].promotion,
                            'text2': listing[1].promotion,
                            'created': listing[0].created.strftime('%Y-%m-%d'),
                        })
                    if not operator.eq(listing[0].description, listing[1].description):
                        activity_radar.append({
                            'name': 'description',
                            'text1': listing[0].description,
                            'text2': listing[1].description,
                            'created': listing[0].created.strftime('%Y-%m-%d'),
                        })
                    if not operator.eq(listing[0].lightning_deal, listing[1].lightning_deal):
                        activity_radar.append({
                            'name': 'lightning_deal',
                            'text1': listing[0].lightning_deal,
                            'text2': listing[1].lightning_deal,
                            'created': listing[0].created.strftime('%Y-%m-%d'),
                        })
                    if not operator.eq(listing[0].feature, listing[1].feature):
                        activity_radar.append({
                            'name': 'feature',
                            'text1': listing[0].feature,
                            'text2': listing[1].feature,
                            'created': listing[0].created.strftime('%Y-%m-%d'),
                        })

                    # listing[0].created = listing[0].created.strftime('%Y-%m-%d')
                    # if eval(listing[0].buy_box_res):
                    #     listing[0].buy_box_res = eval(listing[0].buy_box_res)[0]
                    # else:
                    #     listing[0].buy_box_res = ''
                    # listing[0].price1 = listing[1].price
                    # listing[0].title1 = listing[1].title
                    # listing[0].description1 = listing[1].description
                    # activity_radar.append(listing[0])
            return activity_radar
        else:
            for val in others_asins:
                listing = Listings.objects.filter(asin=val).order_by('-created')[:2]
                if param:
                    if actBgn:
                        listing = listing.filter(created__gte=actBgn)
                    if actEnd:
                        listing = listing.filter(created__lte=actEnd)

                if len(listing) == 2:
                    if not listing[0].price == listing[1].price or not listing[0].title == listing[1].title or not listing[0]. \
                                               image_date == listing[1].image_date or not operator.eq(listing[0].description,
                                               listing[1].description) or not operator.eq(listing[0].feature, listing[1].feature):

                        listing[0].changed = ''
                        if not listing[0].price == listing[1].price:
                            listing[0].changed += 'price,'
                        if not listing[0].image_date == listing[1].image_date:
                            listing[0].changed += 'Gallery,'
                        if not listing[0].title == listing[1].title:
                            listing[0].changed += 'title,'
                        if not listing[0].feature == listing[1].feature or not listing[0].description == listing[
                            1].description:
                            listing[0].changed += 'Promotion,'

                        listing[0].created = listing[0].created.strftime('%Y-%m-%d')
                        if eval(listing[1].buy_box_res):
                            listing[0].buy_box_res = eval(listing[1].buy_box_res)[0]
                        else:
                            listing[0].buy_box_res = ''
                        listing[0].price1 = listing[1].price
                        listing[0].title1 = listing[1].title
                        listing[0].description1 = listing[1].description
                        activity_radar.append(listing[0])
            return activity_radar

    def _get_rising(self,user,ownership,user_id,param = ''):
        if param:
            ourBgn = param.get('ourBgn', '')
            ourEnd = param.get('ourEnd', '')
            othBgn = param.get('othBgn', '')
            othEnd = param.get('othEnd', '')
        data = []
        asins = Dashboard._get_asins(self, user, ownership=ownership, user_id=user_id)
        for val in asins:
            listing_max = Listings.objects.filter(asin=val).aggregate(Max('created'))
            if not listing_max or not listing_max['created__max']:
                continue
            start_time = listing_max['created__max'].strftime("%Y-%m-%d")
            if param:
                if ourBgn:
                    start_time = ourBgn
                if othBgn:
                    start_time = othBgn
            listing = Listings.objects.filter(asin=val,created__icontains=start_time)
            if listing:
                end_time = (listing[0].created + datetime.timedelta(days=-7)).strftime("%Y-%m-%d")
                if param:
                    if ourEnd:
                        end_time = ourEnd
                    if othEnd:
                        end_time = othEnd
                listing1 = Listings.objects.filter(asin=val,created__icontains=end_time)

                if listing1:
                    rvw_score2 = round(float(listing[0].rvw_score) - float(listing1[0].rvw_score),2)
                    total_review2 = listing[0].total_review - listing1[0].total_review
                else:
                    rvw_score2 = 0
                    total_review2 = 0
                re = {
                    'asin':listing[0].asin,
                    'created':listing[0].created.strftime("%Y-%m-%d"),
                    'sku':listing[0].user_asin.sku,
                    'brand':listing[0].brand,
                    'total_review':listing[0].total_review,
                    'total_review2':total_review2,
                    'rvw_score':float(listing[0].rvw_score),
                    'rvw_score2':rvw_score2
                }
                data.append(re)
        if data:
            for v in range(len(data)):
                for i in range(len(data) - 1 - v):
                    if (i + 1) < len(data) and data[i+1]['total_review2'] > data[i]['total_review2']:
                        temp = data[i + 1]
                        data[i + 1] = data[i]
                        data[i] = temp
        return data

    def index(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        viewRange = self.GET.get('viewRange',user.user.id)

        if viewRange:
            viewRange = int(viewRange)

        user_list = UserProfile.objects.filter(state=1)
        if user.role == 0:
            user_list = user_list.filter(id=user.id)
        if user.role == 1:
            user_list = user_list.filter(Q(group=user)|Q(id=user.id))

        asins = Dashboard._get_asins(self,user,listing_watcher=1,user_id=viewRange)
        ours_li = Dashboard._get_rising(self,user,'Ours',viewRange)[0:8]
        others_li = Dashboard._get_rising(self,user,'Others',viewRange)[0:8]
        others_asins = Dashboard._get_asins(self, user, ownership='Others', user_id=viewRange)

        activity_radar = Dashboard._get_activity_radar(self, others_asins = others_asins)
        if activity_radar:
            activity_radar = activity_radar[0:6]
        radar_page = 0
        if len(activity_radar) >= 6:
            radar_page = 1

        o_rising_page = 0
        th_rising_page = 0
        if len(ours_li) >= 8:
            o_rising_page = 1
        if len(others_li) >= 8:
            th_rising_page = 1
        review_max = Reviews.objects.filter(asin__in=asins).aggregate(Max('created'))
        if review_max and review_max['created__max']:
            reviews = Reviews.objects.filter(created__icontains=review_max['created__max'],score__lte=3,asin__in=asins).order_by('-review_date')
        else:
            reviews = []
        is_page = 0
        if len(reviews) > 6:
            is_page = 1
        if reviews:
            reviews = reviews[0:6]

        for val in reviews:
            if val.review_date:
                val.review_date = val.review_date.strftime("%Y-%m-%d")
            sku = UserAsins.objects.filter(aid=val.asin)
            val.sku = sku[0].sku

        data = {
            'user': user,
            'avator': user.user.username[0],
            'reviews': reviews,
            'ours_li': ours_li,
            'others_li': others_li,
            'is_page': is_page,
            'th_rising_page': th_rising_page,
            'o_rising_page': o_rising_page,
            'radar_page': radar_page,
            'activity_radar': activity_radar,
            'user_list': user_list,
            'viewRange': viewRange,
        }
        return render(self, 'dashboard/dashboard.html', data)

    @csrf_exempt
    def ajax_get_reviews(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}),content_type='application/json')
        revBgn = self.GET.get('revBgn', '')
        revEnd = self.GET.get('revEnd', '')
        page = self.GET.get('page', 1)
        viewRange = self.GET.get('viewRange', '')
        offset = (int(page)-1)*6

        asins = Dashboard._get_asins(self,user,user_id=viewRange)
        review_max = Reviews.objects.filter(asin__in=asins).aggregate(Max('created'))
        if not review_max or not review_max['created__max']:
            return HttpResponse(json.dumps({'code': 0, 'msg': '没有数据！'}), content_type='application/json')
        reviews = Reviews.objects.filter(created__icontains=review_max['created__max'],score__lte=3, asin__in=asins).order_by('-review_date')

        if revBgn:
            reviews = reviews.filter(review_date__gte=revBgn)
        if revEnd:
            reviews = reviews.filter(review_date__lte=revEnd)
        if reviews:
            reviews = reviews[offset:offset+6]
        if not reviews:
            return HttpResponse(json.dumps({'code': 0, 'msg': '没有数据！'}), content_type='application/json')

        data = []
        for val in reviews:
            if val.review_date:
                val.review_date = val.review_date.strftime("%Y-%m-%d")
            a = model_to_dict(val)
            a['sku'] = UserAsins.objects.get(aid=val.asin).sku
            data.append(a)
        is_page = 1
        if len(reviews) < 6:
            is_page = 0

        re = {
            'data':data,
            'review_page':page,
            'is_page':is_page
        }

        return HttpResponse(json.dumps({'code': 1, 'data': re}), content_type='application/json')

    @csrf_exempt
    def ajax_rising(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')

        type = self.GET.get('type', 'Ours')
        viewRange = self.GET.get('viewRange', '')
        page = self.GET.get('page', 1)
        offset = (int(page) - 1) * 8
        res = Dashboard._get_rising(self,user,type,viewRange,param=self.GET)[offset:offset+8]
        is_page = 1
        if len(res) < 8:
            is_page = 0

        data = {
            'data':res,
            'is_page':is_page,
            'page':page,
            'type':type
        }
        return HttpResponse(json.dumps({'code': 1, 'data': data}), content_type='application/json')

    @csrf_exempt
    def ajax_radar(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')

        page = self.GET.get('page', 1)
        viewRange = self.GET.get('viewRange', '')
        offset = (int(page) - 1) * 6
        asins = Dashboard._get_asins(self, user, ownership='Others',user_id=viewRange)
        res = Dashboard._get_activity_radar(self,asins, param=self.GET)
        is_page = 1
        if len(res)<6:
            is_page = 0
        data = []
        if res:
            res = res[offset:offset+6]
            for val in res:
                re = {
                    'asin':val.asin,
                    'created':val.created,
                    'changed':val.changed,
                    'buy_box_res':val.buy_box_res
                }
                data.append(re)
            data = {
                'data': data,
                'page': page,
                'is_page': is_page
            }
            return HttpResponse(json.dumps({'code': 1, 'data': data}), content_type='application/json')
        else:
            data = {
                'data': [],
                'page': page,
                'is_page': is_page
            }
            return HttpResponse(json.dumps({'code': 1, 'data': data}), content_type='application/json')

    @csrf_exempt
    def ajax_watcher(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')
        page = self.GET.get('page',1)
        listBgn = self.GET.get('listBgn','')
        listEnd = self.GET.get('listEnd','')
        viewRange = self.GET.get('viewRange', '')
        offset = (int(page)-1)*6
        asins = Dashboard._get_asins(self, user,listing_watcher=1,user_id=viewRange)
        listing_watchers = []
        listing_watchers = ListingWacher.objects.filter(asin__in=asins)
        if not listEnd and not listBgn:
            listing_watchers_max = listing_watchers.aggregate(Max('created'))
            listing_watchers = listing_watchers.filter(created__icontains=listing_watchers_max['created__max'].strftime("%Y-%m-%d"))
        if listEnd:
            listing_watchers = listing_watchers.filter(created__lte=listEnd)
        if listBgn:
            listing_watchers = listing_watchers.filter(created__gte=listBgn)

        if listing_watchers:
            listing_watchers = listing_watchers[offset:offset+6]
        data = []
        for val in listing_watchers:
            if val.price:
                price = val.price
            else:
                price = ''
            if val.fba:
                fba = 'FBA'
            else:
                fba = 'FBM'
            if val.prime:
                prime = 'Prime'
            else:
                prime = ''
            if val.shipping:
                shipping = val.shipping
            else:
                shipping = ''

            if val.winner:
                winner = 'Buy box winner'
            else:
                winner = 'not winner'
            asin = UserAsins.objects.filter(aid=val.asin)[0]
            re = {
                'created':val.created.strftime('%Y-%m-%d %H:%M:%S'),
                'seller_link':val.seller_link,
                'seller':val.seller,
                'asin':val.asin,
                'sku':asin.sku,
                'price':price,
                'fba':fba,
                'prime':prime,
                'shipping':shipping,
                'winner':winner,
                'images':val.images,
            }
            data.append(re)
        li_watcher_page = 0
        if len(listing_watchers) >= 3:
            li_watcher_page = 1
        data = {
            'li_watcher_page':li_watcher_page,
            'data':data,
            'page':page
        }
        return HttpResponse(json.dumps({'code': 1, 'data': data}), content_type='application/json')

    @csrf_exempt
    def export_dash_reviews(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")

        revBgn = self.GET.get('revBgn', '')
        revEnd = self.GET.get('revEnd', '')
        viewRange = self.GET.get('viewRange', '')

        asins = Dashboard._get_asins(self,user,user_id=viewRange)
        review_max = Reviews.objects.filter(asin__in=asins).aggregate(Max('created'))
        if review_max and review_max['created__max']:
            reviews = Reviews.objects.filter(created__icontains=review_max['created__max'],score__lte=3, asin__in=asins).order_by('-review_date')
            if revBgn:
                reviews = reviews.filter(review_date__gte=revBgn)
            if revEnd:
                reviews = reviews.filter(review_date__lte=revEnd)
            if not revBgn and not revEnd:
                reviews = reviews[0:6]
            data = []
            for val in reviews:
                re = {
                    'title': val.title,
                    'variation': val.variation,
                    'asin': val.asin,
                    'name': val.name,
                    'score': val.score,
                    'is_vp': val.is_vp,
                    'review_date': val.review_date.strftime("%Y-%m-%d"),
                    'content': val.content,
                    'review_link': val.review_link,
                    'created': val.created.strftime("%Y-%m-%d"),
                }
                data.append(re)

            fields = [
                'Title',
                'Variation',
                'Asin',
                'Name',
                'Score',
                'VP',
                'Review Date',
                'Content',
                'Review Link',
                'Created'
            ]
            data_fields = [
                'title',
                'variation',
                'asin',
                'name',
                'score',
                'is_vp',
                'review_date',
                'content',
                'review_link',
                'created'
            ]
            return get_excel_file(self, data, fields, data_fields)

    @csrf_exempt
    def export_rising(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")

        type = self.GET.get('type', 'Ours')
        viewRange = self.GET.get('viewRange', '')

        res = Dashboard._get_rising(self, user, type, viewRange, param=self.GET)

        fields = [
            'SKU',
            'Asin',
            'Reviews',
            'Brand',
            'Growth',
            'Score',
            'Score Change',
            'Created'
        ]
        data_fields = [
            'sku',
            'asin',
            'total_review',
            'brand',
            'total_review2',
            'rvw_score',
            'rvw_score2',
            'created'
        ]
        return get_excel_file(self, res, fields, data_fields)

    @csrf_exempt
    def export_radar(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")

        viewRange = self.GET.get('viewRange', '')
        asins = Dashboard._get_asins(self, user, ownership='Others',user_id=viewRange)
        res = Dashboard._get_activity_radar(self, asins,param=self.GET)
        if not self.GET.get('actBgn','') and not self.GET.get('actEnd',''):
            res = res[0:6]
        data = []
        if res:
            for val in res:
                re = {
                    'asin': val.asin,
                    'title': val.title,
                    'price': val.price,
                    'feature': val.feature,
                    'description': val.description,
                    'image_date': val.image_date.strftime('%Y-%m-%d'),
                    'image_names': val.image_thumbs,
                    'created': val.created,
                    'changed': val.changed,
                    'buy_box_res': val.buy_box_res
                }
                data.append(re)

            fields = [
                'Image Thumbs',
                'Title',
                'Asin',
                'Price',
                'Changed',
                'Feature',
                'Description',
                'Image Date',
                'Buy Box',
                'Created'
            ]
            data_fields = [
                'image_names',
                'title',
                'asin',
                'price',
                'changed',
                'feature',
                'description',
                'image_date',
                'buy_box_res',
                'created'
            ]
            return get_excel_file(self, data, fields, data_fields)

    @csrf_exempt
    def export_watcher(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')
        listBgn = self.GET.get('listBgn', '')
        listEnd = self.GET.get('listEnd', '')
        viewRange = self.GET.get('viewRange', '')
        asins = Dashboard._get_asins(self, user, listing_watcher=1,user_id=viewRange)
        listing_watchers = []
        listing_watchers = ListingWacher.objects.filter(asin__in=asins)
        if not listEnd and not listBgn:
            listing_watchers_max = ListingWacher.objects.aggregate(Max('created'))
            listing_watchers = listing_watchers.filter(
                created__icontains=listing_watchers_max['created__max'].strftime("%Y-%m-%d"))
        if listEnd:
            listing_watchers = listing_watchers.filter(created__lte=listEnd)
        if listBgn:
            listing_watchers = listing_watchers.filter(created__gte=listBgn)

        if listing_watchers:
            listing_watchers = listing_watchers
        if not listBgn and not listEnd:
            listing_watchers = listing_watchers[0:6]
        data = []
        for val in listing_watchers:
            if val.price:
                price = val.price
            else:
                price = ''
            if val.fba:
                fba = 'FBA'
            else:
                fba = 'FBM'
            if val.prime:
                prime = 'Prime'
            else:
                prime = ''
            if val.shipping:
                shipping = val.shipping
            else:
                shipping = ''

            if val.winner:
                winner = 'Buy box winner'
            else:
                winner = 'not winner'
            re = {
                'created': val.created.strftime('%Y-%m-%d %H:%M:%S'),
                'seller_link': val.seller_link,
                'asin': val.asin,
                'seller': val.seller,
                'price': price,
                'fba': fba,
                'prime': prime,
                'shipping': shipping,
                'winner': winner,
            }
            data.append(re)

        fields = [
            'Asin',
            'Seller',
            'Price',
            'FBA',
            'Prime',
            'Shipping',
            'Winner',
            'Seller Link',
            'Created',
        ]

        data_fields = [
            'asin',
            'seller',
            'price',
            'fba',
            'prime',
            'shipping',
            'winner',
            'seller_link',
            'created',
        ]
        return get_excel_file(self, data, fields, data_fields)
