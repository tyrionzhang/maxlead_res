# -*- coding: utf-8 -*-
import json,datetime
from django.shortcuts import render,HttpResponse
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count,Max
from maxlead_site.models import Listings,UserAsins,Questions,Answers,Reviews,AsinReviews
from maxlead_site.views.app import App
from maxlead_site.common.excel_world import get_excel_file

class Item:

    def item(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        asin = self.GET.get('asin', '')
        listing_max = Listings.objects.aggregate(Max('created'))
        listing = Listings.objects.filter(asin=asin).filter(created__gte=listing_max['created__max'].strftime("%Y-%m-1"))\
            .filter(created__lte=listing_max['created__max']).order_by('-created')
        item = listing[0]
        UserAsins.objects.filter(id=item.user_asin.id).update(last_check=datetime.datetime.now())
        qa_max = Questions.objects.aggregate(Max('created'))
        question_count = Questions.objects.filter(asin=item.asin,created__icontains=qa_max['created__max'].strftime("%Y-%m-%d"))
        answer_count = Answers.objects.filter(question__in=question_count)
        asinreview = AsinReviews.objects.filter(aid=item.asin,created__icontains=AsinReviews.objects.aggregate(Max('created'))
                                                                            ['created__max'].strftime("%Y-%m-%d")).all()
        review = Reviews.objects.filter(asin=item.asin,created__icontains=Reviews.objects.aggregate(Max('created'))
                                                                            ['created__max'].strftime("%Y-%m-%d")).all()
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
        if item.user_asin.keywords:
            item.user_asin.keywords = item.user_asin.keywords.split('|')
        if item.user_asin.cat:
            item.user_asin.cat = item.user_asin.cat.split('|')

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
        }
        return render(self, 'listings/listingdetail.html',data)

    @csrf_exempt
    def ajax_get_review(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
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

        return HttpResponse(json.dumps({'code': 1, 'data': {'data':data,'review_page':review_page}}), content_type='application/json')

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


