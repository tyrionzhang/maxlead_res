# -*- coding: utf-8 -*-
from django.shortcuts import render,HttpResponse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from maxlead_site.models import Listings,UserAsins,MenberGroups
from maxlead_site.views.app import App

class Listing:

    def index(self):
        user = App.get_user_info(self)
        if not user:
            return HttpResponseRedirect("/admin/maxlead_site/login/")
        listKwd = self.POST.get('listKwd','')
        searchCol = self.POST.get('searchCol','')
        buybox = self.POST.get('buybox','')
        status = self.POST.get('status','')
        revstatus = self.POST.get('revstatus','')
        liststatus = self.POST.get('liststatus','')

        asins = []
        user_asins = False
        if user.role == 2:
            user_asins = UserAsins.objects.filter().all()

        elif user.role == 0:
            user_asins = UserAsins.objects.filter(user=user.user).all()
        elif user.role == 1:
            groups = MenberGroups.objects.filter(user=user.user)
            user_list = User.objects.filter(group=groups).all()
            user_asins = UserAsins.objects.filter(user=user_list).all()

        if user_asins:
            if status:
                user_asins = user_asins.filter(is_use=status).all()
            if revstatus:
                user_asins = user_asins.filter(review_watcher=revstatus).all()
            if liststatus:
                user_asins = user_asins.filter(listing_watcher=liststatus).all()

            for val in user_asins:
                asins.append(val.aid)
            listings = Listings.objects.order_by("-id").filter(asin__in=asins).annotate(count=Count('asin'))

            if buybox:
                listings = listings.filter(buy_box=buybox)
            if listKwd and searchCol:
                if searchCol == 'SKU':
                    listings = listings.filter(sku__icontains=listKwd)
                if searchCol == 'ASIN':
                    listings = listings.filter(asin__icontains=listKwd)
                if searchCol == 'title':
                    listings = listings.filter(title__icontains=listKwd)
                if searchCol == 'brand':
                    listings = listings.filter(brand__icontains=listKwd)
                if searchCol == 'seller':
                    listings = listings.filter(buy_box_res__icontains=listKwd)
            limit = self.GET.get('limit', 6)
            total_count = listings.count()
            if int(limit) >= total_count:
                limit = total_count
            if not listings:
                return render(self, 'listings/listing.html', {'data': ''})
            paginator = Paginator(listings, limit)
            page = self.GET.get('page')
            try:
                list_data = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                list_data = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                list_data = paginator.page(paginator.num_pages)
            data = {
                'data': True,
                'user': user,
                'avator': user.user.username[0],
                'list_data': list_data,
            }

            return render(self, 'listings/listing.html', data)