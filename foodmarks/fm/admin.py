from fm.models import *
from django.contrib import admin

class RecipeAdmin(admin.ModelAdmin):
    search_fields = ('title', )


class RibbonAdmin(admin.ModelAdmin):
    search_fields = ('recipe__title', )
    list_display = ('id', 'recipe', 'user', )
    list_filter = ('user', )

class TagAdmin(admin.ModelAdmin):
    search_fields = ('key', 'value', )
    list_display = ('key', 'value', 'ribbon', )
    list_filter = ('key', )

admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ribbon, RibbonAdmin)
admin.site.register(Tag, TagAdmin)
