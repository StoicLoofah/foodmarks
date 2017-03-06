from fm.models import *
from django.contrib import admin

class RecipeAdmin(admin.ModelAdmin):
    search_fields = ('title', )


class RibbonAdmin(admin.ModelAdmin):
    search_fields = ('recipe__title', )
    list_display = ('id', 'recipe', 'user', )
    list_filter = ('user', )
    raw_id_fields = ('recipe', 'user')

class TagAdmin(admin.ModelAdmin):
    search_fields = ('key', 'value', )
    list_display = ('value', 'key', 'ribbon', )
    list_filter = ('key', )
    raw_id_fields = ('ribbon', )

admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ribbon, RibbonAdmin)
admin.site.register(Tag, TagAdmin)
