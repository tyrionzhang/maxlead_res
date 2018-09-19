# -*- coding: utf-8 -*-
import os,json,threading,smtplib,random
import sys, string
import poplib
from datetime import *
import time
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import OrderItems,OldOrderItems,EmailTemplates,NoSendRes,EmailContacts,StockLogs
from maxlead_site.views.app import App
from django.db.models import Q
from maxlead import settings
from maxlead_site.common.excel_world import read_excel_for_orders,read_excel_file1,read_csv_file
from django.core.mail import send_mail
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import parseaddr,formataddr
from maxlead_site.common import common

def _get_send_time(time_str, m_time=None):
    time_now = datetime.now()
    time_saturday = time_now.strftime('%Y-%m-%d ') + time_str
    time_saturday = datetime.strptime(time_saturday, '%Y-%m-%d %H:%M')
    t_re = (time_saturday - time_now).total_seconds()
    if t_re < 0:
        time_re = datetime.now() + timedelta(days=1)
        time_saturday = time_re.strftime('%Y-%m-%d ') + time_str
        time_saturday = datetime.strptime(time_saturday, '%Y-%m-%d %H:%M')
        t_re = (time_saturday - time_now).total_seconds()
    if m_time:
        t_re = int(t_re) + m_time
    return t_re

def send_email_as_tmp(title, msg, from_email, email, order_id, sku, buyer, payments_date, is_presale, order_status, user_id, request_path):
    smtp_server = 'smtp.gmail.com'
    from_addr = 'maxlead.us@gmail.com'
    to_addr = email
    password = "nxtpinfcqitdcpzb"
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
    try:
        # 发送邮件
        server = smtplib.SMTP(smtp_server, 587)
        server.set_debuglevel(1)
        server.starttls()
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())
        server.quit()
    except Exception as e:
        print(e)
        email_order_obj = OrderItems()
        email_order_obj.id
        email_order_obj.user_id = user_id
        email_order_obj.order_id = order_id
        email_order_obj.sku = sku
        email_order_obj.payments_date = payments_date
        email_order_obj.is_presale = is_presale
        email_order_obj.customer = buyer
        email_order_obj.email = to_addr
        email_order_obj.is_email = 0
        email_order_obj.send_date = datetime.now()
        email_order_obj.order_status = order_status
        email_order_obj.save()
        log_obj = StockLogs()
        log_obj.id
        log_obj.user_id = user_id
        log_obj.fun = request_path
        log_obj.description = 'Order_id:%s,Error:%s' % (order_id, e)
        log_obj.save()

        if email_order_obj.id:
            old_obj = OldOrderItems.objects.filter(order_id=order_id)
            if old_obj:
                old_obj.delete()
    return True

@csrf_exempt
def order_list(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('search_words','').replace('amp;','')
    is_email = request.GET.get('search_is_email','')
    is_presale = request.GET.get('search_is_presale','')
    start_date = request.GET.get('search_start_date','')
    end_date = request.GET.get('search_end_date','')
    payments_date = request.GET.get('search_payments_date','')
    nosend_re  = NoSendRes.objects.values_list('sku').filter(order_id='', status='')

    if (is_presale and is_presale=='1'):
        list = OrderItems.objects.filter(is_email=0, sku__in=nosend_re)
        is_email = 0
    elif (is_email and is_email == '1'):
        if not start_date:
            start_date = (datetime.now() + timedelta(days=-5)).strftime("%Y-%m-%d")
        list = OldOrderItems.objects.filter(is_email=1, created__gte=start_date)
        is_presale = 0
    else:
        nosend_re1 = NoSendRes.objects.values_list('order_id').filter(status='Refund').exclude(order_id='')
        contacts = EmailContacts.objects.values_list('email_address').filter(expired_time__gt=datetime.now())
        list = OrderItems.objects.filter(is_email=0)
        if nosend_re:
            list = list.exclude(sku__in=nosend_re)
        if nosend_re1:
            list = list.exclude(order_id__in=nosend_re1)
        if contacts:
            check_contacts = []
            for val in contacts:
                check_contacts.append(val[0].strip())
            list = list.exclude(email__in=check_contacts)
        if is_presale:
            list = list.filter(is_presale=is_presale)
    if not user.user.is_superuser:
        list = list.filter(user_id=user.user.id)
    if keywords:
        list = list.filter(Q(order_id__contains=keywords)| Q(sku__contains=keywords)| Q(customer__contains=keywords)| Q(email__contains=keywords))
    if start_date:
        list = list.filter(created__gte=start_date)
    if end_date:
        list = list.filter(created__lte=end_date)
    if payments_date:
        list = list.filter(payments_date__contains=payments_date)

    data = {
        'list': list,
        'user': user,
        'keywords': keywords,
        'is_email': is_email,
        'is_presale': is_presale,
        'payments_date': payments_date,
        'start_date': start_date,
        'end_date': end_date,
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
        order_id = request.POST.get('order_id','')
        status = request.POST.get('status','')
        sku = request.POST.get('sku','').replace('amp;','')
        if not sku:
            return HttpResponse(json.dumps({'code': 1, 'msg': 'Sku is empty!'}), content_type='application/json')
        if not id:
            obj = NoSendRes()
            obj.id
            obj.user_id = user.user_id
            obj.sku = sku
            obj.order_id = order_id
            obj.status = status
            obj.save()
            if obj.id:
                return HttpResponse(json.dumps({'code': 1, 'msg': 'Work is Done!'}), content_type='application/json')

@csrf_exempt
def orders_del(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        data = request.POST.get('data','')
        is_email = request.POST.get('is_email','')
        if is_email == '1':
            obj = OldOrderItems.objects.filter(order_id__in=eval(data))
        else:
            obj = OrderItems.objects.filter(order_id__in=eval(data))

        if obj:
            re = obj.delete()
            if not re:
                return HttpResponse(json.dumps({'code': 0, 'msg': 'Work is Faild!'}), content_type='application/json')
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
        res = read_excel_for_orders(file_path,user=user.user_id)
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
            old_orders = OldOrderItems.objects.filter(order_id=val['order_id'])
            tmps = EmailTemplates.objects.filter(sku=val['sku'])
            if orders and tmps and not old_orders:
                title = tmps[0].title
                if title and not title.find('%s') == -1:
                    title = title % val['order_id']
                else:
                    title = "After-sale Service for your recent order from Brandline (Amazon order: %s)" % val['order_id']
                if tmps[0].content and tmps[0].content.find('%s') == -1:
                    msg = tmps[0].content
                else:
                    msg = tmps[0].content % val['buyer']
                m_time += (3 + random.randint(7, 20))
                time_re = _get_send_time(tmps[0].send_time, m_time=m_time)
                tmp_res = [title, msg, user, val['email'], val['order_id'], val['sku'], val['buyer'], orders[0].payments_date,
                           orders[0].is_presale, orders[0].order_status, user.user_id, request.path]
                t = threading.Timer(float('%.1f' % time_re), send_email_as_tmp, tmp_res)
                t.start()
                email_order_obj = OldOrderItems()
                email_order_obj.id
                email_order_obj.user_id = user.user_id
                email_order_obj.order_id = val['order_id']
                email_order_obj.sku = val['sku']
                email_order_obj.payments_date = orders[0].payments_date
                email_order_obj.is_presale = orders[0].is_presale
                email_order_obj.is_email = 1
                email_order_obj.send_date = datetime.now()
                email_order_obj.order_status = orders[0].order_status
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
    if not user.user.is_superuser:
        list = list.filter(user_id=user.user.id)
    if keywords:
        list = list.filter(Q(sku__contains=keywords)|Q(order_id__contains=keywords)|Q(status__contains=keywords))

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
        res = read_excel_file1(NoSendRes, file_path, 'no_send_res', user=user.user_id)
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

@csrf_exempt
def contact_list(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('search_words','').replace('amp;','')
    list = EmailContacts.objects.filter(expired_time__gt=datetime.now())
    if keywords:
        list = list.filter(Q(email_address__contains=keywords)|Q(email__contains=keywords))
    data = {
        'list': list,
        'user': user,
        'keywords': keywords,
        'title': 'Email Contacts',
    }
    return render(request, "Stocks/send_email/contact_list.html", data)

@csrf_exempt
def update_emails(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        myfile = request.FILES.get('myfile', '')
        email = request.POST.get('email', '')
        expired_time = request.POST.get('expired_time', '')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}), content_type='application/json')
        if not expired_time:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'Expired is empty!'}), content_type='application/json')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        expired_time = datetime.now() + timedelta(days = int(expired_time))
        res = read_csv_file(EmailContacts, file_path, email=email, expired_time=expired_time)
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def batch_del_ocheck(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')
    if request.method == 'POST':
        ids = eval(request.POST.get('data',''))
        if not ids:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'请选择要删除的模板！'}), content_type='application/json')
        obj = NoSendRes.objects.filter(id__in=ids)
        if not obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'请求的数据不存在！'}), content_type='application/json')
        obj.delete()
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully！'}), content_type='application/json')
