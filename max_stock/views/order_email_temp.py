# -*- coding: utf-8 -*-
import os,json
from datetime import *
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import EmailTemplates
from maxlead_site.views.app import App
from django.db.models import Q
from maxlead import settings
from maxlead_site.common.excel_world import read_excel_file1

@csrf_exempt
def email_temps(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('search_words','').replace('amp;','')
    send_time = request.GET.get('search_send_time','')
    order_status = request.GET.get('search_order_status','')
    list = EmailTemplates.objects.all()
    if not user.user.is_superuser:
        list = list.filter(user_id=user.user.id)
    if keywords:
        list = list.filter(Q(sku__contains=keywords)| Q(title__contains=keywords)| Q(content__contains=keywords))
    if send_time:
        list = list.filter(send_time=send_time)
    if order_status:
        list = list.filter(order_status=order_status)

    data = {
        'list': list,
        'user': user,
        'keywords': keywords,
        'send_time': send_time,
        'order_status': order_status,
        'title': 'Email Templates',
    }

    return render(request, "Stocks/send_email/email_temp.html", data)

@csrf_exempt
def tmp_save(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        sku = request.POST.get('sku','').replace('amp;','')
        title = request.POST.get('title','')
        keywords = request.POST.get('keywords','')
        send_time = request.POST.get('send_time','')
        order_status = request.POST.get('order_status','')
        content = request.POST.get('content','')
        if not id:
            obj = EmailTemplates()
            obj.id
            obj.order_status = int(order_status)
            obj.sku = sku
            obj.user_id = user.user.id
            obj.keywords = keywords
            obj.title = title
            obj.content = content
            obj.send_time = send_time
            obj.save()
            if obj.id:
                return HttpResponse(json.dumps({'code': 1, 'msg': 'Work is Done!'}), content_type='application/json')
        else:
            id = int(id)
            re = EmailTemplates.objects.filter(id=id)
            if not re:
                return HttpResponse(json.dumps({'code': 0, 'msg': 'Template is not exits!'}), content_type='application/json')
            i = re.update(sku=sku,title=title,content=content,send_time=send_time,order_status=order_status,keywords=keywords)
            if i:
                return HttpResponse(json.dumps({'code': 1, 'msg': 'Work is Done!'}), content_type='application/json')

@csrf_exempt
def del_tmp(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        id = request.POST.get('id','')
        re = EmailTemplates.objects.filter(id=id)
        if not re:
            return HttpResponse(json.dumps({'code': 0, 'msg': 'Template is not exits!'}),
                                content_type='application/json')
        re.delete()
        return HttpResponse(json.dumps({'code': 1, 'msg': 'Work is Done!'}), content_type='application/json')

@csrf_exempt
def tmp_import(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        myfile = request.FILES.get('myfile','')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}),content_type='application/json')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        res = read_excel_file1(EmailTemplates,file_path,'email_templates',user=user.user_id)
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')
