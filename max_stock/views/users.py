# -*- coding: utf-8 -*-
import time,json
from django.contrib import auth
from django.shortcuts import render,HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from maxlead_site.models import UserProfile
from maxlead_site.views import commons

@csrf_exempt
def userLogin(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/admin/max_stock/index/",{'user': request.user})
    return render(request,"Stocks/user/login.html")