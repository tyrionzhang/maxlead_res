# -*- coding: utf-8 -*-
import json
import datetime,csv,codecs
from dateutil.relativedelta import relativedelta
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.db.models import Sum
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from maxlead_site.views.app import App
from maxlead_site.models import AdsBrand,AdsCampaign,AdvProducts,CampaignPla,PurProduct,BizReport
from maxlead_site.models import UserProfile
from django.views.decorators.csrf import csrf_exempt
from maxlead_site.views.ads_manager.brand import account_li
from maxlead_site.views.ads_manager.brand_sku import _get_spend

def _get_month_re(date_str, end_date):
    v_year_end = datetime.datetime.strptime(end_date, '%Y%m').year
    v_month_end = datetime.datetime.strptime(end_date, '%Y%m').month
    v_year_start = datetime.datetime.strptime(date_str, '%Y%m').year
    v_month_start = datetime.datetime.strptime(date_str, '%Y%m').month
    interval = (v_year_end - v_year_start) * 12 + (v_month_end - v_month_start)
    return interval

def details(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    account = request.GET.get('account', '1')
    range_type = request.GET.get('range_type', 'Weekly')
    sum_by_date = request.GET.get('sum_by_date', '')
    search_key = request.GET.get('search_key', 'all')
    listKwd = request.GET.get('listKwd', '')
    week = request.GET.get('week', '')
    end_week = request.GET.get('end_week', '')
    month = request.GET.get('month', '')
    end_month = request.GET.get('end_month', '')
    other_self = request.GET.get('other_self', '')
    brand = request.GET.get('brand', '')
    ordder_field = request.GET.get('ordder_field', 'sp_sales')
    order_desc = request.GET.get('order_desc', '-')

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
    fields = [
        ('account', 'Account'),
        ('date_range', 'Date Range'),
        ('asin', 'ASIN'),
        ('sku', 'SKU'),
        ('brand', 'Brand'),
        ('impressions_sum', 'Impressions'),
        ('clicks_sum', 'Clicks'),
        ('ctr', 'CTR'),
        ('sp_spend', 'Spend'),
        ('self_units', 'Self Units'),
        ('self_sales', 'Self Sales'),
        ('cr', 'CR'),
        ('other_units', 'Other Units'),
        ('other_sales', 'Other Sales'),
        ('sp_sales', 'SP Sales'),
        ('all_sales', 'All Sales'),
        ('all_spend_sales', 'All Spend/All Sales'),
        ('sp_sales_sales', 'SP Sales/All Sales'),
        ('other_self', 'Other > Self'),
        ('hb_cr', 'CR环比'),
        ('hb_ctr', 'CTR环比')
    ]
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

    user_group = user.group
    users = []
    user_list = UserProfile.objects.filter(state=1)
    if not user.user.is_superuser and not user_group.user.username == 'Ads':
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
    if user_list:
        for val in user_list:
            users.append(val.user_id)

    brand_list = []
    brand_list_obj = AdsBrand.objects.filter(user_id__in=users).order_by('brand', '-id')
    if brand_list_obj:
        for val in brand_list_obj:
            if val.brand and not val.brand in brand_list:
                brand_list.append(val.brand)
    range_type_str = ''
    if start_month and range_type == 'Monthly':
        range_type_str = "%s-%s" % (start_month, end_month_month)
    if start_week and range_type == 'Weekly':
        range_type_str = "%s-%s" % (start_week, end_week_week)
    if sum_by_date == 'on':
        biz_obj = BizReport.objects.values("asin").filter(user_id__in=users, account=account).distinct().exclude(
            asin='')
        if brand:
            asin_li = AdsBrand.objects.values('asin').filter(user_id__in=users, brand=brand).distinct().exclude(asin='')
            biz_obj = biz_obj.filter(asin__in=asin_li)
        if biz_obj:
            biz_obj = _get_spend(biz_obj, range_type, year_str, end_year_str, end_month_str=end_month_str, month_str=month_str,
                             week_str=week_str, end_week_str=end_week_str)
    else:
        biz_obj = BizReport.objects.values('asin', 'year_str', 'month', 'week').filter(user_id__in=users, account=account)
        if brand:
            asin_li = AdsBrand.objects.values('asin').filter(user_id__in=users, brand=brand).distinct().exclude(asin='')
            biz_obj = biz_obj.filter(asin__in=asin_li)

    data_li = []
    if biz_obj:
        self_sales = 0
        biz_obj = biz_obj.annotate(all_sales=Sum('ordered_product_sales'))
        for val in biz_obj:
            val['account'] = ''
            val['date_range'] = ''
            val['impressions_sum'] = 0
            val['clicks_sum'] = 0
            val['ctr'] = ''
            val['sp_spend'] = 0
            val['self_units'] = 0
            val['self_sales'] = 0
            val['cr'] = ''
            val['other_units'] = 0
            val['other_sales'] = 0
            val['sp_sales'] = 0
            val['all_sales'] = 0
            val['all_spend_sales'] = 0
            val['sp_sales_sales'] = 0
            val['other_self'] = ''
            val['hb_cr'] = ''
            val['hb_ctr'] = ''
            if not sum_by_date == 'on':
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

            val['date_range'] = range_type_str
            val['account'] = account_li[int(account)]
            adv_obj = AdvProducts.objects.filter(user_id__in=users, account=account, advertised_asin=val['asin'])
            pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, advertised_asin=val['asin'])
            brand_obj = AdsBrand.objects.filter(user_id__in=users, asin=val['asin'])
            if brand_obj:
                val['sku'] = brand_obj[0].sku
                val['brand'] = brand_obj[0].brand
            else:
                val['sku'] = ''
                val['brand'] = ''
            if adv_obj:
                if sum_by_date == 'on':
                    last_adv_obj = _get_spend(adv_obj, range_type, start_last_year, last_year, end_month_str=last_month,
                                              month_str=start_last_month, week_str=start_last_week,
                                              end_week_str=end_last_week)
                    adv_obj = _get_spend(adv_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                else:
                    last_adv_obj = adv_obj.filter(year_str=sum_off_year, month=sum_off_month, week=sum_off_week)
                    adv_obj = adv_obj.filter(year_str=val['year_str'], month=val['month'], week=val['week'])
                if adv_obj:
                    adv_obj = adv_obj.aggregate(self_sales=Sum('day_advertised_sku_sales'),
                                                self_units=Sum('day_advertised_sku_units'), sp_spend=Sum('spend'),
                                                impressions_sum=Sum('impressions'), clicks_sum=Sum('clicks'))
                    impressions_sum = adv_obj['impressions_sum']
                    clicks_sum = adv_obj['clicks_sum']
                    sp_spend = adv_obj['sp_spend']
                    self_units = adv_obj['self_units']
                    self_sales = adv_obj['sp_spend']
                    if impressions_sum == 0:
                        ctr = 0
                    else:
                        ctr = clicks_sum / impressions_sum * 100
                    if clicks_sum == 0:
                        cr = 0
                    else:
                        cr = self_units / clicks_sum * 100
                    if search_key == 'CTR' and ctr >= float(listKwd):
                        biz_obj.remove(val)
                        continue
                    if search_key == 'CR' and cr >= float(listKwd):
                        biz_obj.remove(val)
                        continue

                    if last_adv_obj:
                        adv_obj = adv_obj.aggregate(hb_self_units=Sum('day_advertised_sku_units'),
                                                    hb_impressions_sum=Sum('impressions'),
                                                    hb_clicks_sum=Sum('clicks'))
                        hb_impressions_sum = adv_obj['hb_impressions_sum']
                        hb_clicks_sum = adv_obj['hb_clicks_sum']
                        hb_self_units = adv_obj['hb_self_units']
                        if hb_impressions_sum == 0:
                            hb_ctr = 0
                        else:
                            hb_ctr = hb_clicks_sum / hb_impressions_sum * 100
                        if hb_clicks_sum == 0:
                            hb_cr = 0
                        else:
                            hb_cr = hb_self_units / hb_clicks_sum * 100
                        val['hb_ctr'] = (ctr - hb_ctr) / hb_ctr * 100
                        val['hb_ctr'] = '%.2f' % val['hb_ctr']
                        val['hb_cr'] = (cr - hb_cr) / hb_cr * 100
                        val['hb_cr'] = '%.2f' % val['hb_cr']

                    val['ctr'] = '%.2f' % ctr
                    val['cr'] = '%.2f' % cr
                    val['impressions_sum'] = impressions_sum
                    val['clicks_sum'] = clicks_sum
                    val['sp_spend'] = sp_spend
                    val['self_units'] = self_units
                    val['self_sales'] = self_sales
                    if val['all_sales'] == 0:
                        val['all_spend_sales'] = 0
                    else:
                        val['all_spend_sales'] = sp_spend / val['all_sales'] * 100
                        val['all_spend_sales'] = '%.2f' % val['all_spend_sales']
            if pur_obj:
                if sum_by_date == 'on':
                    pur_obj = _get_spend(pur_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                else:
                    pur_obj = pur_obj.filter(year_str=val['year_str'], month=val['month'], week=val['week'])
                if pur_obj:
                    pur_obj = pur_obj.aggregate(other_units=Sum('day_other_sku_units'),
                                                other_sales=Sum('day_other_sku_sales'))
                    other_units = pur_obj['other_units']
                    other_sales = pur_obj['other_sales']
                    sp_sales = other_sales + self_sales
                    val['other_units'] = other_units
                    val['other_sales'] = other_sales
                    val['sp_sales'] = '%.2f' % sp_sales
                    if val['all_sales'] == 0:
                        val['sp_sales_sales'] = 0
                    else:
                        val['sp_sales_sales'] = sp_sales / val['all_sales'] * 100
                        val['sp_sales_sales'] = '%.2f' % val['sp_sales_sales']
                    if other_sales > self_sales:
                        val['other_self'] = 'Y'
                    else:
                        if other_self == 'on':
                            biz_obj.remove(val)
                            continue
                        val['other_self'] = 'N'
            data_li.append({
                'account' : val['account'],
                'date_range' : val['date_range'],
                'asin' : val['asin'],
                'sku' : val['sku'],
                'brand' : val['brand'],
                'impressions_sum' : val['impressions_sum'],
                'clicks_sum' : val['clicks_sum'],
                'ctr' : val['ctr'],
                'sp_spend' : val['sp_spend'],
                'self_units' : val['self_units'],
                'self_sales' : val['self_sales'],
                'cr' : val['cr'],
                'other_units' : val['other_units'],
                'other_sales' : val['other_sales'],
                'sp_sales' : val['sp_sales'],
                'all_sales' : val['all_sales'],
                'all_spend_sales' : val['all_spend_sales'],
                'sp_sales_sales' : val['sp_sales_sales'],
                'other_self' : val['other_self'],
                'hb_cr' : val['hb_cr'],
                'hb_ctr' : val['hb_ctr']
            })

        for i in range(0, len(data_li)):
            for n in range(i+1, len(data_li)):
                if not order_desc:
                    if float(data_li[i][ordder_field]) > float(data_li[n][ordder_field]):
                        check = data_li[n]
                        data_li[n] = data_li[i]
                        data_li[i] = check
                else:
                    if float(data_li[i][ordder_field]) < float(data_li[n][ordder_field]):
                        check = data_li[i]
                        data_li[i] = data_li[n]
                        data_li[n] = check
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
            'brand': brand,
            'account': account,
            'range_type': range_type,
            'sum_by_date': sum_by_date,
            'search_key': search_key,
            'listKwd': listKwd,
            'week': week,
            'end_week': end_week,
            'month': month,
            'end_month': end_month,
            'other_self': other_self,
            'brand_list': brand_list,
            'ordder_field': ordder_field,
            'order_desc': order_desc,
            'avator': user.user.username[0]
        }
    else:
        data = {
            'data': '',
            'fields': fields,
            'user': user,
            'brand': brand,
            'account': account,
            'range_type': range_type,
            'sum_by_date': sum_by_date,
            'search_key': search_key,
            'listKwd': listKwd,
            'week': week,
            'end_week': end_week,
            'month': month,
            'end_month': end_month,
            'other_self': other_self,
            'brand_list': brand_list,
            'avator': user.user.username[0]
        }


    return render(request, 'ads_manager/details.html', data)

@csrf_exempt
def export_details(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    account = request.GET.get('account', '1')
    range_type = request.GET.get('range_type', 'Weekly')
    sum_by_date = request.GET.get('sum_by_date', '')
    search_key = request.GET.get('search_key', 'all')
    listKwd = request.GET.get('listKwd', '')
    week = request.GET.get('week', '')
    end_week = request.GET.get('end_week', '')
    month = request.GET.get('month', '')
    end_month = request.GET.get('end_month', '')
    other_self = request.GET.get('other_self', '')
    brand = request.GET.get('brand', '')

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
    fields = [
        'Account',
        'Date Range',
        'ASIN',
        'SKU',
        'Brand',
        'Impressions',
        'Clicks',
        'CTR',
        'Spend',
        'Self Units',
        'Self Sales',
        'CR',
        'Other Units',
        'Other Sales',
        'SP Sales',
        'All Sales',
        'All Spend/All Sales',
        'SP Sales/All Sales',
        'Other > Self',
        'CR环比下降',
        'CTR环比下降'
    ]
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

    user_group = user.group
    users = []
    user_list = UserProfile.objects.filter(state=1)
    if not user.user.is_superuser and not user_group.user.username == 'Ads':
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
    if user_list:
        for val in user_list:
            users.append(val.user_id)

    range_type_str = ''
    if start_month and range_type == 'Monthly':
        range_type_str = "%s-%s" % (start_month, end_month_month)
    if start_week and range_type == 'Weekly':
        range_type_str = "%s-%s" % (start_week, end_week_week)
    if sum_by_date == 'on':
        biz_obj = BizReport.objects.values("asin").filter(user_id__in=users, account=account).distinct().exclude(
            asin='')
        if brand:
            asin_li = AdsBrand.objects.values('asin').filter(user_id__in=users, brand=brand).distinct().exclude(asin='')
            biz_obj = biz_obj.filter(asin__in=asin_li)
        if biz_obj:
            biz_obj = _get_spend(biz_obj, range_type, year_str, end_year_str, end_month_str=end_month_str, month_str=month_str,
                             week_str=week_str, end_week_str=end_week_str)
    else:
        biz_obj = BizReport.objects.values('asin', 'year_str', 'month', 'week').filter(user_id__in=users, account=account)
        if brand:
            asin_li = AdsBrand.objects.values('asin').filter(user_id__in=users, brand=brand).distinct().exclude(asin='')
            biz_obj = biz_obj.filter(asin__in=asin_li)

    if not biz_obj:
        return HttpResponse(json.dumps({'code': 0, 'msg': u'数据不存在!'}), content_type='application/json')
    file_name = 'details-%s.csv' % datetime.datetime.now().strftime('%Y-%m-%d')
    data = []
    if biz_obj:
        self_sales = 0
        biz_obj = biz_obj.annotate(all_sales=Sum('ordered_product_sales'))
        for val in biz_obj:
            val['account'] = ''
            val['date_range'] = ''
            val['impressions_sum'] = 0
            val['clicks_sum'] = 0
            val['ctr'] = ''
            val['sp_spend'] = 0
            val['self_units'] = 0
            val['self_sales'] = 0
            val['cr'] = ''
            val['other_units'] = 0
            val['other_sales'] = 0
            val['sp_sales'] = 0
            val['all_sales'] = 0
            val['all_spend_sales'] = 0
            val['sp_sales_sales'] = 0
            val['other_self'] = ''
            val['hb_cr'] = ''
            val['hb_ctr'] = ''
            if not sum_by_date == 'on':
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

            val['date_range'] = range_type_str
            val['account'] = account_li[int(account)]
            adv_obj = AdvProducts.objects.filter(user_id__in=users, account=account, advertised_asin=val['asin'])
            pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, advertised_asin=val['asin'])
            brand_obj = AdsBrand.objects.filter(user_id__in=users, asin=val['asin'])
            if brand_obj:
                val['sku'] = brand_obj[0].sku
                val['brand'] = brand_obj[0].brand
            else:
                val['sku'] = ''
                val['brand'] = ''
            if adv_obj:
                if sum_by_date == 'on':
                    last_adv_obj = _get_spend(adv_obj, range_type, start_last_year, last_year, end_month_str=last_month,
                                              month_str=start_last_month, week_str=start_last_week,
                                              end_week_str=end_last_week)
                    adv_obj = _get_spend(adv_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                else:
                    last_adv_obj = adv_obj.filter(year_str=sum_off_year, month=sum_off_month, week=sum_off_week)
                    adv_obj = adv_obj.filter(year_str=val['year_str'], month=val['month'], week=val['week'])
                if adv_obj:
                    adv_obj = adv_obj.aggregate(self_sales=Sum('day_advertised_sku_sales'),
                                                self_units=Sum('day_advertised_sku_units'), sp_spend=Sum('spend'),
                                                impressions_sum=Sum('impressions'), clicks_sum=Sum('clicks'))
                    impressions_sum = adv_obj['impressions_sum']
                    clicks_sum = adv_obj['clicks_sum']
                    sp_spend = adv_obj['sp_spend']
                    self_units = adv_obj['self_units']
                    self_sales = adv_obj['sp_spend']
                    if impressions_sum == 0:
                        ctr = 0
                    else:
                        ctr = clicks_sum / impressions_sum * 100
                    if clicks_sum == 0:
                        cr = 0
                    else:
                        cr = self_units / clicks_sum * 100
                    if search_key == 'CTR' and ctr >= float(listKwd):
                        biz_obj.remove(val)
                        continue
                    if search_key == 'CR' and cr >= float(listKwd):
                        biz_obj.remove(val)
                        continue

                    if last_adv_obj:
                        adv_obj = adv_obj.aggregate(hb_self_units=Sum('day_advertised_sku_units'),
                                                    hb_impressions_sum=Sum('impressions'),
                                                    hb_clicks_sum=Sum('clicks'))
                        hb_impressions_sum = adv_obj['hb_impressions_sum']
                        hb_clicks_sum = adv_obj['hb_clicks_sum']
                        hb_self_units = adv_obj['hb_self_units']
                        if hb_impressions_sum == 0:
                            hb_ctr = 0
                        else:
                            hb_ctr = hb_clicks_sum / hb_impressions_sum * 100
                        if hb_clicks_sum == 0:
                            hb_cr = 0
                        else:
                            hb_cr = hb_self_units / hb_clicks_sum * 100
                        val['hb_ctr'] = (ctr - hb_ctr) / hb_ctr * 100
                        val['hb_ctr'] = '%.2f' % val['hb_ctr']
                        val['hb_cr'] = (cr - hb_cr) / hb_cr * 100
                        val['hb_cr'] = '%.2f' % val['hb_cr']

                    val['ctr'] = '%.2f' % ctr
                    val['cr'] = '%.2f' % cr
                    val['impressions_sum'] = impressions_sum
                    val['clicks_sum'] = clicks_sum
                    val['sp_spend'] = sp_spend
                    val['self_units'] = self_units
                    val['self_sales'] = self_sales
                    if val['all_sales'] == 0:
                        val['all_spend_sales'] = 0
                    else:
                        val['all_spend_sales'] = sp_spend / val['all_sales'] * 100
                        val['all_spend_sales'] = '%.2f' % val['all_spend_sales']
            if pur_obj:
                if sum_by_date == 'on':
                    pur_obj = _get_spend(pur_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                else:
                    pur_obj = pur_obj.filter(year_str=val['year_str'], month=val['month'], week=val['week'])
                if pur_obj:
                    pur_obj = pur_obj.aggregate(other_units=Sum('day_other_sku_units'),
                                                other_sales=Sum('day_other_sku_sales'))
                    other_units = pur_obj['other_units']
                    other_sales = pur_obj['other_sales']
                    sp_sales = other_sales + self_sales
                    val['other_units'] = other_units
                    val['other_sales'] = other_sales
                    val['sp_sales'] = '%.2f' % sp_sales
                    if val['all_sales'] == 0:
                        val['sp_sales_sales'] = 0
                    else:
                        val['sp_sales_sales'] = sp_sales / val['all_sales'] * 100
                        val['sp_sales_sales'] = '%.2f' % val['sp_sales_sales']
                    if other_sales > self_sales:
                        val['other_self'] = 'Y'
                    else:
                        if other_self == 'on':
                            biz_obj.remove(val)
                            continue
                        val['other_self'] = 'N'
            data.append([
                val['account'],
                val['date_range'],
                val['asin'],
                val['sku'],
                val['brand'],
                val['impressions_sum'],
                val['clicks_sum'],
                val['ctr'],
                val['sp_spend'],
                val['self_units'],
                val['self_sales'],
                val['cr'],
                val['other_units'],
                val['other_sales'],
                val['sp_sales'],
                val['all_sales'],
                val['all_spend_sales'],
                val['sp_sales_sales'],
                val['other_self'],
                val['hb_cr'],
                val['hb_ctr'],
            ])
    response = HttpResponse(content_type='text/csv')  # 设置头信息，告诉浏览器这是个文件
    response.write(codecs.BOM_UTF8)
    response['Content-Disposition'] = 'attachment;filename="%s"' % file_name
    writer = csv.writer(response)
    # 先写入columns_name
    writer.writerow(fields)
    writer.writerows(data)
    return response