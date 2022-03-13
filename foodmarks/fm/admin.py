from fm.models import *
from django.contrib import admin

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'link')
    search_fields = ('title', )


@admin.register(Ribbon)
class RibbonAdmin(admin.ModelAdmin):
    search_fields = ('recipe__title', )
    list_display = ('id', 'recipe', 'user', )
    list_filter = ('user', )
    raw_id_fields = ('recipe', 'user')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('key', 'value', )
    list_display = ('value', 'key', 'ribbon', )
    list_filter = ('key', )
    raw_id_fields = ('ribbon', )

