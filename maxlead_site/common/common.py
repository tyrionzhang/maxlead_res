# -*- coding: utf-8 -*-

import os
from datetime import *
from django.db.models import Count
from maxlead_site.models import UserAsins,UserProfile
from max_stock.models import UserEmailMsg
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

def spiders_send_email(f_obj, file_path=None):
    msg_list = UserEmailMsg.objects.filter(is_send=0)
    if msg_list:
        msg_str = ''
        subject = 'Maxlead库存预警'
        from_email = settings.EMAIL_HOST_USER
        msg_dict = {}
        for val in msg_list:
            msg_obj = UserEmailMsg.objects.filter(id=val.id)
            if val.user.email:
                msg_dict.update({val.user.email:''})
                msg_dict[val.user.email] += val.content
                msg_str += val.content
                msg_obj.update(is_send=1)
            else:
                msg_obj.delete()
        for key in msg_dict:
            send_mail(subject, msg_dict[key], from_email, [key], fail_silently=False)
        if msg_str:
            send_mail(subject, msg_str, from_email, ['shipping.gmi@gmail.com'], fail_silently=False)
    f_obj.close()
    os.remove(file_path)

def kill_pid_for_name(name):
    lines = os.popen('ps -ef | grep %s' % name)
    for path in lines:
        try:
            client = path.split(' ')
            if "idle" in client:
                progress = path.split(' ')[2]
                if not progress:
                    progress = path.split(' ')[1]
                os.popen('kill %s' % progress)
        except:
            continue