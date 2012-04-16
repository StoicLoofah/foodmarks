from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from foodmarks.fm.models import Recipe
from foodmarks.fm.views import view_recipe

class NewestRecipesFeed(Feed):
    title = 'foodmarks Newest Recipes'
    link = '/feed/'
    description = 'The latest recipes and bookmarks on foodmarks.'

    def items(self):
        return Recipe.objects.order_by('-time_created')[:10]

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        if item.link:
            return item.link
        else:
            return reverse('fm.views.view_recipe', args=[int(item.id)])

    def item_description(self, item):
        if item.link:
            return mark_safe(
                '<a href="{0}">View on foodmarks</a>'.format(
                    reverse('fm.views.view_recipe', args=[int(item.id)])))
        return ''