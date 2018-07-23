# -*- coding: utf-8 -*-
import json
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import AmazonCode,OrderItems
from maxlead_site.views.app import App
from django.db.models import Q


@csrf_exempt
def code_index(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    code_list = AmazonCode.objects.all()
    data = {
        'code_list': code_list,
        'user': user,
        'title': 'AmazonCode',
    }
    return render(request, "Stocks/auto_email/codes.html", data)

@csrf_exempt
def code_save(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66}), content_type='application/json')

    if request.method == 'POST':
        id = request.POST.get('id','')
        email = request.POST.get('email','')
        code = request.POST.get('code','')
        if not id:
            code_obj = AmazonCode()
            code_obj.id
            code_obj.email = email
            code_obj.code = code
            code_obj.save()
            if code_obj.id:
                return HttpResponse(json.dumps({'code': 1, 'msg': '保存成功！'}), content_type='application/json')
        else:
            code_obj = AmazonCode.objects.filter(id=id)
            re = code_obj.update(code=code)
            if re:
                return HttpResponse(json.dumps({'code': 1, 'msg': '保存成功！'}), content_type='application/json')

@csrf_exempt
def orders(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '')
    order_list = OrderItems.objects.all()
    if keywords:
        order_list = order_list.filter(Q(order_id__contains=keywords)|Q(sku__contains=keywords)|Q(email__contains=keywords))
    data = {
        'order_list': order_list,
        'user': user,
        'title': 'Orders',
    }
    return render(request, "Stocks/auto_email/orders.html", data)

