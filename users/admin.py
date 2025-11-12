from django.contrib import admin
from .models import Artisan, Client, TradeCategory


@admin.register(TradeCategory)
class TradeCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Artisan)
class ArtisanAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email_address', 'phone_number', 'trade_category', 'location', 'language', 'created_at')
    search_fields = ('first_name', 'last_name', 'email_address', 'trade_category__name')
    list_filter = ('trade_category', 'location', 'language')
    ordering = ('-created_at',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email_address', 'phone_number', 'location', 'language', 'created_at')
    search_fields = ('first_name', 'last_name', 'email_address')
    list_filter = ('location', 'language')
    ordering = ('-created_at',)

