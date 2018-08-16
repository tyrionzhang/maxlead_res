# -*- coding: utf-8 -*-
import os,json,threading,smtplib
from datetime import *
import time
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import OrderItems,OldOrderItems,EmailTemplates,NoSendRes
from maxlead_site.views.app import App
from django.db.models import Q
from maxlead import settings
from maxlead_site.common.excel_world import read_excel_for_orders,read_excel_file1
from django.core.mail import send_mail
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import parseaddr,formataddr
from maxlead_site.common import common

def _get_send_time(time_str):
    time_now = datetime.now()
    time_saturday = time_now.strftime('%Y-%m-%d ') + time_str
    time_saturday = datetime.strptime(time_saturday, '%Y-%m-%d %H:%M')
    t_re = (time_saturday - time_now).total_seconds()
    if t_re < 0:
        time_re = datetime.now() + timedelta(days=1)
        time_saturday = time_re.strftime('%Y-%m-%d ') + time_str
        time_saturday = datetime.strptime(time_saturday, '%Y-%m-%d %H:%M')
        t_re = (time_saturday - time_now).total_seconds()
    return t_re

def send_email_as_tmp(title, msg, from_email, email):
    smtp_server = 'smtp.gmail.com'
    from_addr = 'maxlead.us@gmail.com'
    to_addr = email
    password = "FF04JEsNKsRgvd>j2ES68iA0"
    if from_email and from_email.email_pass:
        if from_email.smtp_server:
            smtp_server = from_email.smtp_server
        from_addr = from_email.other_email
        password = common.decrypt(16, from_email.email_pass)

    # 自定义处理邮件收发地址的显示内容
    def _format_addr(s):
        name, addr = parseaddr(s)
        # 将邮件的name转换成utf-8格式，addr如果是unicode，则转换utf-8输出，否则直接输出addr
        return formataddr((Header(name, 'utf-8').encode(), addr))

    msg = MIMEText(msg, 'html', 'utf-8')
    # 邮件对象
    msg['From'] = _format_addr('<%s>' % from_addr)
    msg['to'] = _format_addr('<%s>' % to_addr)
    msg['Subject'] = Header(title, 'utf-8').encode()
    msg['date'] = time.strftime("%a,%d %b %Y %H:%M:%S %z")
    # 发送邮件
    server = smtplib.SMTP(smtp_server, 465)
    server.set_debuglevel(1)
    server.login(from_addr, password)
    server.sendmail(from_addr, to_addr, msg.as_string())
    server.quit()
    return True

@csrf_exempt
def order_list(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('search_words','').replace('amp;','')
    is_email = request.GET.get('search_is_email','')
    is_presale = request.GET.get('search_is_presale','')
    payments_date = request.GET.get('search_payments_date','')
    nosend_re  = NoSendRes.objects.values_list('sku').all()

    if (is_presale and is_presale=='1'):
        list = OrderItems.objects.filter(is_email=0, sku__in=nosend_re)
        is_email = 0
    elif (is_email and is_email == '1'):
        list = OldOrderItems.objects.filter(is_email=1)
        is_presale = 0
    else:
        list = OrderItems.objects.filter(is_email=0).exclude(sku__in=nosend_re)
        if is_presale:
            list = list.filter(is_presale=is_presale)
    if keywords:
        list = list.filter(Q(order_id__contains=keywords)| Q(sku__contains=keywords)| Q(customer__contains=keywords))
    if payments_date:
        list = list.filter(payments_date__contains=payments_date)

    data = {
        'list': list,
        'user': user,
        'keywords': keywords,
        'is_email': is_email,
        'is_presale': is_presale,
        'payments_date': payments_date,
        'title': 'Order Items',
    }
    return render(request, "Stocks/send_email/order_list.html", data)

@csrf_exempt
def order_save(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        sku = request.POST.get('sku','').replace('amp;','')
        if not id:
            obj = NoSendRes()
            obj.id
            obj.sku = sku
            obj.save()
            if obj.id:
                return HttpResponse(json.dumps({'code': 1, 'msg': 'Work is Done!'}), content_type='application/json')

@csrf_exempt
def order_import(request):
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
        res = read_excel_for_orders(file_path)
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def send_email(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        data = request.POST.get('data')
        m_time = 0
        list_data = eval(data)
        for i,val in enumerate(list_data):
            orders = OrderItems.objects.filter(order_id=val['order_id'], is_email=0)
            tmps = EmailTemplates.objects.filter(sku=val['sku'])
            if orders and tmps:
                title = tmps[0].title
                if title:
                    title = title % val['order_id']
                else:
                    title = "After-sale Service for your recent order from Brandline (Amazon order: %s)" % val['order_id']
                msg = tmps[0].content % val['buyer']
                if not i == 0 and list_data[i - 1]['sku'] == list_data[i]['sku']:
                    m_time += 5
                if not i == 0 and not list_data[i - 1]['sku'] == list_data[i]['sku']:
                    m_time = 0
                time_re = _get_send_time(tmps[0].send_time)
                time_re = int(time_re) + m_time
                tmp_res = [title, msg, user, 'swlxyztd@163.com']
                t = threading.Timer(float('%.1f' % 1), send_email_as_tmp, tmp_res)
                t.start()
                email_order_obj = OldOrderItems()
                email_order_obj.id
                email_order_obj.order_id = val['order_id']
                email_order_obj.email = val['email']
                email_order_obj.sku = val['sku']
                email_order_obj.payments_date = orders[0].payments_date
                email_order_obj.is_presale = orders[0].is_presale
                email_order_obj.is_email = 1
                email_order_obj.order_status = orders[0].order_status
                email_order_obj.customer = orders[0].customer
                email_order_obj.save()
                if email_order_obj.id:
                    orders.delete()
        return HttpResponse(json.dumps({'code': 1, 'msg': 'Work is Done!'}), content_type='application/json')

@csrf_exempt
def no_send_list(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")

    keywords = request.GET.get('search_words', '').replace('amp;', '')
    list = NoSendRes.objects.all()
    if keywords:
        list = list.filter(sku__contains=keywords)

    data = {
        'list': list,
        'user': user,
        'keywords': keywords,
        'title': 'Order List',
    }
    return render(request, "Stocks/send_email/no_send_list.html", data)

@csrf_exempt
def check_order_import(request):
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
        res = read_excel_file1(NoSendRes, file_path, 'no_send_res')
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def del_check_order(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        id = request.POST.get('id','')
        obj = NoSendRes.objects.filter(id=id)
        if not obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': 'Data is not exits!'}), content_type='application/json')
        obj.delete()
        return HttpResponse(json.dumps({'code': 1, 'msg': 'Work is Done!'}), content_type='application/json')