# -*- coding: utf-8 -*-
import json,datetime
from django.shortcuts import render,HttpResponse
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max
from maxlead_site.models import Listings,UserAsins,Questions,Answers,Reviews,AsinReviews,ListingWacher
from maxlead_site.views.app import App
from maxlead_site.common.excel_world import get_excel_file
from maxlead_site.views.dashboard.dashboard import Dashboard

class Item:

    def item(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        asin = self.GET.get('asin', '')
        listing_max = Listings.objects.aggregate(Max('created'))
        out_time = listing_max['created__max']-datetime.timedelta(days=30)
        listing = Listings.objects.filter(asin=asin).filter(created__gte=out_time).filter(created__lte=listing_max['created__max']).order_by('-created')
        item = listing[0]
        UserAsins.objects.filter(id=item.user_asin.id).update(last_check=datetime.datetime.now())
        qa_max = Questions.objects.aggregate(Max('created'))
        question_count = Questions.objects.filter(asin=item.asin,created__icontains=qa_max['created__max'].strftime("%Y-%m-%d"))
        answer_count = Answers.objects.filter(question__in=question_count)
        asinreview = AsinReviews.objects.filter(aid=item.asin,created__icontains=AsinReviews.objects.aggregate(Max('created'))
                                                                            ['created__max'].strftime("%Y-%m-%d")).all()
        review = Reviews.objects.filter(asin=item.asin,created__icontains=Reviews.objects.aggregate(Max('created'))
                                                                            ['created__max'].strftime("%Y-%m-%d")).all()
        listing_watchers = []
        listing_watchers_max = ListingWacher.objects.aggregate(Max('created'))
        listing_watchers = ListingWacher.objects.filter(asin=item.asin,created__icontains=listing_watchers_max['created__max']. \
                                                        strftime("%Y-%m-%d"))
        item_offer = len(listing_watchers)
        if listing_watchers:
            listing_watchers = listing_watchers[0:3]
        for val in listing_watchers:
            val.created = val.created.strftime('%Y-%m-%d %H:%M:%S')
        li_watcher_page = 1
        if len(listing_watchers) < 3:
            li_watcher_page = 0

        activity_radar = Dashboard._get_activity_radar(self, asin=asin)
        if not activity_radar:
            others_asins = Dashboard._get_asins(self, user, ownership='Others')
            activity_radar = Dashboard._get_activity_radar(self, others_asins=others_asins)
            if activity_radar:
                activity_radar = activity_radar

        if activity_radar:
            activity_radar[0].title_re = activity_radar[0].title[0:90]
            activity_radar[0].title1_re = activity_radar[0].title1[0:90]
            activity_radar[0].description_re = activity_radar[0].description[0:90]
            activity_radar[0].description1_re = activity_radar[0].description1[0:90]
            activity_radar = activity_radar[0]
        else:
            activity_radar = []
        line_x = []
        line_price_y = []
        line_review_y = []
        for v in listing:
            if v.price:
                line_price_y.append(float(v.price[1:]))
            if v.total_review:
                line_review_y.append(int(v.total_review))
            line_x.append(int(v.created.strftime("%d")))

        positive_words = []
        for ar in asinreview:
            if ar.positive_keywords:
                ar.positive_keywords= eval(ar.positive_keywords)
                for a in ar.positive_keywords:
                    positive_words.append({'count':a,'words':ar.positive_keywords[a]})

        review_limit = self.GET.get('review_limit', 5)

        paginator = Paginator(review, review_limit)
        review_page = self.GET.get('review_page',1)
        try:
            review_data = paginator.page(review_page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            review_data = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            review_data = paginator.page(paginator.num_pages)

        for val in review_data:
            if val.review_date:
                val.review_date = val.review_date.strftime("%B %d, %Y")

        item.question_answer = str(question_count.count())+'/'+str(answer_count.count())
        box_res = eval(item.buy_box_res)
        if box_res:
            if 'Fulfilled by Amazon' in box_res:
                item.is_FBA = 'FBA'
            else:
                item.is_FBA = ''
            item.buy_box_res = box_res[0]
        else:
            item.buy_box_res = 'Amazon.com'
        if item.prime:
            item.prime = 'Prime'
        else:
            item.prime = ''
        if item.image_date:
            item.image_date = item.image_date.strftime("%Y-%m-%d")
        if item.created:
            item.created = item.created.strftime("%Y-%m-%d %H:%M:%S")
        if item.user_asin.last_check:
            item.user_asin.last_check = item.user_asin.last_check.strftime("%Y-%m-%d %H:%M:%S")
        else:
            item.user_asin.last_check = ''
        if item.user_asin.update_time:
            item.user_asin.update_time = item.user_asin.update_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            item.user_asin.update_time = ''
        if item.rvw_score:
            item.rvw_score = int(item.rvw_score)
        if item.category_rank:
            item.category_rank = item.category_rank.split('|')
        item.item_offer = item_offer

        data = {
            'user': user,
            'avator': user.user.username[0],
            'res':item,
            'asinreview':positive_words,
            'review':review_data,
            'review_page':review_page,
            'line_x':line_x,
            'line_price_y':line_price_y,
            'line_review_y':line_review_y,
            'activity_radar':activity_radar,
            'listing_watchers':listing_watchers,
            'li_watcher_page':li_watcher_page,
        }
        return render(self, 'listings/listingdetail.html',data)

    @csrf_exempt
    def ajax_get_watcher(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')
        asin = self.GET.get('asin','')
        page = self.GET.get('page',1)
        offset = (int(page)-1)*3

        listing_watchers = []
        listing_watchers_max = ListingWacher.objects.aggregate(Max('created'))
        listing_watchers = ListingWacher.objects.filter(asin=asin,
                                                        created__icontains=listing_watchers_max['created__max']. \
                                                        strftime("%Y-%m-%d"))
        if listing_watchers:
            listing_watchers = listing_watchers[offset:offset+3]
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
                'created':val.created.strftime('%Y-%m-%d %H:%M:%S'),
                'seller_link':val.seller_link,
                'seller':val.seller,
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
    def ajax_get_review(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')
        asin = self.GET.get('asin', '')
        is_vp = self.GET.get('is_vp', '')
        score = self.GET.get('score', '')
        rvKwd = self.GET.get('rvKwd', '')
        end_date = self.GET.get('end_date', '')
        start_date = self.GET.get('start_date', '')

        review = Reviews.objects.filter(asin=asin, created__icontains=Reviews.objects.aggregate(Max('created'))
        ['created__max'].strftime("%Y-%m-%d")).all()

        if is_vp:
            review = review.filter(is_vp=is_vp)
        if score and not score == 'positive' and not score == 'critical':
            review = review.filter(score=score)
        if score == 'positive':
            review = review.filter(score__gte=3)
        if score == 'critical':
            review = review.filter(score__lt=3)
        if rvKwd:
            review = review.filter(content__icontains=rvKwd)
        if end_date:
            review = review.filter(created__lte=end_date)
        if start_date:
            review = review.filter(created__gte=start_date)

        review_limit = self.GET.get('review_limit', 5)

        # paginator = Paginator(review, review_limit)
        review_page = self.GET.get('review_page',1)
        offset = (int(review_page)-1) * int(review_limit)
        page_limit = offset + int(review_limit)
        review = review.all()[offset:page_limit]
        is_page = 1
        if len(review) < 6:
            is_page = 0

        data = []
        for val in review:
            if val.created:
                val.created = val.created.strftime("%Y-%m-%d")
                val.review_date = val.review_date.strftime("%B %d, %Y")
                if val.is_vp == 1:
                    val.is_vp = 'Verified Purchase'
                else:
                    val.is_vp = ''
            data.append(model_to_dict(val))

        return HttpResponse(json.dumps({'code': 1, 'data': {'data':data,'review_page':review_page,'is_page':is_page}}), content_type='application/json')

    @csrf_exempt
    def ajax_get_radar(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')

        asin = self.GET.get('asin', '')
        page = int(self.GET.get('page', 1))

        activity_radar = Dashboard._get_activity_radar(self, asin=asin)
        if not activity_radar:
            others_asins = Dashboard._get_asins(self, user, ownership='Others')
            activity_radar = Dashboard._get_activity_radar(self, others_asins=others_asins)
            if activity_radar:
                activity_radar = activity_radar
        is_page = 1
        if len(activity_radar) < page+1:
            is_page = 0
            return HttpResponse(
                json.dumps({'code': 1, 'data': {'data':'','page': page, 'is_page': is_page}}),content_type='application/json')

        if activity_radar:
            activity_radar = {
                'title_re':activity_radar[page].title[0:90],
                'title1_re':activity_radar[page].title1[0:90],
                'description_re':activity_radar[page].description[0:90],
                'description1_re':activity_radar[page].description1[0:90],
                'created':activity_radar[page].created,
                'title':activity_radar[page].title,
                'price1':activity_radar[page].price1,
                'price':activity_radar[page].price,
                'title1':activity_radar[page].title1,
                'description':activity_radar[page].description,
                'description1':activity_radar[page].description1,
            }

        return HttpResponse(json.dumps({'code': 1, 'data': {'data':activity_radar,'page':page,'is_page':is_page}}),
                            content_type='application/json')

    @csrf_exempt
    def export_qa(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")

        asin = self.GET.get('qa_asin', '')

        qa_max = Questions.objects.aggregate(Max('created'))
        question = Questions.objects.filter(asin=asin, created__icontains=qa_max['created__max'].strftime("%Y-%m-%d"))
        answer = Answers.objects.filter(question__in=question)
        data = []
        for val in answer:
            re = {
                'question':val.question.question,
                'asin':val.question.asin,
                'asked':val.question.asked,
                'votes':val.question.votes,
                'answer':val.answer,
                'person':val.person,
                'created':val.created.strftime("%Y-%m-%d %H:%M:%S")
            }

            data.append(re)

        fields = [
            'Question',
            'Asin',
            'Asked',
            'Votes',
            'Answer',
            'Answerer',
            'Create Date'
        ]

        data_fields = [
            'question',
            'asin',
            'asked',
            'votes',
            'answer',
            'person',
            'created'
        ]

        return get_excel_file(self, data, fields, data_fields)

    @csrf_exempt
    def export_reviews(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")

        asin = self.GET.get('review_asin', '')
        is_vp = self.GET.get('is_vp', '')
        score = self.GET.get('score', '')
        rvKwd = self.GET.get('rvKwd', '')
        end_date = self.GET.get('end_date', '')
        start_date = self.GET.get('start_date', '')

        review = Reviews.objects.filter(asin=asin, created__icontains=Reviews.objects.aggregate(Max('created'))
        ['created__max'].strftime("%Y-%m-%d")).all()

        if is_vp:
            review = review.filter(is_vp=is_vp)
        if score and not score == 'positive' and not score == 'critical':
            review = review.filter(score=score)
        if score == 'positive':
            review = review.filter(score__gte=3)
        if score == 'critical':
            review = review.filter(score__lt=3)
        if rvKwd:
            review = review.filter(content__icontains=rvKwd)
        if end_date:
            review = review.filter(created__lte=end_date)
        if start_date:
            review = review.filter(created__gte=start_date)

        asinreview = AsinReviews.objects.filter(aid=asin,created__icontains=AsinReviews.objects.aggregate(Max('created'))
                                                ['created__max'].strftime("%Y-%m-%d")).all()

        data = []
        for val in review:
            re = {
                'title':val.title,
                'variation':val.variation,
                'asin':val.asin,
                'name':val.name,
                'score':val.score,
                'avg_score': asinreview[0].avg_score,
                'is_vp':val.is_vp,
                'review_date':val.review_date.strftime("%Y-%m-%d"),
                'content':val.content,
                'positive_keywords':asinreview[0].positive_keywords,
                'negative_keywords':asinreview[0].negative_keywords,
                'total_review':asinreview[0].total_review,
                'review_link':val.review_link,
                'created':val.created.strftime("%Y-%m-%d"),
            }
            data.append(re)

        fields = [
            'Title',
            'Variation',
            'Asin',
            'Name',
            'Score',
            'Avg Score',
            'VP',
            'Review Date',
            'Content',
            'Positive Keywords',
            'Negative Keywords',
            'Total Review',
            'Review Link',
            'Created'
        ]
        data_fields = [
            'title',
            'variation',
            'asin',
            'name',
            'score',
            'avg_score',
            'is_vp',
            'review_date',
            'content',
            'positive_keywords',
            'negative_keywords',
            'total_review',
            'review_link',
            'created'
        ]
        return get_excel_file(self, data, fields, data_fields)

    @csrf_exempt
    def ajax_chart(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")

        asin = self.GET.get('asin', '')
        tsData1 = self.GET.get('tsData1', '')
        tsData2 = self.GET.get('tsData2', '')
        tsStartDate = self.GET.get('tsStartDate', '')
        tsEndDate = self.GET.get('tsEndDate', '')
        listing = Listings.objects.filter(asin=asin).order_by('-created')
        if tsStartDate:
            listing = listing.filter(created__gte=tsStartDate)
        if tsEndDate:
            listing = listing.filter(created__gte=tsEndDate)

        line_x = []
        line_y1 = []
        line_y2 = []
        for v in listing:
            if v.price:
                if tsData1 == 'price':
                    line_y1.append(float(v.price[1:]))
                if tsData2 == 'price':
                    line_y2.append(float(v.price[1:]))
            if v.total_review:
                if tsData1 == 'reviews':
                    line_y1.append(int(v.total_review))
                if tsData2 == 'reviews':
                    line_y2.append(int(v.total_review))
            if v.rvw_score:
                if tsData1 == 'score':
                    line_y1.append(float(v.rvw_score))
                if tsData2 == 'score':
                    line_y2.append(float(v.rvw_score))
            if v.total_qa:
                if tsData1 == 'qa':
                    line_y1.append(int(v.total_qa))
                if tsData2 == 'qa':
                    line_y2.append(int(v.total_qa))
            line_x.append(int(v.created.strftime("%d")))

        return HttpResponse(json.dumps({'code': 1, 'data': {'line_x':line_x,'line_y1':line_y1,'line_y2':line_y2}}),
                            content_type='application/json')

    @csrf_exempt
    def export_shuttle(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")

        asin = self.GET.get('shuttle_asin', '')
        tsStartDate = self.GET.get('tsStartDate', '')
        tsEndDate = self.GET.get('tsEndDate', '')
        listing = Listings.objects.filter(asin=asin).order_by('-created')
        if tsStartDate:
            listing = listing.filter(created__gte=tsStartDate)
        if tsEndDate:
            listing = listing.filter(created__gte=tsEndDate)
        data = []
        for v in listing:
            re = {
                'image_names':v.image_thumbs,
                'title':v.title,
                'asin':v.asin,
                'sku':v.sku,
                'description':v.description,
                'feature':v.feature,
                'buy_box':v.buy_box,
                'price':v.price,
                'total_review':v.total_review,
                'total_qa':v.total_qa,
                'rvw_score':v.rvw_score,
                'category_rank':v.category_rank,
                'inventory':v.inventory,
                'last_check':v.user_asin.last_check.strftime("%Y-%m-%d %H:%M:%S"),
                'created':v.created.strftime("%Y-%m-%d %H:%M:%S"),
                'image_date':v.image_date.strftime("%Y-%m-%d"),
            }
            data.append(re)

        fields = [
            'Image Names',
            'Ttile',
            'Asin',
            'SKU',
            'Description',
            'Feature',
            'Buy Box',
            'Price',
            'Total Review',
            'Total Qa',
            'Rvw Score',
            'Category Rank',
            'Inventory',
            'Last Check',
            'Created',
            'Image Date'
        ]

        data_fields = [
            'title',
            'asin',
            'sku',
            'description',
            'feature',
            'buy_box',
            'price',
            'total_review',
            'total_qa',
            'rvw_score',
            'category_rank',
            'inventory',
            'last_check',
            'created',
            'image_date'
        ]
        return get_excel_file(self, data, fields, data_fields)



