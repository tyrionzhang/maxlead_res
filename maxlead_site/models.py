from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Create your models here.

class MenberGroups(models.Model):
    name = models.CharField('Name', max_length=50)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'menber_groups'

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    state = models.IntegerField('State',default=0)
    role = models.IntegerField('Role',default=0)
    group = models.ManyToManyField(MenberGroups,related_name='MenberGroups')
    er_count = models.IntegerField(default=0)
    em_count = models.IntegerField(default=0)
    er_time = models.IntegerField(default=0)

    class Meta:
        db_table = 'user_profile'

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)


class UserAsins(models.Model):
    user = models.ForeignKey(User)
    aid = models.CharField('AsinId',max_length=50)
    sku = models.CharField('SKU',max_length=50,default='')
    keywords = models.CharField('Keywords',max_length=255,default='')
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

class Listings(models.Model):
    title = models.CharField('Title', max_length=255)
    asin = models.CharField('AsinId', max_length=50)
    sku = models.CharField('SKU', max_length=50)
    brand = models.CharField('Brand', max_length=50)
    buy_box = models.CharField('Buy Box', max_length=50)
    price = models.CharField('Price', max_length=50,null=True)
    total_review = models.IntegerField('RVW QTY', default=0)
    rvw_score = models.DecimalField('RVW Score', max_digits=2, decimal_places=1,null=True)
    category_rank = models.TextField('Category Rank', null=True)
    inventory = models.IntegerField('Inventory', default=0)
    is_review_watcher = models.BooleanField('Is Review Watcher', default=True)
    is_listing_watcher = models.BooleanField('Is Listing Watcher', default=True)
    created = models.DateTimeField('Create Date', auto_now_add=True)
    image_date = models.DateField('Image Date',null=True)
    image_names = models.TextField('Images', null=True)
    image_thumbs = models.TextField('Images Thumb', null=True)
    image_urls = models.TextField('Image Urls', null=True)

    class Meta:
        db_table = 'product_list'

class Questions(models.Model):
    question = models.CharField('Question',max_length=225)
    asin = models.CharField('AsinId',max_length=50,default='')
    asked = models.CharField('Asked',max_length=225,default='')
    votes = models.IntegerField('Votes',default=0,null=True)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'questions'
class Answers(models.Model):
    question = models.ForeignKey(Questions)
    person = models.CharField('Person',max_length=225)
    answer = models.TextField('Answer',null=True)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'answers'

class Log(models.Model):
    name = models.CharField('Name',max_length=225)
    description = models.CharField('Description',max_length=225)
    user = models.ForeignKey(User)
    created = models.DateTimeField('Create Date',auto_now_add=True)

    class Meta:
        db_table = 'log'