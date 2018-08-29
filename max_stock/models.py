from django.db import models
from django.contrib.auth.models import User
import django.utils.timezone as timezone

# Create your models here.
class Thresholds(models.Model):
    sku = models.CharField('Sku',max_length=225)
    warehouse = models.CharField('Warehouse',max_length=225)
    threshold = models.IntegerField('Threshold',default=0)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'stock_thresholds'

class WarehouseStocks(models.Model):
    sku = models.CharField('Sku',max_length=225)
    warehouse = models.CharField('Warehouse', max_length=225)
    qty = models.IntegerField('Qty', default=0)
    is_new = models.IntegerField('Is New', default=1)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'warehouse_stocks'

class SkuUsers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sku = models.CharField('Sku',max_length=225)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'sku_users'

class StockLogs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fun = models.CharField('Sku',max_length=225)
    description = models.TextField('Description')
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'stock_logs'

class AmazonCode(models.Model):
    email = models.CharField('Email',max_length=225)
    code = models.CharField('Code',max_length=225)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'amazon_code'

class OrderItems(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    order_id = models.CharField('Order Id', max_length=225)
    sku = models.CharField('SKU', max_length=225)
    order_status = models.CharField('Status', max_length=50)
    email = models.CharField('Email', max_length=225)
    customer = models.CharField('Customer', max_length=225, default=None)
    is_email = models.IntegerField('Is Email', default=0)
    is_presale = models.IntegerField('Presale', default=0)
    payments_date = models.DateTimeField('Payments Date', null=True)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'order_items'

class OldOrderItems(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    order_id = models.CharField('Order Id', max_length=225)
    sku = models.CharField('SKU', max_length=50)
    order_status = models.CharField('Status', max_length=50)
    email = models.CharField('Email', max_length=225)
    customer = models.CharField('Customer', max_length=225)
    is_email = models.IntegerField('Is Email', default=0)
    is_presale = models.IntegerField('Presale', default=1)
    payments_date= models.DateTimeField('Payments Date', null=True)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'old_order_items'

class NoSendRes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    down_date = models.DateField('Date', auto_now_add=True, null=True)
    order_id = models.CharField('Order Id', max_length=225, default='')
    sku = models.CharField('SKU', max_length=50)
    status = models.CharField('Status', max_length=50, default='')
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'no_send_res'

class EmailTemplates(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    sku = models.CharField('SKU', max_length=50)
    keywords = models.CharField('Keywords', max_length=255, default=None)
    title = models.CharField('Title', max_length=255)
    content = models.TextField('Content')
    order_status = models.IntegerField('Order Status', default=0)
    send_time = models.CharField('Send Time', max_length=255, default=None)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'email_templates'

class Schedule(models.Model):
    templates = models.ForeignKey(EmailTemplates, on_delete=models.CASCADE)
    sku = models.CharField('SKU', max_length=50)
    time_str = models.CharField('Time Str', max_length=50)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'schedule'

class Roles(models.Model):
    name = models.CharField('Name', max_length=50)
    code = models.CharField('Code', max_length=50)

    class Meta:
        db_table = 'roles'

class Menus(models.Model):
    name = models.CharField('Name', max_length=50)
    parent_id = models.IntegerField('Parent', default=0)
    roles = models.ManyToManyField(Roles)
    url = models.CharField('Url', max_length=50)
    elem_id = models.CharField('ID', max_length=50)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'menus'

class EmailContacts(models.Model):
    email_address = models.CharField('Email Address', max_length=225)
    email = models.CharField('Email', max_length=225)
    expired_time = models.DateTimeField('Expired', null=True)
    created = models.DateTimeField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'email_contacts'


