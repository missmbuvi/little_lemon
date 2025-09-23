from django.contrib import admin

from django.contrib import admin
from .models import Category, MenuItem, Cart, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'featured', 'category']
    list_filter = ['category', 'featured']
    search_fields = ['title']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'menuitem', 'quantity', 'price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'delivery_crew', 'status', 'total', 'date']
    list_filter = ['status', 'date']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menuitem', 'quantity', 'price']