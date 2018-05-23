# -*- coding: utf-8 -*-
import time,json
from django.contrib import auth
from django.shortcuts import render,HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from maxlead_site.models import UserProfile
from maxlead_site.views import commons
from maxlead_site.views.app import App

@csrf_exempt
def index(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    return render(request,"Stocks/stocks/index.html")

@csrf_exempt
def threshold(request):
    user = App.get_user_info(request)
    if not user:
        return HttpResponseRedirect("/admin/max_stock/login/")
    return render(request,"Stocks/stocks/threshold.html")