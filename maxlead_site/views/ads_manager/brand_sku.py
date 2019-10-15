# -*- coding: utf-8 -*-
import json
import datetime,csv,codecs
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

def _get_spend(spend_obj, range_type, year_str, end_year_str, month_str=None, end_month_str=None, week_str=None, end_week_str=None):
    if range_type == 'Monthly':
        res = spend_obj.filter(year_str__gte=year_str, year_str__lte=end_year_str, month__gte=month_str,
                                   month__lte=end_month_str)
    else:
        res = spend_obj.filter(year_str__gte=year_str, year_str__lte=end_year_str, week__gte=week_str,
                                       week__lte=end_week_str)
    return res

def brand_sku(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    searchCol = request.GET.get('searchCol', 'brand')
    account = request.GET.get('account', '1')
    range_type = request.GET.get('range_type', 'Weekly')
    sum_by_date = request.GET.get('sum_by_date', '')
    search_key = request.GET.get('search_key', 'all')
    listKwd = request.GET.get('listKwd', '')
    week = request.GET.get('week', '')
    end_week = request.GET.get('end_week', '')
    month = request.GET.get('month', '')
    end_month = request.GET.get('end_month', '')
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

    if searchCol == 'brand':
        if sum_by_date  == 'on':
            ads_brand = AdsBrand.objects.filter(user_id__in=users).values("brand").distinct().exclude(brand='')
            if brand:
                brands = AdsBrand.objects.values('sku').filter(user_id__in=users, brand=brand)
                ads_brand = ads_brand.filter(advertised_sku__in=brands)
        else:
            ads_brand = AdvProducts.objects.values("year_str", "month", "week", "advertised_sku").annotate(sp_spend=Sum('spend'),
                                            self_units=Sum('day_advertised_sku_units'), self_sales=Sum('day_advertised_sku_sales')).\
                                            filter(user_id__in=users, account=account).exclude(advertised_sku='')
            if brand:
                brands = AdsBrand.objects.values('sku').filter(user_id__in=users, brand=brand)
                ads_brand = ads_brand.filter(advertised_sku__in=brands)

    else:
        if sum_by_date == 'on':
            ads_brand = AdvProducts.objects.filter(user_id__in=users, account=account).values("advertised_sku").distinct().exclude(advertised_sku='')
            ads_brand = _get_spend(ads_brand, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                 month_str=month_str, week_str=week_str, end_week_str=end_week_str)
        else:
            ads_brand = AdvProducts.objects.values("year_str", "month", "week", "advertised_sku").annotate(test_sum=Sum('day_advertised_sku_sales')).filter(user_id__in=users, account=account).exclude(advertised_sku='')

        if brand:
            brands = AdsBrand.objects.values('sku').filter(user_id__in=users, brand=brand)
            ads_brand = ads_brand.filter(advertised_sku__in=brands)
    if searchCol == 'SKU':
        fields = [
            ('account', 'Account'),
            ('date_range', 'Date Range'),
            ('sku', 'SKU'),
            ('asin', 'ASIN'),
            ('brand', 'Brand'),
            ('sp_spend', 'SP Spend'),
            ('self_units', 'Self Units'),
            ('self_sales', 'Self Sales'),
            ('other_units', 'Other Units'),
            ('other_sales', 'Other Sales'),
            ('sp_sales', 'SP Sales'),
            ('all_sales', 'All Sales'),
            ('spend_sales', 'All Spend/All Sales'),
            ('sp_all_sales', 'SP Sales/All Sales')
        ]
        if search_key == 'SKU':
            ads_brand = ads_brand.filter(advertised_sku=listKwd)
        if search_key == 'ASIN':
            adv_brand_obj = AdsBrand.objects.filter(user_id__in=users, asin=listKwd).values('sku')
            ads_brand = ads_brand.filter(advertised_sku__in=adv_brand_obj)
    else:
        fields = [
            ('account', 'Account'),
            ('date_range', 'Date Range'),
            ('brand', 'Brand'),
            ('sp_spend', 'SP Spend'),
            ('sb_spend', 'SB Spend'),
            ('all_spend', 'All Spend'),
            ('self_units', 'Self Units'),
            ('self_sales', 'Self Sales'),
            ('other_units', 'Other Units'),
            ('other_sales', 'Other Sales'),
            ('sp_sales', 'SP Sales'),
            ('sb_sales', 'SB Sales'),
            ('all_ads_sales', 'All Ads Sales'),
            ('all_sales', 'All Sales'),
            ('spend_sales', 'All Spend/All Sales'),
            ('ads_sales_sales', 'All Ads Sales/All Sales')
        ]

    limit = request.GET.get('limit', 20)
    page = request.GET.get('page', 1)
    re_limit = limit

    total_count = len(ads_brand)
    total_page = round(len(ads_brand) / int(limit))
    if int(limit) >= total_count:
        limit = total_count
    if ads_brand:
        data_li = []
        range_type_str = ''
        if start_month and range_type == 'Monthly':
            range_type_str = "%s-%s" % (start_month, end_month_month)
        if start_week and range_type == 'Weekly':
            range_type_str = "%s-%s" % (start_week, end_week_week)
        for val in ads_brand:
            sb_spend = 0
            sp_spend = 0
            self_sales = 0
            other_sales = 0
            sb_sales = 0
            all_sales = 0
            self_units = 0
            other_units = 0
            if searchCol == 'brand':
                if sum_by_date == 'on':
                    brand_str = val['brand']
                    campaign_list = AdsCampaign.objects.values('campaign').filter(user_id__in=users, account=account,
                                                                                  brand=val['brand'])
                    sku_list = AdsBrand.objects.values('sku').filter(user_id__in=users, brand=val['brand'])
                    asin_list = AdsBrand.objects.values('asin').filter(user_id__in=users, brand=val['brand'])
                    if campaign_list:
                        pla_obj = CampaignPla.objects.filter(user_id__in=users, account=account, campaign_name__in=campaign_list)
                        pla_obj = _get_spend(pla_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                                 month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                        if pla_obj:
                            pla_obj = pla_obj.aggregate(sb_spend=Sum('spend'), sb_sales=Sum('day_total_sales'))
                            sb_spend = pla_obj['sb_spend']
                            sb_sales = pla_obj['sb_sales']
                    if sku_list:
                        adv_obj = AdvProducts.objects.filter(user_id__in=users, account=account, advertised_sku__in=sku_list)
                        pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, advertised_sku__in=sku_list)
                        biz_obj = BizReport.objects.filter(user_id__in=users, account=account, asin__in=asin_list)
                        adv_obj = _get_spend(adv_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                                 month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                        if adv_obj:
                            adv_obj = adv_obj.aggregate(sp_spend=Sum('spend'), self_units=Sum('day_advertised_sku_units'),
                                                        self_sales=Sum('day_advertised_sku_sales'))
                            sp_spend = adv_obj['sp_spend']
                            self_units = adv_obj['self_units']
                            self_sales = adv_obj['self_sales']

                        pur_obj = _get_spend(pur_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                                 month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                        if pur_obj:
                            pur_obj = pur_obj.aggregate(other_units=Sum('day_other_sku_units'), other_sales=Sum('day_other_sku_sales'))
                            other_units = pur_obj['other_units']
                            other_sales = pur_obj['other_sales']

                        biz_obj = _get_spend(biz_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                                 month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                        if biz_obj:
                            biz_obj = biz_obj.aggregate(all_sales=Sum('ordered_product_sales'))
                            all_sales = biz_obj['all_sales']
                    all_spend = sp_spend + sb_spend
                    sp_sales = self_sales + other_sales
                    all_ads_sales = sp_sales + sb_sales
                else:
                    brand_str = ''
                    if val['month']:
                        if val['month'] < 10:
                            range_type_str = "%s0%s" % (val['year_str'], val['month'])
                        else:
                            range_type_str = "%s%s" % (val['year_str'], val['month'])
                    if val['week']:
                        week_obj = '%s-%s-0' % (val['year_str'], val['week'])
                        start_week = datetime.datetime.strptime(week_obj, '%Y-%U-%w')
                        start_week_str = start_week + datetime.timedelta(days=-6)
                        range_type_str = "%s-%s" % (start_week_str.strftime("%Y%m%d"), start_week.strftime("%Y%m%d"))
                    sp_spend = val['sp_spend']
                    self_units = val['self_units']
                    self_sales = val['self_sales']
                    brand_adv_obj = AdsBrand.objects.filter(user_id__in=users, sku=val['advertised_sku'])
                    if brand_adv_obj:
                        brand_str = brand_adv_obj[0].brand
                        if brand_str:
                            campaign_list = AdsCampaign.objects.values('campaign').filter(user_id__in=users, account=account,
                                                                                          brand=brand_str)
                            if campaign_list:
                                pla_obj = CampaignPla.objects.filter(user_id__in=users, account=account, campaign_name__in=campaign_list)
                                if pla_obj:
                                    pla_obj = pla_obj.aggregate(sb_spend=Sum('spend'), sb_sales=Sum('day_total_sales'))
                                    sb_spend = pla_obj['sb_spend']
                                    sb_sales = pla_obj['sb_sales']
                    pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, advertised_sku=val['advertised_sku'])
                    asin_list = AdsBrand.objects.values('asin').filter(user_id__in=users, sku=val['advertised_sku'])
                    if asin_list:
                        biz_obj = BizReport.objects.filter(user_id__in=users, account=account, asin__in=asin_list)
                        if biz_obj:
                            biz_obj = biz_obj.aggregate(all_sales=Sum('ordered_product_sales'))
                            all_sales = biz_obj['all_sales']
                    if pur_obj:
                        pur_obj = pur_obj.aggregate(other_units=Sum('day_other_sku_units'),
                                                    other_sales=Sum('day_other_sku_sales'))
                        other_units = pur_obj['other_units']
                        other_sales = pur_obj['other_sales']
                    all_spend = sp_spend + sb_spend
                    sp_sales = self_sales + other_sales
                    all_ads_sales = sp_sales + sb_sales
                if not all_sales == 0:
                    spend_sales = all_spend / all_sales * 100
                    spend_sales = '%.2f' % spend_sales
                    ads_sales_sales = all_ads_sales / all_sales * 100
                    ads_sales_sales = '%.2f' % ads_sales_sales
                else:
                    spend_sales = 0
                    ads_sales_sales = 0

                data_li.append({
                    'account' : account_li[int(account)],
                    'date_range' : range_type_str,
                    'brand' : brand_str,
                    'sb_spend' : sb_spend,
                    'all_spend' : '%.2f' % all_spend,
                    'sp_spend' : sp_spend,
                    'self_sales' : self_sales,
                    'other_sales' : '%.2f' % other_sales,
                    'sb_sales' : sb_sales,
                    'sp_sales' : '%.2f' % sp_sales,
                    'all_sales' : all_sales,
                    'self_units' : self_units,
                    'other_units' : other_units,
                    'spend_sales' : spend_sales,
                    'all_ads_sales' : '%.2f' % all_ads_sales,
                    'ads_sales_sales' : ads_sales_sales
                })
            else:
                pla_obj = False
                campaign_list = False
                brand_str = ''
                asin_str = ''
                brand_obj = AdsBrand.objects.filter(user_id__in=users, sku=val['advertised_sku'])
                if brand_obj:
                    brand_str = brand_obj[0].brand
                    asin_str = brand_obj[0].asin
                    if brand_str:
                        campaign_list = AdsCampaign.objects.values('campaign').filter(user_id__in=users, account=account,
                                                                              brand=brand_str)
                        if campaign_list:
                            pla_obj = CampaignPla.objects.filter(user_id__in=users, account=account, campaign_name__in=campaign_list)
                if sum_by_date == 'on':
                    if pla_obj:
                        pla_obj = _get_spend(pla_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                         month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                    adv_obj = AdvProducts.objects.filter(user_id__in=users, account=account, advertised_sku=val['advertised_sku'])
                    pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, advertised_sku=val['advertised_sku'])
                    biz_obj = BizReport.objects.filter(user_id__in=users, account=account, asin=asin_str)
                    adv_obj = _get_spend(adv_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                         month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                    pur_obj = _get_spend(pur_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                         month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                    biz_obj = _get_spend(biz_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                         month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                else:
                    if val['month']:
                        if val['month'] < 10:
                            range_type_str = "%s0%s" % (val['year_str'], val['month'])
                        else:
                            range_type_str = "%s%s" % (val['year_str'], val['month'])
                    if val['week']:
                        week_obj = '%s-%s-0' % (val['year_str'], val['week'])
                        start_week = datetime.datetime.strptime(week_obj, '%Y-%U-%w')
                        start_week_str = start_week + datetime.timedelta(days=-6)
                        range_type_str = "%s-%s" % (start_week_str.strftime("%Y%m%d"), start_week.strftime("%Y%m%d"))
                    if campaign_list:
                        pla_obj = CampaignPla.objects.filter(user_id__in=users, account=account, year_str=val['year_str'],
                                                         month=val['month'], week=val['week'], campaign_name__in=campaign_list)

                    adv_obj = AdvProducts.objects.filter(user_id__in=users, account=account, year_str=val['year_str'],
                                                         month=val['month'], week=val['week'], advertised_sku=val['advertised_sku'])
                    pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, year_str=val['year_str'],
                                                        month=val['month'], week=val['week'], advertised_sku=val['advertised_sku'])
                    asin_biz_list = AdsBrand.objects.filter(user_id__in=users, sku=val['advertised_sku']).values('asin')
                    biz_obj = BizReport.objects.filter(user_id__in=users, account=account, asin__in=asin_biz_list)
                if pla_obj:
                    pla_obj = pla_obj.aggregate(sb_spend=Sum('spend'), sb_sales=Sum('day_total_sales'))
                    sb_spend = pla_obj['sb_spend']
                    sb_sales = pla_obj['sb_sales']
                if biz_obj:
                    biz_obj = biz_obj.aggregate(all_sales=Sum('ordered_product_sales'))
                    all_sales = biz_obj['all_sales']
                if pur_obj:
                    pur_obj = pur_obj.aggregate(other_units=Sum('day_other_sku_units'),
                                                other_sales=Sum('day_other_sku_sales'))
                    other_units = pur_obj['other_units']
                    other_sales = pur_obj['other_sales']
                if adv_obj:
                    adv_obj = adv_obj.aggregate(sp_spend=Sum('spend'), self_units=Sum('day_advertised_sku_units'),
                                                self_sales=Sum('day_advertised_sku_sales'))
                    sp_spend = adv_obj['sp_spend']
                    self_units = adv_obj['self_units']
                    self_sales = adv_obj['self_sales']

                sp_sales = self_sales + other_sales
                all_spend = sp_spend + sb_spend
                all_ads_sales = sp_sales + sb_sales
                if not all_sales == 0:
                    spend_sales = all_spend / all_sales * 100
                    spend_sales = '%.2f' % spend_sales
                    ads_sales_sales = all_ads_sales / all_sales * 100
                    ads_sales_sales = '%.2f' % ads_sales_sales
                else:
                    spend_sales = 0
                    ads_sales_sales = 0
                data_li.append({
                    'account': account_li[int(account)],
                    'date_range': range_type_str,
                    'sku': val['advertised_sku'],
                    'brand': brand_str,
                    'asin': asin_str,
                    'sp_spend': sp_spend,
                    'self_sales': self_sales,
                    'other_sales': '%.2f' % other_sales,
                    'sp_sales': '%.2f' % sp_sales,
                    'all_sales': all_sales,
                    'self_units': self_units,
                    'other_units': other_units,
                    'spend_sales': spend_sales,
                    'sp_all_sales': ads_sales_sales
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
            'searchCol': searchCol,
            'account': account,
            'range_type': range_type,
            'sum_by_date': sum_by_date,
            'search_key': search_key,
            'listKwd': listKwd,
            'week': week,
            'end_week': end_week,
            'month': month,
            'end_month': end_month,
            'brand_list': brand_list,
            'brand': brand,
            'ordder_field': ordder_field,
            'order_desc': order_desc,
            'avator': user.user.username[0]
        }
    else:
        data = {
            'data': '',
            'fields': fields,
            'total_count': total_count,
            'total_page': total_page,
            're_limit': int(re_limit),
            'limit': int(limit),
            'page': page,
            'user': user,
            'brand_list': brand_list,
            'searchCol': searchCol,
            'account': account,
            'range_type': range_type,
            'sum_by_date': sum_by_date,
            'search_key': search_key,
            'listKwd': listKwd,
            'week': week,
            'end_week': end_week,
            'month': month,
            'end_month': end_month,
            'brand': brand,
            'avator': user.user.username[0]
        }
    return render(request, 'ads_manager/brand_sku.html', data)

@csrf_exempt
def export_brand_sku(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    searchCol = request.GET.get('searchCol', 'brand')
    account = request.GET.get('account', '1')
    range_type = request.GET.get('range_type', 'Weekly')
    sum_by_date = request.GET.get('sum_by_date', '')
    search_key = request.GET.get('search_key', '')
    listKwd = request.GET.get('listKwd', '')
    week = request.GET.get('week', '')
    end_week = request.GET.get('end_week', '')
    month = request.GET.get('month', '')
    end_month = request.GET.get('end_month', '')

    month_str = None
    end_month_str = None
    week_str = None
    end_week_str = None
    start_month = None
    end_month_month = None
    start_week = None
    end_week_week = None
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

    user_group = user.group
    users = []
    user_list = UserProfile.objects.filter(state=1)
    if not user.user.is_superuser and not user_group.user.username == 'Ads':
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
    if user_list:
        for val in user_list:
            users.append(val.user_id)

    if searchCol == 'brand':
        if sum_by_date  == 'on':
            ads_brand = AdsBrand.objects.filter(user_id__in=users).values("brand").distinct().exclude(brand='')
        else:
            ads_brand = AdvProducts.objects.values("year_str", "month", "week", "advertised_sku").annotate(sp_spend=Sum('spend'),
                                            self_units=Sum('day_advertised_sku_units'), self_sales=Sum('day_advertised_sku_sales')).\
                                            filter(user_id__in=users, account=account).exclude(advertised_sku='')

    else:
        if sum_by_date == 'on':
            ads_brand = AdvProducts.objects.filter(user_id__in=users, account=account).values("advertised_sku").distinct().exclude(advertised_sku='')
            ads_brand = _get_spend(ads_brand, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                 month_str=month_str, week_str=week_str, end_week_str=end_week_str)
        else:
            ads_brand = AdvProducts.objects.values("year_str", "month", "week", "advertised_sku").annotate(test_sum=Sum('day_advertised_sku_sales')).filter(user_id__in=users, account=account).exclude(advertised_sku='')

    if searchCol == 'SKU':
        fields = [
            'Account',
            'Date Range',
            'SKU',
            'ASIN',
            'Brand',
            'SP Spend',
            'Self Units',
            'Self Sales',
            'Other Units',
            'Other Sales',
            'SP Sales',
            'All Sales',
            'All Spend/All Sales',
            'SP Sales/All Sales'
        ]
        if search_key == 'SKU':
            ads_brand = ads_brand.filter(advertised_sku=listKwd)
        if search_key == 'ASIN':
            adv_brand_obj = AdsBrand.objects.filter(user_id__in=users, asin=listKwd).values('sku')
            ads_brand = ads_brand.filter(advertised_sku__in=adv_brand_obj)
    else:
        fields = [
            'Account',
            'Date Range',
            'Brand',
            'SP Spend',
            'SB Spend',
            'All Spend',
            'Self Units',
            'Self Sales',
            'Other Units',
            'Other Sales',
            'SP Sales',
            'SB Sales',
            'All Ads Sales',
            'All Sales',
            'All Spend/All Sales',
            'All Ads Sales/All Sales'
        ]

    if not ads_brand:
        return HttpResponse(json.dumps({'code': 0, 'msg': u'数据不存在!'}), content_type='application/json')
    file_name = 'brand_SKU-%s.csv' % datetime.datetime.now().strftime('%Y-%m-%d')
    data_li = []
    range_type_str = ''
    if start_month and range_type == 'Monthly':
        range_type_str = "%s-%s" % (start_month, end_month_month)
    if start_week and range_type == 'Weekly':
        range_type_str = "%s-%s" % (start_week, end_week_week)
    for val in ads_brand:
        sb_spend = 0
        sp_spend = 0
        self_sales = 0
        other_sales = 0
        sb_sales = 0
        all_sales = 0
        self_units = 0
        other_units = 0
        if searchCol == 'brand':
            if sum_by_date == 'on':
                brand_str = val['brand']
                campaign_list = AdsCampaign.objects.values('campaign').filter(user_id__in=users, account=account,
                                                                              brand=val['brand'])
                sku_list = AdsBrand.objects.values('sku').filter(user_id__in=users, brand=val['brand'])
                asin_list = AdsBrand.objects.values('asin').filter(user_id__in=users, brand=val['brand'])
                if campaign_list:
                    pla_obj = CampaignPla.objects.filter(user_id__in=users, account=account, campaign_name__in=campaign_list)
                    pla_obj = _get_spend(pla_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                             month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                    if pla_obj:
                        pla_obj = pla_obj.aggregate(sb_spend=Sum('spend'), sb_sales=Sum('day_total_sales'))
                        sb_spend = pla_obj['sb_spend']
                        sb_sales = pla_obj['sb_sales']
                if sku_list:
                    adv_obj = AdvProducts.objects.filter(user_id__in=users, account=account, advertised_sku__in=sku_list)
                    pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, advertised_sku__in=sku_list)
                    biz_obj = BizReport.objects.filter(user_id__in=users, account=account, asin__in=asin_list)
                    adv_obj = _get_spend(adv_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                             month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                    if adv_obj:
                        adv_obj = adv_obj.aggregate(sp_spend=Sum('spend'), self_units=Sum('day_advertised_sku_units'),
                                                    self_sales=Sum('day_advertised_sku_sales'))
                        sp_spend = adv_obj['sp_spend']
                        self_units = adv_obj['self_units']
                        self_sales = adv_obj['self_sales']

                    pur_obj = _get_spend(pur_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                             month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                    if pur_obj:
                        pur_obj = pur_obj.aggregate(other_units=Sum('day_other_sku_units'), other_sales=Sum('day_other_sku_sales'))
                        other_units = pur_obj['other_units']
                        other_sales = pur_obj['other_sales']

                    biz_obj = _get_spend(biz_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                             month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                    if biz_obj:
                        biz_obj = biz_obj.aggregate(all_sales=Sum('ordered_product_sales'))
                        all_sales = biz_obj['all_sales']
                all_spend = sp_spend + sb_spend
                sp_sales = self_sales + other_sales
                all_ads_sales = sp_sales + sb_sales
            else:
                brand_str = ''
                if val['month']:
                    if val['month'] < 10:
                        range_type_str = "%s0%s" % (val['year_str'], val['month'])
                    else:
                        range_type_str = "%s%s" % (val['year_str'], val['month'])
                if val['week']:
                    week_obj = '%s-%s-0' % (val['year_str'], val['week'])
                    start_week = datetime.datetime.strptime(week_obj, '%Y-%U-%w')
                    start_week_str = start_week + datetime.timedelta(days=-6)
                    range_type_str = "%s-%s" % (start_week_str.strftime("%Y%m%d"), start_week.strftime("%Y%m%d"))
                sp_spend = val['sp_spend']
                self_units = val['self_units']
                self_sales = val['self_sales']
                brand_adv_obj = AdsBrand.objects.filter(user_id__in=users, sku=val['advertised_sku'])
                if brand_adv_obj:
                    brand_str = brand_adv_obj[0].brand
                    if brand_str:
                        campaign_list = AdsCampaign.objects.values('campaign').filter(user_id__in=users, account=account,
                                                                                      brand=brand_str)
                        if campaign_list:
                            pla_obj = CampaignPla.objects.filter(user_id__in=users, account=account, campaign_name__in=campaign_list)
                            if pla_obj:
                                pla_obj = pla_obj.aggregate(sb_spend=Sum('spend'), sb_sales=Sum('day_total_sales'))
                                sb_spend = pla_obj['sb_spend']
                                sb_sales = pla_obj['sb_sales']
                pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, advertised_sku=val['advertised_sku'])
                asin_list = AdsBrand.objects.values('asin').filter(user_id__in=users, sku=val['advertised_sku'])
                if asin_list:
                    biz_obj = BizReport.objects.filter(user_id__in=users, account=account, asin__in=asin_list)
                    if biz_obj:
                        biz_obj = biz_obj.aggregate(all_sales=Sum('ordered_product_sales'))
                        all_sales = biz_obj['all_sales']
                if pur_obj:
                    pur_obj = pur_obj.aggregate(other_units=Sum('day_other_sku_units'),
                                                other_sales=Sum('day_other_sku_sales'))
                    other_units = pur_obj['other_units']
                    other_sales = pur_obj['other_sales']
                all_spend = sp_spend + sb_spend
                sp_sales = self_sales + other_sales
                all_ads_sales = sp_sales + sb_sales
            if not all_sales == 0:
                spend_sales = all_spend / all_sales * 100
                spend_sales = '%.2f' % spend_sales
                ads_sales_sales = all_ads_sales / all_sales * 100
                ads_sales_sales = '%.2f' % ads_sales_sales
            else:
                spend_sales = 0
                ads_sales_sales = 0

            data_li.append([
                account_li[int(account)],
                range_type_str,
                brand_str,
                sp_spend,
                sb_spend,
                '%.2f' % all_spend,
                self_units,
                self_sales,
                other_units,
                '%.2f' % other_sales,
                '%.2f' % sp_sales,
                sb_sales,
                '%.2f' % all_ads_sales,
                all_sales,
                spend_sales,
                ads_sales_sales
            ])
        else:
            pla_obj = False
            campaign_list = False
            brand_str = ''
            asin_str = ''
            brand_obj = AdsBrand.objects.filter(user_id__in=users, sku=val['advertised_sku'])
            if brand_obj:
                brand_str = brand_obj[0].brand
                asin_str = brand_obj[0].asin
                if brand_str:
                    campaign_list = AdsCampaign.objects.values('campaign').filter(user_id__in=users, account=account,
                                                                          brand=brand_str)
                    if campaign_list:
                        pla_obj = CampaignPla.objects.filter(user_id__in=users, account=account, campaign_name__in=campaign_list)
            if sum_by_date == 'on':
                if pla_obj:
                    pla_obj = _get_spend(pla_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                adv_obj = AdvProducts.objects.filter(user_id__in=users, account=account, advertised_sku=val['advertised_sku'])
                pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, advertised_sku=val['advertised_sku'])
                biz_obj = BizReport.objects.filter(user_id__in=users, account=account, asin=asin_str)
                adv_obj = _get_spend(adv_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                pur_obj = _get_spend(pur_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
                biz_obj = _get_spend(biz_obj, range_type, year_str, end_year_str, end_month_str=end_month_str,
                                     month_str=month_str, week_str=week_str, end_week_str=end_week_str)
            else:
                if val['month']:
                    if val['month'] < 10:
                        range_type_str = "%s0%s" % (val['year_str'], val['month'])
                    else:
                        range_type_str = "%s%s" % (val['year_str'], val['month'])
                if val['week']:
                    week_obj = '%s-%s-0' % (val['year_str'], val['week'])
                    start_week = datetime.datetime.strptime(week_obj, '%Y-%U-%w')
                    start_week_str = start_week + datetime.timedelta(days=-6)
                    range_type_str = "%s-%s" % (start_week_str.strftime("%Y%m%d"), start_week.strftime("%Y%m%d"))
                if campaign_list:
                    pla_obj = CampaignPla.objects.filter(user_id__in=users, account=account, year_str=val['year_str'],
                                                     month=val['month'], week=val['week'], campaign_name__in=campaign_list)

                adv_obj = AdvProducts.objects.filter(user_id__in=users, account=account, year_str=val['year_str'],
                                                     month=val['month'], week=val['week'], advertised_sku=val['advertised_sku'])
                pur_obj = PurProduct.objects.filter(user_id__in=users, account=account, year_str=val['year_str'],
                                                    month=val['month'], week=val['week'], advertised_sku=val['advertised_sku'])
                asin_biz_list = AdsBrand.objects.filter(user_id__in=users, sku=val['advertised_sku']).values('asin')
                biz_obj = BizReport.objects.filter(user_id__in=users, account=account, asin__in=asin_biz_list)
            if pla_obj:
                pla_obj = pla_obj.aggregate(sb_spend=Sum('spend'), sb_sales=Sum('day_total_sales'))
                sb_spend = pla_obj['sb_spend']
                sb_sales = pla_obj['sb_sales']
            if biz_obj:
                biz_obj = biz_obj.aggregate(all_sales=Sum('ordered_product_sales'))
                all_sales = biz_obj['all_sales']
            if pur_obj:
                pur_obj = pur_obj.aggregate(other_units=Sum('day_other_sku_units'),
                                            other_sales=Sum('day_other_sku_sales'))
                other_units = pur_obj['other_units']
                other_sales = pur_obj['other_sales']
            if adv_obj:
                adv_obj = adv_obj.aggregate(sp_spend=Sum('spend'), self_units=Sum('day_advertised_sku_units'),
                                            self_sales=Sum('day_advertised_sku_sales'))
                sp_spend = adv_obj['sp_spend']
                self_units = adv_obj['self_units']
                self_sales = adv_obj['self_sales']

            sp_sales = self_sales + other_sales
            all_spend = sp_spend + sb_spend
            all_ads_sales = sp_sales + sb_sales
            if not all_sales == 0:
                spend_sales = all_spend / all_sales * 100
                spend_sales = '%.2f' % spend_sales
                ads_sales_sales = all_ads_sales / all_sales * 100
                ads_sales_sales = '%.2f' % ads_sales_sales
            else:
                spend_sales = 0
                ads_sales_sales = 0
            data_li.append([
                account_li[int(account)],
                range_type_str,
                val['advertised_sku'],
                asin_str,
                brand_str,
                sp_spend,
                self_units,
                self_sales,
                other_units,
                '%.2f' % other_sales,
                '%.2f' % sp_sales,
                all_sales,
                spend_sales,
                ads_sales_sales
            ])
    response = HttpResponse(content_type='text/csv')  # 设置头信息，告诉浏览器这是个文件
    response.write(codecs.BOM_UTF8)
    response['Content-Disposition'] = 'attachment;filename="%s"' % file_name
    writer = csv.writer(response)
    # 先写入columns_name
    writer.writerow(fields)
    writer.writerows(data_li)
    return response