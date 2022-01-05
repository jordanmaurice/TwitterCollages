from django.contrib import admin
from .models import Order

class OrderAdmin(admin.ModelAdmin):
    list = ('first_name', 'last_name', 'email', 'twitter_handle')

admin.site.register(Order, OrderAdmin)