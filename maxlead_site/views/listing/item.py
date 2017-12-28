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
        id = self.GET.get('id', '')

        item = Listings.objects.get(id=int(id))
        UserAsins.objects.filter(id=item.user_asin.id).update(last_check=datetime.datetime.now())
        qa_max = Questions.objects.aggregate(Max('created'))
        question_count = Questions.objects.filter(asin=item.asin,created__icontains=qa_max['created__max'].strftime("%Y-%m-%d"))
        answer_count = Answers.objects.filter(question__in=question_count)
        asinreview = AsinReviews.objects.filter(aid=item.asin,created__icontains=AsinReviews.objects.aggregate(Max('created'))
                                                                            ['created__max'].strftime("%Y-%m-%d")).all()
        review = Reviews.objects.filter(asin=item.asin,created__icontains=Reviews.objects.aggregate(Max('created'))
                                                                            ['created__max'].strftime("%Y-%m-%d")).all()

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

        data = {
            'user': user,
            'avator': user.user.username[0],
            'res':item,
            'asinreview':positive_words,
            'review':review_data,
            'review_page':review_page,
        }
        return render(self, 'listings/listingdetail.html',data)

    @csrf_exempt
    def ajax_get_review(self):
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
        # try:
        #     review_data = paginator.page(review_page)
        # except PageNotAnInteger:
        #     # If page is not an integer, deliver first page.
        #     review_data = paginator.page(1)
        # except EmptyPage:
        #     # If page is out of range (e.g. 9999), deliver last page of results.
        #     review_data = paginator.page(paginator.num_pages)
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
