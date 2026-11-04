"""Настройки админ-панели для приложения blog."""

from django.contrib import admin

from .models import Category, Location, Post

admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Post)

admin.site.site_header = "Блогикум"
admin.site.site_title = "Блогикум"
