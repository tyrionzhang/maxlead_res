from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserAsins(models.Model):
    user = models.ForeignKey(User)
    aid = models.CharField('AsinId',max_length=50)
    name = models.CharField('Field',max_length=255,default='')
    alias = models.CharField('Alias',max_length=255,default='')
    is_email = models.BooleanField(u'是否邮件通知',default=1)
    is_use = models.BooleanField(default=1)

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
    image_names = models.TextField('Images', null=True)
    image_urls = models.TextField('Image Urls', null=True)
    created = models.DateField('Create Date',auto_now_add=True)

    class Meta:
        db_table = 'reviews'
