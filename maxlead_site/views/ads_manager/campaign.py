# -*- coding: utf-8 -*-
import json,os
import datetime,csv,codecs
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from maxlead_site.views.app import App
from maxlead_site.models import AdsCampaign,AdsBrand
from maxlead_site.models import UserProfile
from django.views.decorators.csrf import csrf_exempt
from maxlead import settings
from maxlead_site.common.excel_world import handleEncoding

account_li = {
    1 : u'1账号',
    2 : u'子账号',
    3 : u'2账号',
    4 : u'3账号',
    5 : u'HZ账号',
    6 : u'UKDP'
}

type_li = {
    1 : 'Inventory',
    2 : 'Brand',
    3 : 'Business',
    4 : 'Search Term',
    5 : 'Placement',
    6 : 'Advertised',
    7 : 'Purchased',
    8 : 'SB Camp Pla',
    9 : 'SB Kwd Pla'
}

def campaign(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/maxlead_site/login/")

    viewRange = request.GET.get('viewRange', user.user.id)
    order_type = request.GET.get('order_type', '')
    order_dasc = request.GET.get('order_dasc', '')
    team_list = UserProfile.objects.filter(role=1,state=1).order_by('user__username','-id')
    if viewRange:
        viewRange = int(viewRange)
    user_group = user.group
    brand_list = []
    brand_list_obj = AdsBrand.objects.all().order_by('brand', '-id')
    ads_campaign = AdsCampaign.objects.all().order_by('-created', '-id')
    users = []
    user_list = []
    if not user.user.is_superuser and not user_group.user.username == 'Ads':
        user_list = UserProfile.objects.filter(state=1)
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
        if user_list:
            for val in user_list:
                users.append(val.user_id)
        brand_list_obj = brand_list_obj.filter(user_id__in=users)
        ads_campaign = ads_campaign.filter(user_id__in=users)

    if brand_list_obj:
        for val in brand_list_obj:
            if val.brand and not val.brand in brand_list:
                brand_list.append(val.brand)
    if viewRange:
        ads_campaign = ads_campaign.filter(user_id=viewRange)

    if ads_campaign:
        for v in ads_campaign:
            if v.team:
                team = User.objects.filter(id=v.team)
                v.team = team[0].username
            else:
                v.team = ''
            if not v.change_time:
                v.change_time = ''
            else:
                v.change_time = v.change_time.strftime('%Y-%m-%d %H:%M:%S')
            v.created = v.created.strftime('%Y-%m-%d %H:%M:%S')
            v.account = account_li[v.account]

    limit = request.GET.get('limit', 20)
    page = request.GET.get('page', 1)
    re_limit = limit

    total_count = len(ads_campaign)
    total_page = round(len(ads_campaign) / int(limit))
    if int(limit) >= total_count:
        limit = total_count
    if ads_campaign:
        paginator = Paginator(ads_campaign, limit)
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
            'total_count': total_count,
            'total_page': total_page,
            're_limit': int(re_limit),
            'limit': int(limit),
            'page': page,
            'user': user,
            'order_type': order_type,
            'order_dasc': order_dasc,
            'viewRange': viewRange,
            'avator': user.user.username[0],
            'team_list': team_list,
            'brand_list': brand_list,
            'user_list': user_list
        }
    else:
        data = {
            'data': '',
            'total_count': total_count,
            'total_page': total_page,
            're_limit': int(re_limit),
            'limit': int(limit),
            'page': page,
            'user': user,
            'viewRange': viewRange,
            'avator': user.user.username[0],
            'user_list': user_list
        }
    return render(request, 'ads_manager/campaign.html', data)

@csrf_exempt
def campaign_import(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        myfile = request.FILES.get('my_file','')
        if not myfile:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'File is empty!'}),content_type='application/json')
        file_path = os.path.join(settings.BASE_DIR, settings.DOWNLOAD_URL, 'excel_stocks', myfile.name)
        f = open(file_path, 'wb')
        for chunk in myfile.chunks():
            f.write(chunk)
        f.close()
        # handleEncoding(file_path)
        file = open(file_path, 'r', encoding='gb2312')
        csv_files = csv.reader(file)
        msg = 'Successfully!\n'
        for i, val in enumerate(csv_files, 0):
            try:
                if i == 0 and not val[0] == 'Account' and not val[1] == 'Campaign':
                    return HttpResponse(json.dumps({'code': 0, 'msg': u'文件错误~'}),
                                        content_type='application/json')
                if i > 0:
                    account = list (account_li.keys()) [list (account_li.values()).index (val[0])]
                    campaign_check = AdsCampaign.objects.filter(user=user.user, account=account, campaign=val[1])
                    team = User.objects.filter(username=val[2])
                    val[3] = val[3].upper()
                    brand_check = AdsBrand.objects.filter(user=user.user, brand=val[3])
                    if not brand_check:
                        msg += '第%s行,Brand不存在。\n' % (i + 1)
                        continue
                    if val[2] and not team:
                        msg += '第%s行,Team不存在。\n' % (i + 1)
                        continue
                    if campaign_check:
                        campaign_check.update(brand=val[3])
                        if val[2]:
                            campaign_check.update(team=team[0].id)
                    else:
                        brand_obj = AdsCampaign()
                        brand_obj.id
                        brand_obj.user = user.user
                        if val[2]:
                            brand_obj.team = team[0].id
                        brand_obj.campaign = val[1]
                        brand_obj.account = account
                        brand_obj.brand = val[3]
                        brand_obj.save()
            except:
                msg += '第%s行添加有误。\n' % (i + 1)
                continue
        file.close()
        res = {'code': 1, 'msg': msg}
        os.remove(file_path)
    return HttpResponse(json.dumps(res), content_type='application/json')

@csrf_exempt
def export_campaign(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    campaign_data = AdsCampaign.objects.all()
    user_group = user.group
    users = []
    if not user.user.is_superuser and not user_group.user.username == 'Ads':
        user_list = UserProfile.objects.filter(state=1)
        user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
        if user_list:
            for val in user_list:
                users.append(val.user_id)
        campaign_data = campaign_data.filter(user_id__in=users)

    if not campaign_data:
        return HttpResponse(json.dumps({'code': 0, 'msg': u'数据不存在!'}), content_type='application/json')
    file_name = 'campaign_%s.csv' % datetime.datetime.now().strftime('%Y-%m-%d')
    data = []
    for val in campaign_data:
        if val.team:
            team = User.objects.filter(id=val.team)
            team = team[0].username
        else:
            team = ''
        data.append([
            account_li[val.account],
            val.campaign,
            team,
            val.brand
        ])

    response = HttpResponse(content_type='text/csv')  # 设置头信息，告诉浏览器这是个文件
    response.write(codecs.BOM_UTF8)
    response['Content-Disposition'] = 'attachment;filename="%s"' % file_name
    writer = csv.writer(response)
    # 先写入columns_name
    writer.writerow(["Account", "Campaign", "Team", "Brand"])
    writer.writerows(data)
    return response

@csrf_exempt
def get_brand(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'GET':
        brand = request.GET.get('brand','')
        user_list = UserProfile.objects.filter(state=1)
        if user.role == 0:
            user_list = user_list.filter(id=user.id)
        if user.role == 1:
            user_list = user_list.filter(Q(group=user) | Q(id=user.id))
        users = []
        if user_list:
            for val in user_list:
                users.append(val.user_id)
        brand_list = []
        brand_list_obj = AdsBrand.objects.filter(user_id__in=users, brand__contains=brand).order_by('brand', '-id')
        if brand_list_obj:
            for val in brand_list_obj:
                if val.brand and not val.brand in brand_list:
                    brand_list.append(val.brand)
        return HttpResponse(json.dumps({'code': 1, 'data': brand_list}), content_type='application/json')

@csrf_exempt
def get_team(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'GET':
        team = request.GET.get('team','')
        team_list = UserProfile.objects.filter(user__username__contains=team).order_by('user__username', '-id')
        team_data = []
        for val in team_list:
            team_data.append(val.user.username)
        return HttpResponse(json.dumps({'code': 1, 'data': team_data}), content_type='application/json')

@csrf_exempt
def save_campaign(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'POST':
        id = request.POST.get('id','')
        team = request.POST.get('team','')
        brand = request.POST.get('brand','')
        campaign_obj = AdsCampaign.objects.filter(id=id)
        if not campaign_obj:
            return HttpResponse(json.dumps({'code': 0, 'msg': u'数据不存在！'}), content_type='application/json')
        team_obj = User.objects.filter(username=team)
        campaign_obj.update(brand=brand)
        if team_obj:
            campaign_obj.update(team = team_obj[0].id)
        return HttpResponse(json.dumps({'code': 1, 'msg': u'Successfully!'}), content_type='application/json')

@csrf_exempt
def get_campaign(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponse(json.dumps({'code': 66, 'msg': u'login error！'}), content_type='application/json')

    if request.method == 'GET':
        campaign = request.GET.get('campaign', '')
        campaign_list = []
        campaign_list_obj = AdsCampaign.objects.filter(campaign__contains=campaign).order_by('campaign', '-id')
        user_group = user.group
        users = []
        if not user.user.is_superuser and not user_group.user.username == 'Ads':
            user_list = UserProfile.objects.filter(state=1)
            user_list = user_list.filter(Q(group=user_group) | Q(id=user.id))
            if user_list:
                for val in user_list:
                    users.append(val.user_id)
            campaign_list_obj = campaign_list_obj.filter(user_id__in=users)
        if campaign_list_obj:
            for val in campaign_list_obj:
                if val.campaign and not val.campaign in campaign_list:
                    campaign_list.append(val.campaign)
        return HttpResponse(json.dumps({'code': 1, 'data': campaign_list}), content_type='application/json')
