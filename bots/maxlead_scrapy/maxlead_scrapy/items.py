# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy_djangoitem import DjangoItem
from maxlead_site.models import AsinReviews,Reviews,Listings


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
