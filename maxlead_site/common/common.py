# -*- coding: utf-8 -*-

from django.db.models import Count
from maxlead_site.models import UserAsins,UserProfile
from maxlead_site.common.npextractor import NPExtractor

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
            user_asins = user_asins.filter(is_use=status)
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