import datetime

from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Recipe
from .views import view_recipe

class NewestRecipesFeed(Feed):
    title = 'foodmarks Newest Recipes'
    link = '/feed/'
    description = 'The latest recipes and bookmarks on foodmarks.'

    def items(self):
        time = datetime.datetime.now() - datetime.timedelta(days=7)
        return Recipe.objects.filter(
                time_created__gte=time).order_by('-time_created')

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        if item.link:
            return item.link
        else:
            return reverse('view_recipe', args=[int(item.id)])

    def item_description(self, item):
        if item.link:
            return mark_safe(
                '<a href="{0}">View on foodmarks</a>'.format(
                    reverse('view_recipe', args=[int(item.id)])))
        return ''
