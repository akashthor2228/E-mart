from django.db import models
from django.contrib.auth.models import User
import datetime
import os

def getFileName(request, filename):
    now_time = datetime.datetime.now().strftime('%Y%m%d%H:%M:%S')
    new_filename="%s%s" % (now_time,filename)
    return os.path.join('uploads',new_filename)


class Category(models.Model):
    name = models.CharField(max_length=150,null=False,blank=False)
    image = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(max_length=500,null=False,blank=False)
    status = models.BooleanField(default=False,help_text="0-default,1-hidden")
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category,on_delete=models.CASCADE)
    name = models.CharField(max_length=150, null=False, blank=False)
    vendor = models.CharField(max_length=150, null=False, blank=False)
    product_image = models.URLField(max_length=500, blank=True, null=True)
    quantity = models.IntegerField(null=False, blank=False)
    original_price = models.FloatField(null=False, blank=False)
    selling_price = models.FloatField(null=False, blank=False)
    description = models.TextField(max_length=500, null=False, blank=False)
    status = models.BooleanField(default=False, help_text="0-default,1-hidden")
    trending = models.BooleanField(default=False, help_text="0-default,1-trending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    product_qty = models.IntegerField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.product_qty*self.product.selling_price



# models.py
class Fav(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # DELETE product_qty from here

    class Meta:
        db_table = 'fav'

    @property
    def total_cost(self):
        return self.product_qty*self.product.selling_price



class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    user                = models.ForeignKey(User, on_delete=models.CASCADE)
    razorpay_order_id   = models.CharField(max_length=200, blank=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True)
    amount              = models.FloatField()
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at          = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"