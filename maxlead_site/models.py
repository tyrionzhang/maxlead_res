from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


class UserProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    group = models.ForeignKey('self',default=1,on_delete=models.CASCADE)
    state = models.IntegerField('State',default=1)
    role = models.IntegerField('Role',default=0)
    stocks_role = models.CharField('Stocks Role',max_length=50)
    other_email = models.CharField('Other Email',max_length=225,null=True)
    email_pass = models.CharField('Email Pass',max_length=225,null=True)
    smtp_server = models.CharField('Smtp Server',max_length=225,null=True)
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
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    aid = models.CharField('AsinId',max_length=50)
    sku = models.CharField('SKU',max_length=50,default='')
    buy_box = models.CharField('BuyBox',max_length=50,default='')
    ownership = models.CharField('Ownership',max_length=50,default='')
    keywords1 = models.CharField('Keywords1',max_length=255,default='')
    keywords2 = models.CharField('Keywords2',max_length=255,default='')
    keywords3 = models.CharField('Keywords3',max_length=255,default='')
    cat1 = models.CharField('Cat1',max_length=255,default='')
    cat2 = models.CharField('Cat2',max_length=255,default='')
    cat3 = models.CharField('Cat3',max_length=255,default='')
    review_watcher = models.BooleanField('Review Watcher', default=True)
    listing_watcher = models.BooleanField('Listing Watcher', default=True)
    is_email = models.BooleanField(u'是否邮件通知',default=1)
    is_use = models.BooleanField('Status', default=True)
    is_done = models.IntegerField('Is Done', default=0, null=True)
    last_check = models.DateTimeField('Last Check', null=True)
    update_time = models.DateTimeField('Update Time', null=True)
    listing_time = models.DateTimeField('Listing Time', null=True)
    qa_time = models.DateTimeField('Qa Time', null=True)
    review_time = models.DateTimeField('Review Time', null=True)
    watcher_time = models.DateTimeField('Watcher Time', null=True)
    catrank_time = models.DateTimeField('Watcher Time', null=True)

    class Meta:
        db_table = 'user_asins'

class AsinReviews(models.Model):
    aid = models.CharField('AsinId',max_length=50)
    positive_keywords = models.TextField('Positive Keywords',null=True)
    negative_keywords = models.TextField('Negative Keywords',null=True)
    avg_score = models.DecimalField('Avg Score', max_digits=2, decimal_places=1)
    total_review = models.IntegerField('Total Reviews', default=0)
    is_done = models.IntegerField('Done', default=0,null=True)
    created = models.DateField('Create Date',auto_now_add=True)

    class Meta:
        db_table = 'asin_reviews'

class AsinReviewsBackcup(models.Model):
    ar_id = models.IntegerField('ar_id',default=0)
    aid = models.CharField('AsinId',max_length=50)
    positive_keywords = models.TextField('Positive Keywords',null=True)
    negative_keywords = models.TextField('Negative Keywords',null=True)
    avg_score = models.DecimalField('Avg Score', max_digits=2, decimal_places=1)
    total_review = models.IntegerField('Total Reviews', default=0)
    is_done = models.IntegerField('Done', default=0,null=True)
    created = models.DateField('Create Date')

    class Meta:
        db_table = 'asin_reviews_backcup'

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
    image_thumbs = models.TextField('Images Thumb', null=True)
    image_urls = models.TextField('Image Urls', null=True)

    class Meta:
        db_table = 'reviews'

class ReviewsBackcup(models.Model):
    rid = models.IntegerField('Rid',default=0)
    name = models.CharField('User',max_length=255)
    asin = models.CharField('AsinId',max_length=50)
    title = models.CharField('Title',max_length=255)
    variation = models.CharField('Variation',max_length=255,null=True)
    content = models.TextField('Content', default='',null=True)
    review_link = models.CharField('Review Link',max_length=500,null=True)
    score = models.IntegerField('Score',default=0)
    is_vp = models.IntegerField('VP',default=0,null=True)
    review_date = models.DateField('Date')
    created = models.DateField('Create Date')
    image_names = models.TextField('Images', null=True)
    image_thumbs = models.TextField('Images Thumb', null=True)
    image_urls = models.TextField('Image Urls', null=True)

    class Meta:
        db_table = 'reviews_backcup'

class Listings(models.Model):
    user_asin = models.ForeignKey(UserAsins,default=1,on_delete=models.CASCADE)
    title = models.CharField('Title', max_length=255)
    answered= models.CharField('Answered ',max_length=50,default='')
    asin = models.CharField('AsinId', max_length=50)
    sku = models.CharField('SKU', max_length=50)
    brand = models.CharField('Brand', max_length=50)
    shipping = models.CharField('Shipping', max_length=255,default='',null=True)
    prime = models.IntegerField('Prime', default=0)
    description = models.TextField('Description',default='')
    feature = models.TextField('Feature',default='')
    promotion = models.TextField('Promotion',default='')
    lightning_deal = models.CharField('Lightning Deal',max_length=255,default='')
    buy_box = models.CharField('Buy Box', max_length=50)
    buy_box_link = models.CharField('Buy Box Link', max_length=255,default='')
    buy_box_res = models.CharField('Buy Box Data', max_length=255, default='')
    price = models.CharField('Price', max_length=50,null=True)
    total_review = models.IntegerField('RVW QTY', default=0)
    total_qa = models.IntegerField('qa', default=0)
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

class ListingsBackcup(models.Model):
    user_asin = models.IntegerField('uaid',default=0)
    title = models.CharField('Title', max_length=255)
    answered= models.CharField('Answered ',max_length=50,default='')
    asin = models.CharField('AsinId', max_length=50)
    sku = models.CharField('SKU', max_length=50)
    brand = models.CharField('Brand', max_length=50)
    shipping = models.CharField('Shipping', max_length=255,default='',null=True)
    prime = models.IntegerField('Prime', default=0)
    description = models.TextField('Description',default='')
    feature = models.TextField('Feature',default='')
    promotion = models.TextField('Promotion',default='')
    lightning_deal = models.CharField('Lightning Deal',max_length=255,default='')
    buy_box = models.CharField('Buy Box', max_length=50)
    buy_box_link = models.CharField('Buy Box Link', max_length=255,default='')
    buy_box_res = models.CharField('Buy Box Data', max_length=255, default='')
    price = models.CharField('Price', max_length=50,null=True)
    total_review = models.IntegerField('RVW QTY', default=0)
    total_qa = models.IntegerField('qa', default=0)
    rvw_score = models.DecimalField('RVW Score', max_digits=2, decimal_places=1,null=True)
    category_rank = models.TextField('Category Rank', null=True)
    inventory = models.IntegerField('Inventory', default=0)
    is_review_watcher = models.BooleanField('Is Review Watcher', default=True)
    is_listing_watcher = models.BooleanField('Is Listing Watcher', default=True)
    created = models.DateTimeField('Create Date')
    image_date = models.DateField('Image Date',null=True)
    image_names = models.TextField('Images', null=True)
    image_thumbs = models.TextField('Images Thumb', null=True)
    image_urls = models.TextField('Image Urls', null=True)

    class Meta:
        db_table = 'product_list_backcup'

class ListingWacher(models.Model):
    asin = models.CharField('AsinId', max_length=50)
    seller = models.CharField('Seller', max_length=50)
    seller_link = models.CharField('Seller Link', max_length=225,null=True,default='')
    price = models.CharField('Price', max_length=50,null=True)
    shipping = models.CharField('Shipping', max_length=255, default='',null=True)
    fba = models.IntegerField('FBA', default=0)
    prime = models.IntegerField('Prime', default=0)
    winner = models.IntegerField('Winner', default=0)
    images = models.CharField('Images', max_length=255, default='')
    created = models.DateTimeField('Create Date', auto_now_add=True)


    class Meta:
        db_table = 'listing_wacher'

class ListingWacherBackcup(models.Model):
    asin = models.CharField('AsinId', max_length=50)
    seller = models.CharField('Seller', max_length=50)
    seller_link = models.CharField('Seller Link', max_length=225,null=True,default='')
    price = models.CharField('Price', max_length=50,null=True)
    shipping = models.CharField('Shipping', max_length=255, default='',null=True)
    fba = models.IntegerField('FBA', default=0)
    prime = models.IntegerField('Prime', default=0)
    winner = models.IntegerField('Winner', default=0)
    images = models.CharField('Images', max_length=255, default='')
    created = models.DateTimeField('Create Date')

    class Meta:
        db_table = 'listing_wacher_backcup'

class Questions(models.Model):
    question = models.TextField('Question',null=True)
    asin = models.CharField('AsinId',max_length=50,default='')
    asked = models.CharField('Asked',max_length=225,default='')
    votes = models.IntegerField('Votes',default=0,null=True)
    count = models.IntegerField('Count',default=0,null=True)
    is_done = models.IntegerField('Done',default=0,null=True)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'questions'

class QuestionsBackcup(models.Model):
    qid = models.IntegerField('qid',default=0)
    question = models.TextField('Question',null=True)
    asin = models.CharField('AsinId',max_length=50,default='')
    asked = models.CharField('Asked',max_length=225,default='')
    votes = models.IntegerField('Votes',default=0,null=True)
    count = models.IntegerField('Count',default=0,null=True)
    is_done = models.IntegerField('Done',default=0,null=True)
    created = models.DateTimeField('Create Date')

    class Meta:
        db_table = 'questions_backcup'

class Answers(models.Model):
    question = models.ForeignKey(Questions,on_delete=models.CASCADE)
    person = models.CharField('Person',max_length=225)
    answer = models.TextField('Answer',null=True)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'answers'

class AnswersBackcup(models.Model):
    qid = models.IntegerField('Qid',default=0)
    person = models.CharField('Person',max_length=225)
    answer = models.TextField('Answer',null=True)
    created = models.DateTimeField('Create Date')

    class Meta:
        db_table = 'answers_backcup'

class Log(models.Model):
    name = models.CharField('Name',max_length=225)
    description = models.CharField('Description',max_length=225)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    created = models.DateTimeField('Create Date',auto_now_add=True)

    class Meta:
        db_table = 'log'

class Task(models.Model):
    name = models.CharField('Name', max_length=225)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    type = models.IntegerField('Type',default=1)
    description = models.CharField('Description', max_length=225)
    asins = models.CharField('Asins', max_length=225)
    is_new = models.IntegerField('New',default=0)
    file_path = models.CharField('File Path', max_length=225,default='')
    finish_time = models.DateTimeField('Created', null=True)
    created = models.DateTimeField('Created', auto_now_add=True)

    class Meta:
        db_table = 'tasks'

class CategoryRank(models.Model):
    user_asin = models.CharField('User Asin',max_length=50)
    asin = models.CharField('Asin',max_length=255)
    cat = models.CharField('Cat',max_length=255,default='')
    keywords = models.CharField('Keywords',max_length=255,default='')
    rank = models.IntegerField('Rank',default=0)
    is_ad = models.IntegerField('Ad',default=0)
    created = models.DateTimeField('Created', auto_now_add=True)

    class Meta:
        db_table = 'category_rank'

class CategoryRankBackcup(models.Model):
    user_asin = models.CharField('User Asin',max_length=50)
    asin = models.CharField('Asin',max_length=255)
    cat = models.CharField('Cat',max_length=255,default='')
    keywords = models.CharField('Keywords',max_length=255,default='')
    rank = models.IntegerField('Rank',default=0)
    is_ad = models.IntegerField('Ad',default=0)
    created = models.DateTimeField('Created')

    class Meta:
        db_table = 'category_rank_backcup'

class ProxyIp(models.Model):
    ip = models.CharField('IP',max_length=50)
    port = models.CharField('Port',max_length=50)
    ip_type = models.CharField('IpType',max_length=50)
    ip_speed = models.CharField('IpSpeed',max_length=50)
    ip_alive = models.CharField('IpAlive',max_length=50)
    created = models.DateTimeField('Created', auto_now_add=True)

    class Meta:
        db_table = 'proxy_ip'