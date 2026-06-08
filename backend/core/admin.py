from django.contrib import admin
from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'processed', 'created_at')
    list_filter = ('processed', 'created_at')
    search_fields = ('name', 'owner__username')
