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
from maxlead_site.common.excel_world import read_excel_file1,get_excel_file

@csrf_exempt
def email_temps(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('search_words','').replace('amp;','')
    send_time = request.GET.get('search_send_time','')
    order_status = request.GET.get('search_order_status','')
    list = EmailTemplates.objects.filter(customer_num=user.menu_child_type)
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
        customer_num = request.POST.get('customer_num','')
        keywords = request.POST.get('keywords','')
        send_time = request.POST.get('send_time','')
        order_status = request.POST.get('order_status','')
        content = request.POST.get('content','')
        sku = sku.strip()
        if not id:
            obj = EmailTemplates()
            obj.id
            obj.order_status = int(order_status)
            obj.sku = sku
            obj.customer_num = customer_num
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
            i = re.update(sku=sku,title=title,content=content,send_time=send_time,order_status=order_status,keywords=keywords,customer_num=customer_num)
            if i:
                return HttpResponse(json.dumps({'code': 1, 'msg': 'Work is Done!'}), content_type='application/json')

@csrf_exempt
def branch_edit_tmp(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        ids = eval(request.POST.get('data',''))
        keywords = request.POST.get('keywords','')
        title = request.POST.get('title','')
        send_time = request.POST.get('send_time','')
        status = request.POST.get('status','')
        content = request.POST.get('content','')
        update_fields = []
        if keywords:
            update_fields.append('keywords')
        if title:
            update_fields.append('title')
        if send_time:
            update_fields.append('send_time')
        if status:
            update_fields.append('order_status')
        if content:
            update_fields.append('content')
        for val in ids:
            try:
                obj = EmailTemplates()
                obj.id = int(val)
                if keywords:
                    obj.keywords = keywords
                if title:
                    obj.title = title
                if send_time:
                    obj.send_time = send_time
                if status:
                    obj.order_status = status
                if content:
                    obj.content = content
                obj.save(update_fields=update_fields)
            except:
                continue
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
        customer_num = request.POST.get('customer_num','')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}),content_type='application/json')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        res = read_excel_file1(EmailTemplates,file_path,'email_templates',user=user.user_id,customer_num=customer_num)
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def batch_del_tmp(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        ids = eval(request.POST.get('data',''))
        if not ids:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'请选择要删除的模板！'}), content_type='application/json')
        obj = EmailTemplates.objects.filter(id__in=ids)
        if not obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'请求的数据不存在！'}), content_type='application/json')
        obj.delete()
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')

@csrf_exempt
def tmp_export(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;', '')
    send_time = request.GET.get('send_time', '')
    order_status = request.GET.get('order_status', '')
    list = EmailTemplates.objects.filter(customer_num=user.menu_child_type)
    if not user.user.is_superuser:
        list = list.filter(user_id=user.user.id)
    if keywords:
        list = list.filter(Q(sku__contains=keywords) | Q(title__contains=keywords) | Q(content__contains=keywords))
    if send_time:
        list = list.filter(send_time=send_time)
    if order_status:
        list = list.filter(order_status=order_status)

    data = []
    if list:
        for val in list:
            re = {
                'sku':val.sku,
                'keywords':val.keywords,
                'title':val.title,
                'content':val.content,
                'order_status':val.order_status,
                'send_time':val.send_time,
                'created':''
            }
            data.append(re)

        fields = ['SKU','Keywords','Title','Content','Order Status','Send Time','Created']
        data_fields = ['sku','keywords','title','content','order_status','send_time','created']
        return get_excel_file(request, data, fields, data_fields)
    else:
        return HttpResponse('没有数据~~')