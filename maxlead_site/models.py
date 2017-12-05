from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserAsins(models.Model):
    user = models.ForeignKey(User)
    aid = models.CharField('AsinId',max_length=50)
    sku = models.CharField('SKU',max_length=50,default='')
    review_watcher = models.BooleanField('Review Watcher', default=True)
    listing_watcher = models.BooleanField('Listing Watcher', default=True)
    is_email = models.BooleanField(u'是否邮件通知',default=1)
    is_use = models.BooleanField('Status', default=True)
    last_check = models.DateTimeField('Last Check', null=True)

    class Meta:
        db_table = 'user_asins'

class AsinReviews(models.Model):
    aid = models.CharField('AsinId',max_length=50)
    positive_keywords = models.TextField('Positive Keywords',null=True)
    negative_keywords = models.TextField('Negative Keywords',null=True)
    avg_score = models.DecimalField('Avg Score', max_digits=2, decimal_places=1)
    total_review = models.IntegerField('Total Reviews', default=0)
    created = models.DateField('Create Date',auto_now_add=True)

    class Meta:
        db_table = 'asin_reviews'

class Reviews(models.Model):
    name = models.CharField('User',max_length=255)
    asin = models.CharField('AsinId',max_length=50)
    title = models.CharField('Title',max_length=255)
    variation = models.CharField('Variation',max_length=255,null=True)
    content = models.TextField('Content', default='',null=True)
    review_link = models.CharField('Review Link',max_length=500,null=True)
    score = models.IntegerField('Score',default=0)
    is_vp = models.IntegerField('VP',default=0,null=True)
    review_date = models.DateField('Date')
    created = models.DateField('Create Date',auto_now_add=True)
    image_names = models.TextField('Images', null=True)
    image_urls = models.TextField('Image Urls', null=True)

    class Meta:
        db_table = 'reviews'

class listings(models.Model):
    title = models.CharField('Title', max_length=255)
    asin = models.CharField('AsinId', max_length=50)
    sku = models.CharField('SKU', max_length=50)
    brand = models.CharField('Brand', max_length=50)
    buy_box = models.CharField('Buy Box', max_length=50)
    price = models.DecimalField('Price', max_digits=2, decimal_places=1)
    total_review = models.IntegerField('RVW QTY', default=0)
    rvw_score = models.IntegerField('RVW Score', default=0)
    category_rank = models.CharField('Category Rank', max_length=50)
    inventory = models.IntegerField('Inventory', default=0)
    created = models.DateTimeField('Create Date', default=0)
    image_names = models.TextField('Images', null=True)

    class Meta:
        db_table = 'product_list'