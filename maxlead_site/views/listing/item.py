# -*- coding: utf-8 -*-
import json,datetime,calendar
from dateutil.relativedelta import relativedelta
from django.shortcuts import render,HttpResponse
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max
from maxlead_site.models import Listings,UserAsins,Questions,Answers,Reviews,AsinReviews,ListingWacher,CategoryRank
from maxlead_site.views.app import App
from maxlead_site.common.excel_world import get_excel_file
from maxlead_site.common.common import get_review_keywords
from maxlead_site.views.dashboard.dashboard import Dashboard

class Item:

    def item(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        asin = self.GET.get('asin', '')
        listing_max = Listings.objects.filter(asin=asin).aggregate(Max('created'))
        if not listing_max or not listing_max['created__max']:
            listing_max = Listings.objects.aggregate(Max('created'))
        start_time = datetime.datetime.now().strftime("%Y-%m-1")
        end_time = listing_max['created__max'].strftime("%Y-%m-%d")
        if int(datetime.datetime.now().strftime("%d")) <= 5:
            mid_time = datetime.datetime.now() - relativedelta(months=+1)
            mid_days = calendar.monthrange(mid_time.year, mid_time.month)
            start_time = mid_time.strftime("%Y-%m-1")
            end_time = mid_time.strftime("%Y-%m-" + str(mid_days[1]))
        listing = Listings.objects.filter(asin=asin).filter(created__gte=start_time).filter(created__lte=end_time).order_by('-created')
        if not listing:
            item = Listings.objects.filter(asin=asin).filter(created__icontains=listing_max['created__max'].strftime("%Y-%m-%d"))[0]
        else:
            item = listing[0]
        catgorys = []
        if item.user_asin.cat1:
            catgorys.append(item.user_asin.cat1)
        if item.user_asin.cat2:
            catgorys.append(item.user_asin.cat2)
        if item.user_asin.cat3:
            catgorys.append(item.user_asin.cat3)

        UserAsins.objects.filter(id=item.user_asin.id).update(last_check=datetime.datetime.now())
        qa_max = Questions.objects.filter(asin=item.asin).aggregate(Max('created'))
        if not qa_max or not qa_max['created__max']:
            qa_max = Questions.objects.aggregate(Max('created'))
        question_count = Questions.objects.filter(asin=item.asin,created__icontains=qa_max['created__max'].strftime("%Y-%m-%d"))
        answer_count = item.answered
        listing_watchers = []
        listing_watchers_max = ListingWacher.objects.filter(asin=item.asin).aggregate(Max('created'))
        if not listing_watchers_max or not listing_watchers_max['created__max']:
            listing_watchers_max = ListingWacher.objects.aggregate(Max('created'))
        if listing_watchers_max and listing_watchers_max['created__max']:
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

        if activity_radar:
            for val in activity_radar:
                if val['text1']:
                    val['text1'] = val['text1'][0:90]
                if val['text2']:
                    val['text2'] = val['text2'][0:90]
            # activity_radar[0].title_re = activity_radar[0].title[0:90]
            # activity_radar[0].title1_re = activity_radar[0].title1[0:90]
            # activity_radar[0].description_re = activity_radar[0].description[0:90]
            # activity_radar[0].description1_re = activity_radar[0].description1[0:90]
            # activity_radar = activity_radar[0]
        else:
            activity_radar = []

        item.question_answer = str(answer_count)+'/'+str(question_count.count())
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
            'activity_radar':activity_radar,
            'listing_watchers':listing_watchers,
            'li_watcher_page':li_watcher_page,
            'catgorys':catgorys,
            'asin':asin,
        }
        return render(self, 'listings/listingdetail.html',data)

    @csrf_exempt
    def ajax_get_watcher(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')
        asin = self.GET.get('asin','')
        page = self.GET.get('page',1)
        listBgn = self.GET.get('listBgn','')
        listEnd = self.GET.get('listEnd','')
        offset = (int(page)-1)*3

        listing_watchers = []
        listing_watchers_max = ListingWacher.objects.filter(asin=asin).aggregate(Max('created'))
        if not listing_watchers_max or not listing_watchers_max['created__max']:
            listing_watchers_max = ListingWacher.objects.aggregate(Max('created'))
        listing_watchers = ListingWacher.objects.filter(asin=asin,created__icontains=listing_watchers_max['created__max']. \
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
        rvSort = self.GET.get('rvSort', '')
        words = self.GET.get('words', '')

        review_max = Reviews.objects.filter(asin=asin).aggregate(Max('created'))
        if not review_max or not review_max['created__max']:
            review_max = Reviews.objects.aggregate(Max('created'))
        review = Reviews.objects.filter(asin=asin, created__icontains=review_max['created__max'].strftime("%Y-%m-%d")).all()

        if is_vp:
            review = review.filter(is_vp=is_vp)
        if score and not score == 'positive' and not score == 'critical':
            review = review.filter(score=score)
        if score == 'positive':
            review = review.filter(score__gt=3)
        if score == 'critical':
            review = review.filter(score__lte=3)
        if rvKwd:
            review = review.filter(content__icontains=rvKwd)
        if words:
            review = review.filter(content__icontains=words)
        if end_date:
            review = review.filter(review_date__lte=end_date)
        if start_date:
            review = review.filter(review_date__gte=start_date)
        if rvSort:
            if rvSort == 'newest':
                review = review.order_by('-review_date')
            elif rvSort == 'top':
                review = review.order_by('-score')
            else:
                review = review.order_by('review_date')

        asinreviews = get_review_keywords(review)
        positive_words = asinreviews['positive_keywords']
        negative_keywords = asinreviews['negative_keywords']
        review_limit = self.GET.get('review_limit', 6)

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

        return HttpResponse(json.dumps({'code': 1, 'data': {'data':data,'review_page':review_page,'is_page':is_page,
                                                            'positive_words':positive_words,'negative_keywords':negative_keywords}}),
                                                            content_type='application/json')

    @csrf_exempt
    def ajax_get_radar(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')

        asin = self.GET.get('asin', '')
        page = int(self.GET.get('page', 1))

        activity_radar = Dashboard._get_activity_radar(self, asin=asin)
        is_page = 1
        if len(activity_radar) < page+1:
            is_page = 0
            return HttpResponse(
                json.dumps({'code': 1, 'data': {'data':'','page': page, 'is_page': is_page}}),content_type='application/json')

        if activity_radar:
            for val in activity_radar:
                val['text1'] = val['text1'][0:90]
                val['text2'] = val['text2'][0:90]

        return HttpResponse(json.dumps({'code': 1, 'data': {'data':activity_radar,'page':page,'is_page':is_page}}),
                            content_type='application/json')

    @csrf_exempt
    def ajax_k_rank(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '用户未登录'}), content_type='application/json')
        asin = self.GET.get('asin','')
        krStartDate = self.GET.get('krStartDate',datetime.datetime.now().strftime("%Y-%m-1"))
        krEndDate = self.GET.get('krEndDate',datetime.datetime.now().strftime("%Y-%m-d"))
        kwdCat = self.GET.get('kwdCat','')

        ranks = CategoryRank.objects.filter(asin=asin,user_asin=asin)
        if kwdCat:
            ranks = ranks.filter(cat__icontains=kwdCat)
        if krStartDate:
            ranks = ranks.filter(created__gte=krStartDate)
        if krEndDate:
            ranks = ranks.filter(created__lte=krEndDate)

        line_x = []
        cat_y = {}
        keywords_y = {}
        keycat_y = {}
        for val in ranks:
            if val.cat and not val.keywords:
                keys = val.cat.split(',n:')[-1]
                if keys in cat_y:
                    cat_y[keys] += ','+str(val.rank)
                    cat_y['time'+keys] += ',' + val.created.strftime("%d")
                else:
                    cat_y.update({keys:str(val.rank)})
                    cat_y.update({'time'+keys:val.created.strftime("%d")})

            if val.keywords and not val.cat:
                if val.keywords in keywords_y:
                    keywords_y[val.keywords] += ','+str(val.rank)
                    keywords_y['time'+val.keywords] += ',' + val.created.strftime("%d")
                else:
                    keywords_y.update({val.keywords:str(val.rank)})
                    keywords_y.update({'time'+val.keywords:val.created.strftime("%d")})

            if val.keywords and  val.cat:
                keys_c = val.cat.split(',n:')[-1]
                if val.keywords+'/'+keys_c in keycat_y:
                    keycat_y[val.keywords+'/'+keys_c] += ','+str(val.rank)
                    keycat_y['time'+val.keywords+'/'+keys_c] += ',' + val.created.strftime("%d")
                else:
                    keycat_y.update({val.keywords+'/'+keys_c:str(val.rank)})
                    keycat_y.update({'time'+val.keywords+'/'+keys_c:val.created.strftime("%d")})

        chart = []
        if cat_y:
            for i in cat_y:
                cat_y[i] = cat_y[i].split(',')
            chart.append(cat_y)
        if keywords_y:
            for k in keywords_y:
                keywords_y[k] = keywords_y[k].split(',')
            chart.append(keywords_y)
        if keycat_y:
            for k in keycat_y:
                keycat_y[k] = keycat_y[k].split(',')

            chart.append(keycat_y)

        return HttpResponse(json.dumps({'code': 1, 'data': {'chart': chart}}),content_type='application/json')


    @csrf_exempt
    def export_qa(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")

        asin = self.GET.get('qa_asin', '')

        qa_max = Questions.objects.filter(asin=asin).aggregate(Max('created'))
        if not qa_max or not qa_max['created__max']:
            qa_max = Questions.objects.aggregate(Max('created'))
        question = Questions.objects.filter(asin=asin, created__icontains=qa_max['created__max'].strftime("%Y-%m-%d"))
        if not question:
            return HttpResponseRedirect("")

        data = []
        for q in question:
            answer = Answers.objects.filter(question_id=q.id)
            if answer:
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
            else:
                re = {
                    'question': q.question,
                    'asin': q.asin,
                    'asked': q.asked,
                    'votes': q.votes,
                    'answer': '',
                    'person': '',
                    'created': q.created.strftime("%Y-%m-%d %H:%M:%S")
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
        words = self.GET.get('words', '')

        review_max = Reviews.objects.filter(asin=asin).aggregate(Max('created'))
        if not review_max or not review_max['created__max']:
            review_max = Reviews.objects.aggregate(Max('created'))
        review = Reviews.objects.filter(asin=asin, created__icontains=review_max['created__max'].strftime("%Y-%m-%d")).all()

        if is_vp:
            review = review.filter(is_vp=is_vp)
        if score and not score == 'positive' and not score == 'critical':
            review = review.filter(score=score)
        if score == 'positive':
            review = review.filter(score__gt=3)
        if score == 'critical':
            review = review.filter(score__lte=3)
        if rvKwd:
            review = review.filter(content__icontains=rvKwd)
        if words:
            review = review.filter(content__icontains=words)
        if end_date:
            review = review.filter(review_date__lte=end_date)
        if start_date:
            review = review.filter(review_date__gte=start_date)
        a_max = AsinReviews.objects.filter(aid=asin).aggregate(Max('created'))
        if not a_max or not a_max['created__max']:
            a_max = AsinReviews.objects.aggregate(Max('created'))
        asinreview = AsinReviews.objects.filter(aid=asin,created__icontains=a_max['created__max'].strftime("%Y-%m-%d")).all()
        asinreviews = get_review_keywords(review)
        positive_keywords = ''
        negative_keywords = ''
        if asinreviews['positive_keywords']:
            for val in asinreviews['positive_keywords']:
                positive_keywords += val['words']+','
        if asinreviews['negative_keywords']:
            for val in asinreviews['negative_keywords']:
                negative_keywords += val['words']+','
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
                'positive_keywords':positive_keywords,
                'negative_keywords':negative_keywords,
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
        tsStartDate = self.GET.get('tsStartDate', datetime.datetime.now().strftime("%Y-%m-1"))
        tsEndDate = self.GET.get('tsEndDate', datetime.datetime.now().strftime("%Y-%m-%d"))
        listing = Listings.objects.filter(asin=asin).order_by('-created')
        if tsStartDate:
            listing = listing.filter(created__gte=tsStartDate)
        if tsEndDate:
            listing = listing.filter(created__lte=tsEndDate)

        line_x1 = []
        line_x2 = []
        line_y1 = []
        line_y2 = []
        name1 = ''
        name2 = ''
        for v in listing:
            if tsData1 == 'bsr' or tsData2 == 'bsr':
                cate_rank = 0
                if v.category_rank:
                    cate_rank = v.category_rank.split(' in')
                    cate_rank = cate_rank[0].split('#')[1]
                    cate_rank = cate_rank.replace(',','')
                if tsData1 == 'bsr':
                    name1 = 'BSR'
                    line_x1.append(int(v.created.strftime("%d")))
                    line_y1.append(cate_rank)
                if tsData2 == 'bsr':
                    name2 = 'BSR'
                    line_x2.append(int(v.created.strftime("%d")))
                    line_y2.append(cate_rank)
            if v.price:
                if tsData1 == 'price':
                    name1 = 'price'
                    line_x1.append(int(v.created.strftime("%d")))
                    line_y1.append(float(v.price[1:]))
                if tsData2 == 'price':
                    name2 = 'price'
                    line_x2.append(int(v.created.strftime("%d")))
                    line_y2.append(float(v.price[1:]))
            if v.total_review:
                if tsData1 == 'reviews':
                    name1 = 'reviews'
                    line_x1.append(int(v.created.strftime("%d")))
                    line_y1.append(int(v.total_review))
                if tsData2 == 'reviews':
                    name2 = 'reviews'
                    line_x2.append(int(v.created.strftime("%d")))
                    line_y2.append(int(v.total_review))
            if v.rvw_score:
                if tsData1 == 'score':
                    name1 = 'score'
                    line_x1.append(int(v.created.strftime("%d")))
                    line_y1.append(float(v.rvw_score))
                if tsData2 == 'score':
                    name2 = 'score'
                    line_x2.append(int(v.created.strftime("%d")))
                    line_y2.append(float(v.rvw_score))
            if v.total_qa:
                if tsData1 == 'qa':
                    name1 = 'qa'
                    line_x1.append(int(v.created.strftime("%d")))
                    line_y1.append(int(v.total_qa))
                if tsData2 == 'qa':
                    name2 = 'qa'
                    line_x2.append(int(v.created.strftime("%d")))
                    line_y2.append(int(v.total_qa))

        return HttpResponse(json.dumps({'code': 1, 'data': {'line_x1':line_x1,'line_x2':line_x2,'line_y1':line_y1,'line_y2':line_y2,'name1':name1,
                                                            'name2':name2}}),content_type='application/json')

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

    @csrf_exempt
    def export_k_rank(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        asin = self.GET.get('asin', '')
        krStartDate = self.GET.get('krStartDate', datetime.datetime.now().strftime("%Y-%m-1"))
        krEndDate = self.GET.get('krEndDate', datetime.datetime.now().strftime("%Y-%m-%d"))
        kwdCat = self.GET.get('kwdCat', '')

        ranks = CategoryRank.objects.filter(asin=asin, user_asin=asin)
        if kwdCat:
            ranks = ranks.filter(cat__icontains=kwdCat)
        if krStartDate:
            ranks = ranks.filter(created__gte=krStartDate)
        if krEndDate:
            ranks = ranks.filter(created__lte=krEndDate)

        data = []
        for v in ranks:
            re = {
                'asin': v.asin,
                'cat': v.cat,
                'keywords': v.keywords,
                'rank': v.rank,
                'is_ad': v.is_ad,
                'created': v.created.strftime("%Y-%m-%d %H:%M:%S"),
            }
            data.append(re)

        fields = [
            'Asin',
            'Cat',
            'Keywords',
            'Rank',
            'AD',
            'Created',
        ]
        data_fields = [
            'asin',
            'cat',
            'keywords',
            'rank',
            'is_ad',
            'created',
        ]
        if data:
            return get_excel_file(self, data, fields, data_fields)


