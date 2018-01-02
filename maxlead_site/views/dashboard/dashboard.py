# -*- coding: utf-8 -*-
import json,datetime
from django.shortcuts import render,HttpResponse
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count,Max
from maxlead_site.models import Listings,UserAsins,Questions,Answers,Reviews,AsinReviews
from maxlead_site.views.app import App
from maxlead_site.common.excel_world import get_excel_file

class Dashboard:

    def index(self):
        data = {}
        return render(self, 'dashboard/dashboard.html', data)