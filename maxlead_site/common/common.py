# -*- coding: utf-8 -*-

import os
import threading
from datetime import *
from django.db.models import Count
from django.db import connection
from django.db.utils import OperationalError
from maxlead_site.models import UserAsins,UserProfile
from max_stock.models import UserEmailMsg,SkuUsers,Thresholds,WarehouseStocks
from maxlead_site.common.npextractor import NPExtractor
from maxlead import settings
from django.core.mail import send_mail

def get_asins(user, ownership='', status='', revstatus='', liststatus='', type=0, user_id='',is_listings=False,is_done=0):
    asins = []
    if type:
        user_asins = UserAsins.objects.values('aid').annotate(count=Count('aid'))
    else:
        user_asins = UserAsins.objects.values('aid').annotate(count=Count('aid')).filter(review_watcher=1, is_use=1)
    if ownership:
        user_asins = user_asins.filter(ownership=ownership)

    if is_done:
        user_asins = user_asins.filter(is_done=0)

    if user.role == 0:
        user_asins = user_asins.filter(user=user.user)
    elif user.role == 1:
        user_file = UserProfile.objects.filter(group=user)
        uids = []
        for val in user_file:
            uids.append(val.user_id)
        user_asins = user_asins.filter(user_id__in=uids)
    if user_id:
        user_asins = user_asins.filter(user_id=user_id)

    if user_asins:
        if status:
            user_asins = user_asins.filter(is_use=True)
        if revstatus:
            user_asins = user_asins.filter(review_watcher=revstatus)
        if liststatus:
            user_asins = user_asins.filter(listing_watcher=liststatus)
        if is_listings:
            return user_asins

        for val in user_asins:
            asins.append(val['aid'])

        return asins
    else:
        return False

def get_review_keywords(reviews):
    positive_keywords = []
    negative_keywords = []
    if reviews:
        posi_text = ''
        nega_text = ''
        for val in reviews:
            if val.score >= 3:
                if val.content:
                    posi_text += val.content + '\n'
            if val.score < 3:
                if val.content:
                    nega_text += val.content + '\n'

        posi_obj = NPExtractor(posi_text)
        nega_obj = NPExtractor(nega_text)
        posi_line = posi_obj.extract()
        nega_line = nega_obj.extract()
        if posi_obj:
            for val in set(posi_line):
                i = posi_text.count(val)
                if i >= 2:
                    positive_keywords.append({'words': val,'count':i})
        if nega_line:
            for val in set(nega_line):
                n = nega_text.count(val)
                if n >= 2:
                    negative_keywords.append({'words': val, 'count': n})
        if negative_keywords:
            for v in range(len(negative_keywords)):
                for i in  range(len(negative_keywords)-1-v):
                    if (i+1) < len(negative_keywords) and negative_keywords[i+1]['count'] > negative_keywords[i]['count']:
                        temp = negative_keywords[i+1]
                        negative_keywords[i + 1] = negative_keywords[i]
                        negative_keywords[i] = temp
        if positive_keywords:
            for v in range(len(positive_keywords)):
                for i in range(len(positive_keywords)-1-v):
                    if (i+1) < len(positive_keywords) and positive_keywords[i+1]['count'] > positive_keywords[i]['count']:
                        temp = positive_keywords[i+1]
                        positive_keywords[i + 1] = positive_keywords[i]
                        positive_keywords[i] = temp
    return {'negative_keywords':negative_keywords, 'positive_keywords':positive_keywords}

def encrypt(key, s):
    b = bytearray(str(s).encode("utf-8"))
    n = len(b) # 求出 b 的字节数
    c = bytearray(n*2)
    j = 0
    for i in range(0, n):
        b1 = b[i]
        b2 = b1 ^ key # b1 = b2^ key
        c1 = b2 % 16
        c2 = b2 // 16 # b2 = c2*16 + c1
        c1 = c1 + 65
        c2 = c2 + 65 # c1,c2都是0~15之间的数,加上65就变成了A-P 的字符的编码
        c[j] = c1
        c[j+1] = c2
        j = j+2
    return c.decode("utf-8")
def decrypt(key, s):
    c = bytearray(str(s).encode("utf-8"))
    n = len(c) # 计算 b 的字节数
    if n % 2 != 0 :
        return ""
    n = n // 2
    b = bytearray(n)
    j = 0
    for i in range(0, n):
        c1 = c[j]
        c2 = c[j+1]
        j = j+2
        c1 = c1 - 65
        c2 = c2 - 65
        b2 = c2*16 + c1
        b1 = b2^ key
        b[i]= b1
    try:
        return b.decode("utf-8")
    except:
        return "failed"

def get_send_time(time_str):
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

def spiders_send_email():
    msg_list = UserEmailMsg.objects.filter(is_send=0)
    if msg_list:
        msg_str = ''
        subject = 'Maxlead库存预警'
        from_email = settings.EMAIL_HOST_USER
        msg_dict = {}
        for val in msg_list:
            msg_dict.update({val.user.email:''})
            msg_dict[val.user.email] += val.content
            msg_str += val.content
        for key in msg_dict:
            send_mail(subject, msg_dict[key], from_email, [key], fail_silently=False)
        if msg_str:
            send_mail(subject, msg_str, from_email, ['shipping.gmi@gmail.com'], fail_silently=False)
        msg_list.update(is_send=1)

def kill_pid_for_name(name, type=0, select_type=False):
    lines = os.popen('ps -ef | grep %s' % name)
    for path in lines:
        try:
            client = path.split(' ')
            if type == 1:
                client = ['idle']
            if select_type in client:
                progress = path.split(' ')[1]
                if progress:
                    os.popen('kill %s' % progress)

            if "idle" in client:
                progress = path.split(' ')[2]
                if not progress:
                    progress = path.split(' ')[1]
                if progress:
                    os.popen('kill %s' % progress)
        except:
            continue

def to_int(str):
    try:
        int(str)
        return int(str)
    except ValueError: #报类型错误，说明不是整型的
        try:
            float(str) #用这个来验证，是不是浮点字符串
            return int(float(str))
        except ValueError:  #如果报错，说明即不是浮点，也不是int字符串。   是一个真正的字符串
            return False

def warehouse_threshold_msgs(qtys,warehouse=None):
    users = SkuUsers.objects.all().annotate(s=Count("sku"), u=Count("user"))
    thresholds = Thresholds.objects.filter(warehouse__in=warehouse)
    msg_str2 = ''
    c_time = datetime.now().strftime("%Y-%m-%d")
    for val in thresholds:
        t_key = val.warehouse + val.sku
        if t_key in qtys and val.threshold >= int(qtys[t_key]) and users:
            for usr in users:
                if usr.sku == val.sku and usr.user.email:
                    m_str = 'SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s' % (
                        val.sku, val.warehouse, qtys[t_key], val.threshold)
                    check = UserEmailMsg.objects.filter(user=usr.user, sku=val.sku, warehouse=val.warehouse, content=m_str, created__contains=c_time)
                    if not check:
                        obj = UserEmailMsg()
                        obj.id
                        obj.user = usr.user
                        obj.sku = val.sku
                        obj.warehouse = val.warehouse
                        obj.content = m_str
                        obj.save()
                    msg_str2 += '%s=>SKU:%s,Warehouse:%s,QTY:%s,Early warning value:%s \n|' % (
                        usr.user.email, val.sku, val.warehouse, qtys[t_key], val.threshold)
    return msg_str2

def warehouse_date_data(warehouse):
    date_now = datetime.now()
    date0 = date_now.strftime('%Y-%m-%d')
    obj = WarehouseStocks.objects.filter(warehouse__in=warehouse, created__contains=date0)
    try:
        if obj:
            obj.delete()
    except OperationalError:
        connection.close()
        connection.cursor()
        obj = WarehouseStocks.objects.filter(warehouse__in=warehouse, created__contains=date0)
        if obj:
            obj.delete()

    date1 = date_now - timedelta(days=1)
    old_list_qty = {}
    old_list = WarehouseStocks.objects.filter(warehouse__in=warehouse, created__contains=date1.strftime('%Y-%m-%d'))
    for val in old_list:
        o_key = val.warehouse + val.sku
        old_list_qty.update({
            o_key: val.qty
        })
    return old_list_qty

def restart_postgres():
    t = threading.Timer(300.0, restart_postgres)
    try:
        curs = connection.cursor()
        curs.close()
    except OperationalError:
        lines = os.popen('ps -ef | grep %s' % 'postgres')
        for path in lines:
            try:
                client = path.split(' ')
                progress = path.split(' ')[1]
                if progress:
                    os.popen('kill %s' % progress)

                if "idle" in client:
                    progress = path.split(' ')[2]
                    if not progress:
                        progress = path.split(' ')[1]
                    if progress:
                        os.popen('kill %s' % progress)
            except:
                continue
        os.system('service postgresql-9.3 start')
        print(u'启动数据库~')
    t.start()