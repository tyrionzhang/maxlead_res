from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Thresholds(models.Model):
    sku = models.CharField('Sku',max_length=225)
    warehouse = models.CharField('Warehouse',max_length=225)
    threshold = models.IntegerField('Threshold',default=0)
    created = models.DateField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'stock_thresholds'

class WarehouseStocks(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sku = models.CharField('Sku',max_length=225)
    warehouse = models.CharField('Warehouse', max_length=225)
    qty = models.IntegerField('Qty', default=0)
    created = models.DateField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'warehouse_stocks'

class SkuUsers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sku = models.CharField('Sku',max_length=225)
    created = models.DateField('Create Date', auto_now_add=True)

    class Meta:
        db_table = 'sku_users'