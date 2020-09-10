# -*- coding: utf-8 -*-
import os,json,time
import datetime
import requests,threading
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from maxlead_site.views.app import App
from django.views.decorators.csrf import csrf_exempt
from max_stock.models import TrackingOrders,StockLogs
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from maxlead import settings
from maxlead_site.common.excel_world import read_excel_for_tracking_orders,get_excel_file1,get_excel_file

@csrf_exempt
def index(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")

    keywords = request.GET.get('keywords', '').replace('amp;', '')
    billing_date = request.GET.get('billing_date', '')
    end_date = request.GET.get('end_date', '')
    if not billing_date:
        billing_date = (datetime.datetime.now() + datetime.timedelta(days=-5)).strftime("%Y-%m-%d")

    if user.user.is_superuser or user.stocks_role == '66':
        lists = TrackingOrders.objects.get().order_by('-billing_date')
    else:
        lists = TrackingOrders.objects.filter(user_id=user.user_id)
    # if keywords:
    #     lists = lists.filter(Q(order_num__contains=keywords)|Q(tracking_num__contains=keywords))
    # if billing_date:
    #     lists = lists.filter(billing_date__gt=billing_date)
    # if end_date:
    #     lists = lists.filter(billing_date__lte=end_date)
    data = []
    if lists:
        for val in lists:
            first_scan_time = ''
            delivery_time = ''
            if val.first_scan_time:
                first_scan_time = val.first_scan_time.strftime("%Y-%m-%d %H:%M:%S")
            if val.delivery_time:
                delivery_time = val.delivery_time.strftime("%Y-%m-%d %H:%M:%S")
            data.append({
                'order_num': val.order_num,
                'tracking_num': val.tracking_num,
                'warehouse': val.warehouse,
                'account_num': val.account_num,
                'description': val.description,
                'status': val.status,
                'shipment_late': val.shipment_late,
                'delivery_late': val.delivery_late,
                'billing_date': val.billing_date.strftime('%b.%d'),
                'latest_ship_date': val.latest_ship_date,
                'latest_delivery_date': val.latest_delivery_date,
                'first_scan_time': first_scan_time,
                'delivery_time': delivery_time
            })

    data = {
        'user': user,
        'data': data,
        'billing_date': billing_date,
        'end_date': end_date,
        'keywords': keywords,
        'title': 'TrackingOrders',
    }
    return render(request, "Stocks/trackingOrders/index.html", data)

@csrf_exempt
def import_tracking(request):
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
        res = read_excel_for_tracking_orders(file_path, user=user.user_id)
        os.remove(file_path)
        return HttpResponse(json.dumps(res), content_type='application/json')

def get_tracking_order_status():
    # billing_date = datetime.datetime.now().strftime("%b.%y")
    # lists = TrackingOrders.objects.filter(billing_date__contains=billing_date)
    t = threading.Timer(86400.0, get_tracking_order_status)
    datetime_now = datetime.datetime.now()
    re_date = datetime_now + datetime.timedelta(days=-30)
    lists = TrackingOrders.objects.filter(created__gt=re_date).exclude(Q(status='Delivered')| Q(tracking_num=''))
    if lists:
        data = []
        for val in lists:
            try:
                headers = {
                    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
                }
                url = 'http://shipit-api.herokuapp.com/api/carriers/%s/%s'
                if len(val.tracking_num) > 12:
                    carrier = 'ups'
                else:
                    carrier = 'fedex'
                url = url % (carrier, val.tracking_num)
                res = requests.get(url, headers=headers)
                res = json.loads(res.content.decode())
                eta = False
                if 'eta' in res:
                    eta = datetime.datetime.strptime(res['eta'][0:19], '%Y-%m-%dT%H:%M:%S')
                if 'activities' in res:
                    activities = res['activities']
                    if activities:
                        status = activities[0]['details']
                        first_scan_time = ''
                        delivery_time = ''
                        shipment_late = ''
                        delivery_late = ''
                        arrived_date_list = []
                        for v in activities:
                            if v['details'] == 'Arrived at FedEx location':
                                arrived_date_list.append(datetime.datetime.strptime(v['datetime'][0:10], '%Y-%m-%d'))
                            if v['details'] == 'Picked up' and carrier == 'fedex':
                                first_scan_time = datetime.datetime.strptime(v['datetime'], '%Y-%m-%dT%H:%M:%S')
                                first_scan_time = first_scan_time + datetime.timedelta(hours=-7)
                            if v['details'] == 'Delivered':
                                if carrier == 'ups':
                                    delivery_time = datetime.datetime.strptime(v['timestamp'][0:19], '%Y-%m-%dT%H:%M:%S')
                                elif carrier == 'fedex':
                                    delivery_time = datetime.datetime.strptime(v['datetime'], '%Y-%m-%dT%H:%M:%S')
                                delivery_time = delivery_time + datetime.timedelta(hours=-7)
                            if v['details'] == 'Origin scan' and carrier == 'ups':
                                first_scan_time = datetime.datetime.strptime(v['timestamp'][0:19], '%Y-%m-%dT%H:%M:%S')
                                first_scan_time = first_scan_time + datetime.timedelta(hours=-7)
                            if first_scan_time:
                                if val.latest_ship_date and len(val.latest_ship_date) >= 20:
                                    first_scan_time_str = int(time.mktime(first_scan_time.timetuple()))
                                    latest_ship_date_str = int(
                                        time.mktime(time.strptime(val.latest_ship_date[0:19], "%Y-%m-%dT%H:%M:%S")))
                                    shipment_late_c = first_scan_time_str - latest_ship_date_str
                                    if shipment_late_c > 0:
                                        shipment_late = 'Y'
                            if delivery_time:
                                if val.latest_delivery_date and len(val.latest_delivery_date) >= 20:
                                    delivery_time_str = int(time.mktime(delivery_time.timetuple()))
                                    latest_delivery_date_str = int(
                                        time.mktime(time.strptime(val.latest_delivery_date[0:19], "%Y-%m-%dT%H:%M:%S")))
                                    delivery_late_c = delivery_time_str - latest_delivery_date_str
                                    if delivery_late_c > 0:
                                        delivery_late = 'Y'
                        val.status = status
                        if first_scan_time:
                            val.first_scan_time = first_scan_time
                        if delivery_time:
                            val.delivery_time = delivery_time
                        if shipment_late:
                            val.shipment_late = shipment_late
                        if delivery_late:
                            val.delivery_late = delivery_late
                        val.save()
                        update_check = 0
                        update_status = '正常'
                        delivered_status = '正常'
                        if arrived_date_list:
                            arrived_date_list.sort()
                            arrived_date = arrived_date_list[0]
                            billing_date = str(val.billing_date)
                            billing_date = datetime.datetime.strptime(billing_date, '%Y-%m-%d')
                            billing_weekday = billing_date.weekday()
                            update_check = (arrived_date - billing_date).days
                            if billing_weekday == 4 and update_check > 4:
                                update_status = '异常'
                            if billing_weekday != 4 and update_check > 2:
                                update_status = '异常'
                        check_delivered = eta and eta < datetime_now and val.status != 'Delivered'
                        if check_delivered:
                            delivered_status = '异常'
                        if (val.status == 'Order Processed: Ready for UPS' or val.status == 'Order processed: ready for ups'
                                or val.status == 'Shipment information sent to FedEx') or update_check > 2 or check_delivered:
                            data.append({
                                'order_num': val.order_num,
                                'tracking_num': val.tracking_num,
                                'warehouse': val.warehouse,
                                'account_num': val.account_num,
                                'description': val.description,
                                'status': val.status,
                                'update_status': update_status,
                                'delivered_status': delivered_status,
                                'shipment_late': val.shipment_late,
                                'delivery_late': val.delivery_late,
                                'billing_date': val.billing_date.strftime('%b.%d'),
                                'latest_ship_date': val.latest_ship_date,
                                'latest_delivery_date': val.latest_delivery_date,
                                'first_scan_time': val.first_scan_time,
                                'delivery_time': val.delivery_time
                            })
            except:
                log_obj = StockLogs()
                log_obj.id
                log_obj.user_id = 1
                log_obj.fun = 'tracking 自动更新状态'
                log_obj.description = 'Tracking number %s' % (val.tracking_num)
                log_obj.save()
                continue
        if data:
            fields = [
                '发货单时间',
                '账号',
                'OrderNumber',
                'WarehouseName',
                'Description',
                'Tracking Numbers',
                'latest-ship-date',
                'latest-delivery-date',
                'Status',
                '动态更新',
                '预计送达',
                'First Scan time',
                'Delivery time',
                'Shipment Late',
                'Delivery Late'
            ]
            data_fields = [
                'billing_date',
                'account_num',
                'order_num',
                'warehouse',
                'description',
                'tracking_num',
                'latest_ship_date',
                'latest_delivery_date',
                'status',
                'update_status',
                'delivered_status',
                'first_scan_time',
                'delivery_time',
                'shipment_late',
                'delivery_late'
            ]
            try:
                file_path = get_excel_file1(1, data, fields, data_fields)
                file_path = os.path.join(settings.BASE_DIR, file_path)
                subject = '报告邮件'
                text_content = '未扫描状态和异常的订单汇总。'
                html_content = '<p>这是一封<strong>未扫描状态和异常的订单汇总</strong>。</p>'
                from_email = settings.DEFAULT_FROM_EMAIL
                msg = EmailMultiAlternatives(subject, text_content, from_email, ['rudy.zhangwei@gmainland.com', 'nicole.yan@gmainland.com'])
                msg.attach_alternative(html_content, "text/html")
                # 发送附件
                # text = open(file_path, 'rb').read()
                file_name = os.path.basename(file_path)
                # 对文件进行编码处理
                # b = make_header([(file_name, 'utf-8')]).encode('utf-8')
                # msg.attach(b, text)
                msg.attach_file(file_path)
                msg.send()
                os.remove(file_path)
            except Exception as e:
                log_obj = StockLogs()
                log_obj.id
                log_obj.user_id = 1
                log_obj.fun = 'tracking 邮件发送Error'
                log_obj.description = e
                log_obj.save()
    t.start()
    pass

@csrf_exempt
def tracking_orders_export(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    keywords = request.GET.get('keywords', '').replace('amp;', '')
    billing_date = request.GET.get('billing_date', '')
    if not billing_date:
        billing_date = (datetime.datetime.now() + datetime.timedelta(days=-5)).strftime("%Y-%m-%d")
    if user.user.is_superuser or user.stocks_role == '66':
        lists = TrackingOrders.objects.all()
    else:
        lists = TrackingOrders.objects.filter(user_id=user.user_id)
    if keywords:
        lists = lists.filter(Q(order_num__contains=keywords) | Q(tracking_num__contains=keywords))
    if billing_date:
        lists = lists.filter(billing_date__gt=billing_date)

    data = []
    if lists:
        for val in lists:
            first_scan_time = ''
            delivery_time = ''
            if val.first_scan_time:
                first_scan_time = val.first_scan_time.strftime("%Y-%m-%d %H:%M:%S")
            if val.delivery_time:
                delivery_time = val.delivery_time.strftime("%Y-%m-%d %H:%M:%S")
            data.append({
                'order_num': val.order_num,
                'tracking_num': val.tracking_num,
                'warehouse': val.warehouse,
                'account_num': val.account_num,
                'description': val.description,
                'status': val.status,
                'shipment_late': val.shipment_late,
                'delivery_late': val.delivery_late,
                'billing_date': val.billing_date.strftime('%b.%d'),
                'latest_ship_date': val.latest_ship_date,
                'latest_delivery_date': val.latest_delivery_date,
                'first_scan_time': first_scan_time,
                'delivery_time': delivery_time
            })

        fields = [
            '发货单时间',
            '账号',
            'OrderNumber',
            'WarehouseName',
            'Description',
            'Tracking Numbers',
            'latest-ship-date',
            'latest-delivery-date',
            'Status',
            'First Scan time',
            'Delivery time',
            'Shipment Late',
            'Delivery Late'
        ]
        data_fields = [
            'billing_date',
            'account_num',
            'order_num',
            'warehouse',
            'description',
            'tracking_num',
            'latest_ship_date',
            'latest_delivery_date',
            'status',
            'first_scan_time',
            'delivery_time',
            'shipment_late',
            'delivery_late'
        ]
        return get_excel_file(request, data, fields, data_fields)
    else:
        return HttpResponse('没有数据~~')