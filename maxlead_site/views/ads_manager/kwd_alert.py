# -*- coding: utf-8 -*-
import json
import datetime,csv,codecs
from dateutil.relativedelta import relativedelta
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.db.models import Sum, Count
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from maxlead_site.views.app import App
from maxlead_site.models import AdsBrand,AdsCampaign,SearchTeam
from maxlead_site.models import UserProfile
from django.views.decorators.csrf import csrf_exempt
from maxlead_site.views.ads_manager.brand import account_li
from maxlead_site.views.ads_manager.brand_sku import _get_spend
from maxlead_site.views.ads_manager.details import _get_month_re

def kwd_alert(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")
    viewRange = request.GET.get('viewRange', user.user.id)
    account = request.GET.get('account', '1')
    range_type = request.GET.get('range_type', 'Weekly')
    sum_by_date = request.GET.get('sum_by_date', '')
    search_key = request.GET.get('search_key', 'all')
    listKwd = request.GET.get('listKwd', '')
    week = request.GET.get('week', '')
    end_week = request.GET.get('end_week', '')
    month = request.GET.get('month', '')
    end_month = request.GET.get('end_month', '')
    conventers = request.GET.get('conventers', 'All')
    threshold = request.GET.get('threshold', 0)
    threshold = float(threshold)
    order_type = request.GET.get('order_type', '')
    order_dasc = request.GET.get('order_dasc', '')

    month_str = None
    end_month_str = None
    week_str = None
    end_week_str = None
    start_month = None
    end_month_month = None
    start_week = None
    end_week_week = None
    last_year = None
    start_last_year = None
    start_last_month = None
    last_month = None
    start_last_week = None
    end_last_week = None
    if sum_by_date == 'on':
        if range_type == 'Monthly':
            month_re = month.split('-')
            year_str = month_re[0]
            month_str = month_re[1]
            end_month_re = end_month.split('-')
            end_year_str = end_month_re[0]
            end_month_str = end_month_re[1]
            start_month = "%s%s" % (year_str, month_str)
            end_month_month = "%s%s" % (end_year_str, end_month_str)

            last_month_re = _get_month_re(start_month, end_month_month)
            if month_str == 1:
                last_year = int(year_str) - 1
                last_month = 12
            else:
                last_year = year_str
                last_month = int(month_str) - 1
            start_last_re = last_month - last_month_re
            if last_month_re == 0:
                start_last_year = last_year
                start_last_month = last_month
            elif start_last_re > 0:
                start_last_year = last_year
                start_last_month = start_last_re
            else:
                start_last_year = int(last_year) - 1
                start_last_month = start_last_re + 12
        else:
            week_re = week.split('-')
            year_str = week_re[0]
            week_str = week_re[1].split('W')[1]
            end_week_re = end_week.split('-')
            end_year_str = end_week_re[0]
            end_week_str = end_week_re[1].split('W')[1]

            start_week_obj = '%s-%s-0' % (year_str, week_str)
            end_week_obj = '%s-%s-0' % (year_str, end_week_str)
            start_week = datetime.datetime.strptime(start_week_obj, '%Y-%U-%w')
            start_week = start_week + datetime.timedelta(days=-6)
            start_week = start_week.strftime("%Y%m%d")
            end_week_week = datetime.datetime.strptime(end_week_obj, '%Y-%U-%w').strftime("%Y%m%d")
            start_week_date = datetime.datetime.strptime(start_week, "%Y%m%d")
            end_week_date = datetime.datetime.strptime(end_week_obj, '%Y-%U-%w')
            last_week_re = (end_week_date - start_week_date).days
            end_last_week = start_week_date - relativedelta(days=1)
            start_last_week = end_last_week - relativedelta(days=last_week_re)
            start_last_year = start_last_week.year
            last_year = end_last_week.year
            start_last_week = start_last_week.isocalendar()[1]
            end_last_week = end_last_week.isocalendar()[1]

    if viewRange:
        viewRange = int(viewRange)
    user_group = user.group
    users = []
    user_list = UserProfile.objects.filter(state=1)
    if not user.user.is_superuser or not user_group.user.username == 'Ads':
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
        if user_list:
            for val in user_list:
                users.append(val.user_id)

    range_type_str = ''
    if start_month and range_type == 'Monthly':
        range_type_str = "%s-%s" % (start_month, end_month_month)
    if start_week and range_type == 'Weekly':
        range_type_str = "%s-%s" % (start_week, end_week_week)
    fields = [
        ('account', 'Account'),
        ('date_range', 'Date Range'),
        ('campaign_name', 'Campaign Name'),
        ('ad_group_name', 'Ad Group'),
        ('customer_search_term', 'Search Term'),
        ('impressions', 'Impressions'),
        ('clicks', 'Clicks'),
        ('spend', 'Spend'),
        ('day_total_orders', '7 Day Total Orders'),
        ('day_total_sales', '7 Day Total Sales'),
        ('acos', 'ACoS')
    ]
    data_li = []
    if sum_by_date == 'on':
        sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name', 'customer_search_term'). \
            filter(user_id__in=users, account=account).annotate(day_total_orders=Sum('day_total_orders'),
                                                impressions=Sum('impressions'), clicks=Sum('clicks'),
                                                spend=Sum('spend'), day_total_sales=Sum('day_total_sales'))
        if sTeam_obj:
            sTeam_obj = _get_spend(sTeam_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
            if search_key == 'campaign':
                sTeam_obj = sTeam_obj.filter(campaign__icontains=listKwd)
            elif search_key == 'targeting':
                sTeam_obj = sTeam_obj.filter(targeting__icontains=listKwd)
            elif search_key == 'search_term':
                sTeam_obj = sTeam_obj.filter(customer_search_term__icontains=listKwd)
        if conventers == 'new':
            last_sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name','customer_search_term').\
                                                filter(user_id__in=users, account=account)
            if threshold:
                sTeam_obj = sTeam_obj.filter(day_total_orders__gte=threshold)
            if last_sTeam_obj:
                last_sTeam_obj = _get_spend(last_sTeam_obj,range_type, start_last_year, last_year, end_month_str=last_month,
                                              month_str=start_last_month, week_str=start_last_week,
                                              end_week_str=end_last_week)
            for s_val in sTeam_obj:
                checks = {
                    'account': s_val['account'],
                    'campaign_name': s_val['campaign_name'],
                    'ad_group_name': s_val['ad_group_name'],
                    'customer_search_term': s_val['customer_search_term']
                }
                if checks not in last_sTeam_obj:
                    s_val['date_range'] = range_type_str
                    s_val['account'] = account_li[s_val['account']]
                    if float(s_val['day_total_sales']):
                        acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                        s_val['acos'] = '%.2f' % acos
                    else:
                        s_val['acos'] = 0
                    data_li.append(s_val)
        elif conventers == 'rising':
            last_sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                       'customer_search_term').filter(user_id__in=users,
                                                       account=account).annotate(
                day_total_orders=Sum('day_total_orders'),
                impressions=Sum('impressions'), clicks=Sum('clicks'),
                spend=Sum('spend'), day_total_sales=Sum('day_total_sales'))
            if search_key == 'campaign':
                last_sTeam_obj = last_sTeam_obj.filter(campaign__icontains=listKwd)
            elif search_key == 'targeting':
                last_sTeam_obj = last_sTeam_obj.filter(targeting__icontains=listKwd)
            elif search_key == 'search_term':
                last_sTeam_obj = last_sTeam_obj.filter(customer_search_term__icontains=listKwd)
            if last_sTeam_obj:
                last_sTeam_obj = _get_spend(last_sTeam_obj,range_type, start_last_year, last_year, end_month_str=last_month,
                                              month_str=start_last_month, week_str=start_last_week,
                                              end_week_str=end_last_week)
                if last_sTeam_obj:
                    for l_val in last_sTeam_obj:
                        sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                              'customer_search_term').filter(user_id__in=users,
                                                              account=account,campaign_name=l_val['campaign_name'],
                                                              ad_group_name=l_val['ad_group_name'],
                                                              customer_search_term=l_val['customer_search_term']). \
                            annotate(day_total_orders=Sum('day_total_orders'))
                        if sTeam_obj:
                            sTeam_obj = _get_spend(sTeam_obj, range_type, year_str, end_year_str,end_month_str=end_month_str,
                                                   month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                            if sTeam_obj[0]['day_total_orders'] > l_val['day_total_orders']:
                                if threshold:
                                    if not l_val['day_total_orders'] == 0:
                                        checks_term = (sTeam_obj[0]['day_total_orders'] - l_val['day_total_orders'])/l_val['day_total_orders'] * 100
                                    else:
                                        checks_term = 0
                                    if checks_term < threshold:
                                        continue
                                l_val['date_range'] = range_type_str
                                l_val['account'] = account_li[l_val['account']]
                                if float(l_val['day_total_sales']):
                                    acos = float(l_val['spend']) / float(l_val['day_total_sales'])
                                    l_val['acos'] = '%.2f' % acos
                                else:
                                    l_val['acos'] = 0
                                data_li.append(l_val)
        elif conventers == 'non':
            sTeam_obj = sTeam_obj.filter(day_total_orders=0)
            if threshold:
                sTeam_obj = sTeam_obj.filter(clicks__gte=threshold)
            if sTeam_obj:
                for s_val in sTeam_obj:
                    s_val['date_range'] = range_type_str
                    s_val['account'] = account_li[s_val['account']]
                    if float(s_val['day_total_sales']):
                        acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                        s_val['acos'] = '%.2f' % acos
                    else:
                        s_val['acos'] = 0
                    data_li.append(s_val)
        else:
            for s_val in sTeam_obj:
                s_val['date_range'] = range_type_str
                s_val['account'] = account_li[s_val['account']]
                if float(s_val['day_total_sales']):
                    acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                    s_val['acos'] = '%.2f' % acos
                else:
                    s_val['acos'] = 0
                data_li.append(s_val)

    else:
        branth_date = SearchTeam.objects.values('year_str', 'week', 'month').filter(user_id__in=users, account=account).\
                        annotate(day_total_or=Sum('day_total_orders'))
        if branth_date:
            for val in branth_date:
                sum_off_week = 0
                sum_off_month = 0
                if val['month']:
                    if val['month'] < 10:
                        range_type_str = "%s0%s" % (val['year_str'], val['month'])
                    else:
                        range_type_str = "%s%s" % (val['year_str'], val['month'])
                    if val['month'] == 1:
                        sum_off_year = val['year_str'] - 1
                        sum_off_month = 12
                    else:
                        sum_off_year = val['year_str']
                        sum_off_month = val['month'] - 1
                if val['week']:
                    week_obj = '%s-%s-0' % (val['year_str'], val['week'])
                    start_week = datetime.datetime.strptime(week_obj, '%Y-%U-%w')
                    start_week_str = start_week + datetime.timedelta(days=-6)
                    range_type_str = "%s-%s" % (start_week_str.strftime("%Y%m%d"), start_week.strftime("%Y%m%d"))
                    sum_off_week_re = start_week_str - relativedelta(days=1)
                    sum_off_year = sum_off_week_re.year
                    sum_off_week = sum_off_week_re.isocalendar()[1]
                sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name', 'customer_search_term').\
                            filter(user_id__in=users, account=account,year_str=val['year_str'], week=val['week'],
                                   month=val['month']).annotate(day_total_orders=Sum('day_total_orders'),
                                                                impressions=Sum('impressions'), clicks=Sum('clicks'),
                                                                spend=Sum('spend'), day_total_sales=Sum('day_total_sales'))
                if search_key == 'campaign':
                    sTeam_obj = sTeam_obj.filter(campaign__icontains=listKwd)
                elif search_key == 'targeting':
                    sTeam_obj = sTeam_obj.filter(targeting__icontains=listKwd)
                elif search_key == 'search_term':
                    sTeam_obj = sTeam_obj.filter(customer_search_term__icontains=listKwd)

                if conventers == 'new':
                    last_sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                               'customer_search_term').filter(user_id__in=users,
                                                               account=account, year_str=sum_off_year, week=sum_off_week,
                                                               month=sum_off_month)
                    if threshold:
                        sTeam_obj = sTeam_obj.filter(day_total_orders__gte=threshold)
                    for s_val in sTeam_obj:
                        checks = {
                            'account':s_val['account'],
                            'campaign_name':s_val['campaign_name'],
                            'ad_group_name':s_val['ad_group_name'],
                            'customer_search_term':s_val['customer_search_term']
                        }
                        if checks not in last_sTeam_obj:
                            s_val['date_range'] = range_type_str
                            s_val['account'] = account_li[s_val['account']]
                            if float(s_val['day_total_sales']):
                                acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                                s_val['acos'] = '%.2f' % acos
                            else:
                                s_val['acos'] = 0
                            data_li.append(s_val)
                elif conventers == 'rising':
                    last_sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                               'customer_search_term').filter(user_id__in=users,
                                                               account=account,year_str=sum_off_year,week=sum_off_week,
                                                               month=sum_off_month).annotate(day_total_orders=Sum('day_total_orders'),
                                                               impressions=Sum('impressions'), clicks=Sum('clicks'),
                                                               spend=Sum('spend'), day_total_sales=Sum('day_total_sales'))
                    if search_key == 'campaign':
                        last_sTeam_obj = last_sTeam_obj.filter(campaign__icontains=listKwd)
                    elif search_key == 'targeting':
                        last_sTeam_obj = last_sTeam_obj.filter(targeting__icontains=listKwd)
                    elif search_key == 'search_term':
                        last_sTeam_obj = last_sTeam_obj.filter(customer_search_term__icontains=listKwd)
                    if last_sTeam_obj:
                        for l_val in last_sTeam_obj:
                            sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                                  'customer_search_term').filter(user_id__in=users,
                                                                  account=account,year_str=val['year_str'],
                                                                  week=val['week'],month=val['month'],campaign_name=
                                                                  l_val['campaign_name'],ad_group_name=l_val['ad_group_name'],
                                                                  customer_search_term=l_val['customer_search_term']).\
                                annotate(day_total_orders=Sum('day_total_orders'))
                            if sTeam_obj and sTeam_obj[0]['day_total_orders'] > l_val['day_total_orders']:
                                if threshold:
                                    if not l_val['day_total_orders'] == 0:
                                        checks_term = (sTeam_obj[0]['day_total_orders'] - l_val['day_total_orders'])/l_val['day_total_orders'] * 100
                                    else:
                                        checks_term = 0
                                    if checks_term < threshold:
                                        continue
                                l_val['date_range'] = range_type_str
                                l_val['account'] = account_li[l_val['account']]
                                if float(l_val['day_total_sales']):
                                    acos = float(l_val['spend']) / float(l_val['day_total_sales'])
                                    l_val['acos'] = '%.2f' % acos
                                else:
                                    l_val['acos'] = 0
                                data_li.append(l_val)
                elif conventers == 'non':
                    sTeam_obj = sTeam_obj.filter(day_total_orders=0)
                    if threshold:
                        sTeam_obj = sTeam_obj.filter(clicks__gte=threshold)
                    if sTeam_obj:
                        for s_val in sTeam_obj:
                            s_val['date_range'] = range_type_str
                            s_val['account'] = account_li[s_val['account']]
                            if float(s_val['day_total_sales']):
                                acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                                s_val['acos'] = '%.2f' % acos
                            else:
                                s_val['acos'] = 0
                            data_li.append(s_val)
                else:
                    for s_val in sTeam_obj:
                        s_val['date_range'] = range_type_str
                        s_val['account'] = account_li[s_val['account']]
                        if float(s_val['day_total_sales']):
                            acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                            s_val['acos'] = '%.2f' % acos
                        else:
                            s_val['acos'] = 0
                        data_li.append(s_val)


    if data_li:
        limit = request.GET.get('limit', 20)
        page = request.GET.get('page', 1)
        re_limit = limit

        total_count = len(data_li)
        total_page = round(len(data_li) / int(limit))
        if int(limit) >= total_count:
            limit = total_count
        paginator = Paginator(data_li, limit)
        try:
            data = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data = paginator.page(paginator.num_pages)
        data = {
            'data': data,
            'fields': fields,
            'total_count': total_count,
            'total_page': total_page,
            're_limit': int(re_limit),
            'limit': int(limit),
            'page': page,
            'user': user,
            'viewRange': viewRange,
            'account': account,
            'range_type': range_type,
            'sum_by_date': sum_by_date,
            'search_key': search_key,
            'listKwd': listKwd,
            'week': week,
            'end_week': end_week,
            'month': month,
            'end_month': end_month,
            'conventers': conventers,
            'threshold': threshold,
            'order_type': order_type,
            'order_dasc': order_dasc,
            'avator': user.user.username[0]
        }
    else:
        data = {
            'data': '',
            'fields': fields,
            'user': user,
            'viewRange': viewRange,
            'account': account,
            'range_type': range_type,
            'sum_by_date': sum_by_date,
            'search_key': search_key,
            'listKwd': listKwd,
            'week': week,
            'end_week': end_week,
            'month': month,
            'end_month': end_month,
            'conventers': conventers,
            'threshold': threshold,
            'avator': user.user.username[0]
        }

    return render(request, 'ads_manager/kwd_alert.html', data)

@csrf_exempt
def export_kwd_alert(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    viewRange = request.GET.get('viewRange', user.user.id)
    account = request.GET.get('account', '1')
    range_type = request.GET.get('range_type', 'Weekly')
    sum_by_date = request.GET.get('sum_by_date', '')
    search_key = request.GET.get('search_key', 'all')
    listKwd = request.GET.get('listKwd', '')
    week = request.GET.get('week', '')
    end_week = request.GET.get('end_week', '')
    month = request.GET.get('month', '')
    end_month = request.GET.get('end_month', '')
    conventers = request.GET.get('conventers', '')
    threshold = request.GET.get('threshold', 0)
    threshold = float(threshold)

    month_str = None
    end_month_str = None
    week_str = None
    end_week_str = None
    start_month = None
    end_month_month = None
    start_week = None
    end_week_week = None
    last_year = None
    start_last_year = None
    start_last_month = None
    last_month = None
    start_last_week = None
    end_last_week = None
    if sum_by_date == 'on':
        if range_type == 'Monthly':
            month_re = month.split('-')
            year_str = month_re[0]
            month_str = month_re[1]
            end_month_re = end_month.split('-')
            end_year_str = end_month_re[0]
            end_month_str = end_month_re[1]
            start_month = "%s%s" % (year_str, month_str)
            end_month_month = "%s%s" % (end_year_str, end_month_str)

            last_month_re = _get_month_re(start_month, end_month_month)
            if month_str == 1:
                last_year = int(year_str) - 1
                last_month = 12
            else:
                last_year = year_str
                last_month = int(month_str) - 1
            start_last_re = last_month - last_month_re
            if last_month_re == 0:
                start_last_year = last_year
                start_last_month = last_month
            elif start_last_re > 0:
                start_last_year = last_year
                start_last_month = start_last_re
            else:
                start_last_year = int(last_year) - 1
                start_last_month = start_last_re + 12
        else:
            week_re = week.split('-')
            year_str = week_re[0]
            week_str = week_re[1].split('W')[1]
            end_week_re = end_week.split('-')
            end_year_str = end_week_re[0]
            end_week_str = end_week_re[1].split('W')[1]

            start_week_obj = '%s-%s-0' % (year_str, week_str)
            end_week_obj = '%s-%s-0' % (year_str, end_week_str)
            start_week = datetime.datetime.strptime(start_week_obj, '%Y-%U-%w')
            start_week = start_week + datetime.timedelta(days=-6)
            start_week = start_week.strftime("%Y%m%d")
            end_week_week = datetime.datetime.strptime(end_week_obj, '%Y-%U-%w').strftime("%Y%m%d")
            start_week_date = datetime.datetime.strptime(start_week, "%Y%m%d")
            end_week_date = datetime.datetime.strptime(end_week_obj, '%Y-%U-%w')
            last_week_re = (end_week_date - start_week_date).days
            end_last_week = start_week_date - relativedelta(days=1)
            start_last_week = end_last_week - relativedelta(days=last_week_re)
            start_last_year = start_last_week.year
            last_year = end_last_week.year
            start_last_week = start_last_week.isocalendar()[1]
            end_last_week = end_last_week.isocalendar()[1]

    if viewRange:
        viewRange = int(viewRange)
    user_group = user.group
    users = []
    user_list = UserProfile.objects.filter(state=1)
    if not user.user.is_superuser or not user_group.user.username == 'Ads':
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
        if user_list:
            for val in user_list:
                users.append(val.user_id)
    range_type_str = ''
    if start_month and range_type == 'Monthly':
        range_type_str = "%s-%s" % (start_month, end_month_month)
    if start_week and range_type == 'Weekly':
        range_type_str = "%s-%s" % (start_week, end_week_week)
    fields = [
        'Account',
        'Date Range',
        'Campaign Name',
        'Ad Group',
        'Search Term',
        'Impressions',
        'Clicks',
        'Spend',
        '7 Day Total Orders',
        '7 Day Total Sales',
        'ACoS'
    ]
    data_li = []
    if sum_by_date == 'on':
        sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name', 'customer_search_term'). \
            filter(user_id__in=users, account=account).annotate(day_total_orders=Sum('day_total_orders'),
                                                impressions=Sum('impressions'), clicks=Sum('clicks'),
                                                spend=Sum('spend'), day_total_sales=Sum('day_total_sales'))
        if sTeam_obj:
            sTeam_obj = _get_spend(sTeam_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
            if search_key == 'campaign':
                sTeam_obj = sTeam_obj.filter(campaign__icontains=listKwd)
            elif search_key == 'targeting':
                sTeam_obj = sTeam_obj.filter(targeting__icontains=listKwd)
            elif search_key == 'search_term':
                sTeam_obj = sTeam_obj.filter(customer_search_term__icontains=listKwd)
        if conventers == 'new':
            last_sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name','customer_search_term').\
                                                filter(user_id__in=users, account=account)
            if threshold:
                sTeam_obj = sTeam_obj.filter(day_total_orders__gte=threshold)
            if last_sTeam_obj:
                last_sTeam_obj = _get_spend(last_sTeam_obj,range_type, start_last_year, last_year, end_month_str=last_month,
                                              month_str=start_last_month, week_str=start_last_week,
                                              end_week_str=end_last_week)
            for s_val in sTeam_obj:
                checks = {
                    'account': s_val['account'],
                    'campaign_name': s_val['campaign_name'],
                    'ad_group_name': s_val['ad_group_name'],
                    'customer_search_term': s_val['customer_search_term']
                }
                if checks not in last_sTeam_obj:
                    s_val['date_range'] = range_type_str
                    s_val['account'] = account_li[s_val['account']]
                    if float(s_val['day_total_sales']):
                        acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                        s_val['acos'] = '%.2f' % acos
                    else:
                        s_val['acos'] = 0
                    data_li.append([
                        s_val['account'],
                        s_val['date_range'],
                        s_val['campaign_name'],
                        s_val['ad_group_name'],
                        s_val['customer_search_term'],
                        s_val['impressions'],
                        s_val['clicks'],
                        s_val['spend'],
                        s_val['day_total_orders'],
                        s_val['day_total_sales'],
                        s_val['acos']
                    ])
        elif conventers == 'rising':
            last_sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                       'customer_search_term').filter(user_id__in=users,
                                                       account=account).annotate(
                day_total_orders=Sum('day_total_orders'),
                impressions=Sum('impressions'), clicks=Sum('clicks'),
                spend=Sum('spend'), day_total_sales=Sum('day_total_sales'))
            if search_key == 'campaign':
                last_sTeam_obj = last_sTeam_obj.filter(campaign__icontains=listKwd)
            elif search_key == 'targeting':
                last_sTeam_obj = last_sTeam_obj.filter(targeting__icontains=listKwd)
            elif search_key == 'search_term':
                last_sTeam_obj = last_sTeam_obj.filter(customer_search_term__icontains=listKwd)
            if last_sTeam_obj:
                last_sTeam_obj = _get_spend(last_sTeam_obj,range_type, start_last_year, last_year, end_month_str=last_month,
                                              month_str=start_last_month, week_str=start_last_week,
                                              end_week_str=end_last_week)
                if last_sTeam_obj:
                    for l_val in last_sTeam_obj:
                        sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                              'customer_search_term').filter(user_id__in=users,
                                                              account=account,campaign_name=l_val['campaign_name'],
                                                              ad_group_name=l_val['ad_group_name'],
                                                              customer_search_term=l_val['customer_search_term']). \
                            annotate(day_total_orders=Sum('day_total_orders'))
                        if sTeam_obj:
                            sTeam_obj = _get_spend(sTeam_obj, range_type, year_str, end_year_str,end_month_str=end_month_str,
                                                   month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                            if sTeam_obj[0]['day_total_orders'] > l_val['day_total_orders']:
                                if threshold:
                                    if not l_val['day_total_orders'] == 0:
                                        checks_term = (sTeam_obj[0]['day_total_orders'] - l_val['day_total_orders'])/l_val['day_total_orders'] * 100
                                    else:
                                        checks_term = 0
                                    if checks_term < threshold:
                                        continue
                                l_val['date_range'] = range_type_str
                                l_val['account'] = account_li[l_val['account']]
                                if float(l_val['day_total_sales']):
                                    acos = float(l_val['spend']) / float(l_val['day_total_sales'])
                                    l_val['acos'] = '%.2f' % acos
                                else:
                                    l_val['acos'] = 0
                                data_li.append([
                                    l_val['account'],
                                    l_val['date_range'],
                                    l_val['campaign_name'],
                                    l_val['ad_group_name'],
                                    l_val['customer_search_term'],
                                    l_val['impressions'],
                                    l_val['clicks'],
                                    l_val['spend'],
                                    l_val['day_total_orders'],
                                    l_val['day_total_sales'],
                                    l_val['acos']
                                ])
        elif conventers == 'non':
            sTeam_obj = sTeam_obj.filter(day_total_orders=0)
            if threshold:
                sTeam_obj = sTeam_obj.filter(clicks__gte=threshold)
            if sTeam_obj:
                for s_val in sTeam_obj:
                    s_val['date_range'] = range_type_str
                    s_val['account'] = account_li[s_val['account']]
                    if float(s_val['day_total_sales']):
                        acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                        s_val['acos'] = '%.2f' % acos
                    else:
                        s_val['acos'] = 0
                    data_li.append([
                        s_val['account'],
                        s_val['date_range'],
                        s_val['campaign_name'],
                        s_val['ad_group_name'],
                        s_val['customer_search_term'],
                        s_val['impressions'],
                        s_val['clicks'],
                        s_val['spend'],
                        s_val['day_total_orders'],
                        s_val['day_total_sales'],
                        s_val['acos']
                    ])
        else:
            for s_val in sTeam_obj:
                s_val['date_range'] = range_type_str
                s_val['account'] = account_li[s_val['account']]
                if float(s_val['day_total_sales']):
                    acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                    s_val['acos'] = '%.2f' % acos
                else:
                    s_val['acos'] = 0
                data_li.append([
                    s_val['account'],
                    s_val['date_range'],
                    s_val['campaign_name'],
                    s_val['ad_group_name'],
                    s_val['customer_search_term'],
                    s_val['impressions'],
                    s_val['clicks'],
                    s_val['spend'],
                    s_val['day_total_orders'],
                    s_val['day_total_sales'],
                    s_val['acos']
                ])

    else:
        branth_date = SearchTeam.objects.values('year_str', 'week', 'month').filter(user_id__in=users, account=account).\
                        annotate(day_total_or=Sum('day_total_orders'))
        if branth_date:
            for val in branth_date:
                sum_off_week = 0
                sum_off_month = 0
                if val['month']:
                    if val['month'] < 10:
                        range_type_str = "%s0%s" % (val['year_str'], val['month'])
                    else:
                        range_type_str = "%s%s" % (val['year_str'], val['month'])
                    if val['month'] == 1:
                        sum_off_year = val['year_str'] - 1
                        sum_off_month = 12
                    else:
                        sum_off_year = val['year_str']
                        sum_off_month = val['month'] - 1
                if val['week']:
                    week_obj = '%s-%s-0' % (val['year_str'], val['week'])
                    start_week = datetime.datetime.strptime(week_obj, '%Y-%U-%w')
                    start_week_str = start_week + datetime.timedelta(days=-6)
                    range_type_str = "%s-%s" % (start_week_str.strftime("%Y%m%d"), start_week.strftime("%Y%m%d"))
                    sum_off_week_re = start_week_str - relativedelta(days=1)
                    sum_off_year = sum_off_week_re.year
                    sum_off_week = sum_off_week_re.isocalendar()[1]
                sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name', 'customer_search_term').\
                            filter(user_id__in=users, account=account,year_str=val['year_str'], week=val['week'],
                                   month=val['month']).annotate(day_total_orders=Sum('day_total_orders'),
                                                                impressions=Sum('impressions'), clicks=Sum('clicks'),
                                                                spend=Sum('spend'), day_total_sales=Sum('day_total_sales'))
                if search_key == 'campaign':
                    sTeam_obj = sTeam_obj.filter(campaign__icontains=listKwd)
                elif search_key == 'targeting':
                    sTeam_obj = sTeam_obj.filter(targeting__icontains=listKwd)
                elif search_key == 'search_term':
                    sTeam_obj = sTeam_obj.filter(customer_search_term__icontains=listKwd)

                if conventers == 'new':
                    last_sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                               'customer_search_term').filter(user_id__in=users,
                                                               account=account, year_str=sum_off_year, week=sum_off_week,
                                                               month=sum_off_month)
                    if threshold:
                        sTeam_obj = sTeam_obj.filter(day_total_orders__gte=threshold)
                    for s_val in sTeam_obj:
                        checks = {
                            'account':s_val['account'],
                            'campaign_name':s_val['campaign_name'],
                            'ad_group_name':s_val['ad_group_name'],
                            'customer_search_term':s_val['customer_search_term']
                        }
                        if checks not in last_sTeam_obj:
                            s_val['date_range'] = range_type_str
                            s_val['account'] = account_li[s_val['account']]
                            if float(s_val['day_total_sales']):
                                acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                                s_val['acos'] = '%.2f' % acos
                            else:
                                s_val['acos'] = 0
                            data_li.append([
                                s_val['account'],
                                s_val['date_range'],
                                s_val['campaign_name'],
                                s_val['ad_group_name'],
                                s_val['customer_search_term'],
                                s_val['impressions'],
                                s_val['clicks'],
                                s_val['spend'],
                                s_val['day_total_orders'],
                                s_val['day_total_sales'],
                                s_val['acos']
                            ])
                elif conventers == 'rising':
                    last_sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                               'customer_search_term').filter(user_id__in=users,
                                                               account=account,year_str=sum_off_year,week=sum_off_week,
                                                               month=sum_off_month).annotate(day_total_orders=Sum('day_total_orders'),
                                                               impressions=Sum('impressions'), clicks=Sum('clicks'),
                                                               spend=Sum('spend'), day_total_sales=Sum('day_total_sales'))
                    if search_key == 'campaign':
                        last_sTeam_obj = last_sTeam_obj.filter(campaign__icontains=listKwd)
                    elif search_key == 'targeting':
                        last_sTeam_obj = last_sTeam_obj.filter(targeting__icontains=listKwd)
                    elif search_key == 'search_term':
                        last_sTeam_obj = last_sTeam_obj.filter(customer_search_term__icontains=listKwd)
                    if last_sTeam_obj:
                        for l_val in last_sTeam_obj:
                            sTeam_obj = SearchTeam.objects.values('account', 'campaign_name', 'ad_group_name',
                                                                  'customer_search_term').filter(user_id__in=users,
                                                                  account=account,year_str=val['year_str'],
                                                                  week=val['week'],month=val['month'],campaign_name=
                                                                  l_val['campaign_name'],ad_group_name=l_val['ad_group_name'],
                                                                  customer_search_term=l_val['customer_search_term']).\
                                annotate(day_total_orders=Sum('day_total_orders'))
                            if sTeam_obj and sTeam_obj[0]['day_total_orders'] > l_val['day_total_orders']:
                                if threshold:
                                    if not l_val['day_total_orders'] == 0:
                                        checks_term = (sTeam_obj[0]['day_total_orders'] - l_val['day_total_orders'])/l_val['day_total_orders'] * 100
                                    else:
                                        checks_term = 0
                                    if checks_term < threshold:
                                        continue
                                l_val['date_range'] = range_type_str
                                l_val['account'] = account_li[l_val['account']]
                                if float(l_val['day_total_sales']):
                                    acos = float(l_val['spend']) / float(l_val['day_total_sales'])
                                    l_val['acos'] = '%.2f' % acos
                                else:
                                    l_val['acos'] = 0
                                data_li.append([
                                    l_val['account'],
                                    l_val['date_range'],
                                    l_val['campaign_name'],
                                    l_val['ad_group_name'],
                                    l_val['customer_search_term'],
                                    l_val['impressions'],
                                    l_val['clicks'],
                                    l_val['spend'],
                                    l_val['day_total_orders'],
                                    l_val['day_total_sales'],
                                    l_val['acos']
                                ])
                elif conventers == 'non':
                    sTeam_obj = sTeam_obj.filter(day_total_orders=0)
                    if threshold:
                        sTeam_obj = sTeam_obj.filter(clicks__gte=threshold)
                    if sTeam_obj:
                        for s_val in sTeam_obj:
                            s_val['date_range'] = range_type_str
                            s_val['account'] = account_li[s_val['account']]
                            if float(s_val['day_total_sales']):
                                acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                                s_val['acos'] = '%.2f' % acos
                            else:
                                s_val['acos'] = 0
                            data_li.append([
                                s_val['account'],
                                s_val['date_range'],
                                s_val['campaign_name'],
                                s_val['ad_group_name'],
                                s_val['customer_search_term'],
                                s_val['impressions'],
                                s_val['clicks'],
                                s_val['spend'],
                                s_val['day_total_orders'],
                                s_val['day_total_sales'],
                                s_val['acos']
                            ])
                else:
                    for s_val in sTeam_obj:
                        s_val['date_range'] = range_type_str
                        s_val['account'] = account_li[s_val['account']]
                        if float(s_val['day_total_sales']):
                            acos = float(s_val['spend']) / float(s_val['day_total_sales'])
                            s_val['acos'] = '%.2f' % acos
                        else:
                            s_val['acos'] = 0
                        data_li.append([
                            s_val['account'],
                            s_val['date_range'],
                            s_val['campaign_name'],
                            s_val['ad_group_name'],
                            s_val['customer_search_term'],
                            s_val['impressions'],
                            s_val['clicks'],
                            s_val['spend'],
                            s_val['day_total_orders'],
                            s_val['day_total_sales'],
                            s_val['acos']
                        ])
    if not data_li:
        return HttpResponse(json.dumps({'code': 0, 'msg': u'数据不存在!'}), content_type='application/json')
    file_name = 'kwd_alert-%s.csv' % datetime.datetime.now().strftime('%Y-%m-%d')
    response = HttpResponse(content_type='text/csv')  # 设置头信息，告诉浏览器这是个文件
    response.write(codecs.BOM_UTF8)
    response['Content-Disposition'] = 'attachment;filename="%s"' % file_name
    writer = csv.writer(response)
    # 先写入columns_name
    writer.writerow(fields)
    writer.writerows(data_li)
    return response