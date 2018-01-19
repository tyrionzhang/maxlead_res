# -*- coding: utf-8 -*-
import json,datetime
from django.shortcuts import render,HttpResponse
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Max
from django.db.models import Q
from maxlead_site.models import Questions,Answers,Reviews,UserProfile,Task
from maxlead_site.views.app import App
from maxlead_site.common.excel_world import get_excel_file,get_excel_file1

class Miner:

    @csrf_exempt
    def index(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        viewRange = int(self.GET.get('viewRange', user.user.id))
        user_list = UserProfile.objects.filter(state=1)
        if user.role == 0:
            user_list = user_list.filter(id=user.id)
        if user.role == 1:
            user_list = user_list.filter(Q(group=user) | Q(id=user.id))
        users = []
        if user_list:
            for val in user_list:
                users.append(val.user_id)
        tasks = Task.objects.filter(user_id__in=users)
        if viewRange:
            tasks = tasks.filter(user_id=viewRange)

        if tasks:
            data = []
            for v in tasks:
                v.created = v.created.strftime('%Y-%m-%d %H:%M:%S')
                if v.finish_time:
                    v.finish_time = v.finish_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    v.finish_time = ''
                if v.type == 0:
                    v.type = 'Review'
                else:
                    v.type = 'QA'

        limit = self.GET.get('limit', 6)
        page = self.GET.get('page', 1)

        total_count = len(tasks)
        total_page = round(len(tasks)/int(limit))
        if int(limit) >= total_count:
            limit = total_count
        if tasks:
            paginator = Paginator(tasks, limit)
            try:
                tasks_data = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                tasks_data = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                tasks_data = paginator.page(paginator.num_pages)
            data = {
                'data': tasks_data,
                'total_count': total_count,
                'total_page': total_page,
                'limit': limit,
                'page': page,
                'user': user,
                'viewRange': viewRange,
                'avator': user.user.username[0],
                'user_list': user_list
            }
        else:
            data = {
                'data': '',
                'total_count': total_count,
                'total_page': total_page,
                'limit': limit,
                'page': page,
                'user': user,
                'viewRange': viewRange,
                'avator': user.user.username[0],
                'user_list': user_list
            }
        return render(self, 'miner/miner.html', data)


    @csrf_exempt
    def add(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponse(json.dumps({'code': 0, 'msg': '请登陆！'}),content_type='application/json')

        type = int(self.POST.get('taskType',1))
        name = self.POST.get('taskName','')
        description = self.POST.get('taskDesc','')
        asins = self.POST.get('taskASIN','')

        if asins:
            data = []
            asins = asins.split('|')
            tasks = Task.objects.filter(type=type, created__icontains=datetime.datetime.now().strftime('%Y-%m-%d'))
            if tasks:
                file_path = ''
                for val in tasks:
                    if len(eval(val.asins)) == len(asins) and set(eval(val.asins)).issubset(set(asins)):
                        file_path = val.file_path
                if file_path:
                    return HttpResponse(json.dumps({'code': 1, 'data': {'file_path': file_path, 'f_time': 'finish'}}), content_type='application/json')
            if type == 0:
                reviews = Reviews.objects.filter(asin__in=asins,created__icontains=Reviews.objects.aggregate(Max('created'))
                                                                            ['created__max']).all()
                if reviews:
                    for v in reviews:
                        re = {
                            'title':v.title,
                            'name':v.name,
                            'asin':v.asin,
                            'variation':v.variation,
                            'content':v.content,
                            'review_link':v.review_link,
                            'score':v.score,
                            'is_vp':v.is_vp,
                            'review_date':v.review_date.strftime('%Y-%m-%d'),
                            'created':v.created.strftime('%Y-%m-%d'),
                        }
                        data.append(re)
                    fields = [
                        'Title',
                        'Name',
                        'Asin',
                        'Variation',
                        'Content',
                        'Review Link',
                        'Score',
                        'Vp',
                        'Review Date',
                        'Created'
                    ]

                    data_fields = [
                        'title',
                        'name',
                        'asin',
                        'variation',
                        'content',
                        'review_link',
                        'score',
                        'is_vp',
                        'review_date',
                        'created'
                    ]
            else:
                qa_max = Questions.objects.aggregate(Max('created'))
                questions = Questions.objects.filter(asin__in=asins, created__icontains=qa_max['created__max'].strftime("%Y-%m-%d"))
                answers = Answers.objects.filter(question__in=questions)
                if answers:
                    for v in answers:
                        re = {
                            'question':v.question.question,
                            'asin':v.question.asin,
                            'asked':v.question.asked,
                            'votes':v.question.votes,
                            'answer':v.answer,
                            'person':v.person,
                            'created':v.created.strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        data.append(re)

                        fields = [
                            'Question',
                            'Asin',
                            'Asked',
                            'Votes',
                            'Answer',
                            'Person',
                            'Created'
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
            if data:
                task = Task()
                task.id
                task.name = name
                task.user = user.user
                task.type = int(type)
                task.description = description
                task.asins = asins
                task.save()

                file_path = get_excel_file1(self, data, fields, data_fields)
                id = task.id
                f_time = datetime.datetime.now()
                Task.objects.filter(id=id).update(file_path=file_path, finish_time=f_time)
                return HttpResponse(json.dumps({'code': 1, 'data': {'id': id, 'file_path': file_path, 'f_time':\
                                                    f_time.strftime('%Y-%m-%d %H:%M:%S')}}),content_type='application/json')
            else:
                return HttpResponse(json.dumps({'code': 0, 'msg': '没有数据！'}), content_type='application/json')

        else:
            return HttpResponse(json.dumps({'code': 0, 'data': '任务添加失败！'}),content_type='application/json')
