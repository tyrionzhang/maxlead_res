# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy_djangoitem import DjangoItem
from maxlead_site.models import AsinReviews,Reviews,Listings,Questions,Answers,ListingWacher,CategoryRank
from max_stock.models import WarehouseStocks,OrderItems


class AsinReviewsItem(DjangoItem):
    # define the fields for your item here like:
    django_model = AsinReviews

class ReviewsItem(DjangoItem):
    # define the fields for your item here like:

    image_urls = scrapy.Field()
    images = scrapy.Field()
    django_model = Reviews

class ListingsItem(DjangoItem):
    # define the fields for your item here like:

    image_urls = scrapy.Field()
    images = scrapy.Field()
    django_model = Listings

class QuestionsItem(DjangoItem):
    # define the fields for your item here like:
    django_model = Questions

class AnswersItem(DjangoItem):
    # define the fields for your item here like:
    django_model = Answers

class ListingWacherItem(DjangoItem):
    # define the fields for your item here like:
    django_model = ListingWacher

class CategoryRankItem(DjangoItem):
    django_model = CategoryRank

# stocks
class WarehouseStocksItem(DjangoItem):
    # define the fields for your item here like:
    django_model = WarehouseStocks

class OrderItemsItem(DjangoItem):
    # define the fields for your item here like:
    django_model = OrderItems


