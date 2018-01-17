# -*- coding: utf-8 -*-

from django.db.models import Count
from django.contrib.auth.models import User
from maxlead_site.models import UserAsins

def get_asins(user, ownership='', status='', revstatus='', liststatus='', type=0, user_id=''):
    asins = []
    if type:
        user_asins = UserAsins.objects.values('aid').annotate(count=Count('aid'))
    else:
        user_asins = UserAsins.objects.values('aid').annotate(count=Count('aid')).filter(review_watcher=1, is_use=1)
    if ownership:
        user_asins = user_asins.filter(ownership=ownership)

    if user.role == 0:
        user_asins = user_asins.filter(user=user.user)
    elif user.role == 1:
        user_list = User.objects.filter(group=user.user)
        user_asins = user_asins.filter(user=user_list)
    if user_id:
        user_asins = user_asins.filter(user_id=user_id)

    if user_asins:
        if status:
            user_asins = user_asins.filter(is_use=status)
        if revstatus:
            user_asins = user_asins.filter(review_watcher=revstatus)
        if liststatus:
            user_asins = user_asins.filter(listing_watcher=liststatus)
        for val in user_asins:
            asins.append(val['aid'])

        return asins
    else:
        return False