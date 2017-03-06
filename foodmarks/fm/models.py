import datetime

from django.contrib.auth.models import User
from django.db import models

from constants import *

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    link = models.URLField(max_length=255, blank=True, null=True, unique=True)
    servings = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    ingredients = models.TextField(blank=True)
    directions = models.TextField(blank=True)

    time_created = models.DateTimeField(auto_now_add=True)

    def get_tags(self):
        return sorted(Tag.objects.filter(ribbon__recipe=self).values_list('value', flat=True).distinct())

    def get_used_count(self):
        count = 0
        for ribbon in self.ribbon_set.all():
            if ribbon.is_used:
                count += 1
        return count

    def get_thumbs_up_count(self):
        count = 0
        for ribbon in self.ribbon_set.all():
            if ribbon.thumb == True:
                count += 1
        return count

    def get_thumbs_down_count(self):
        count = 0
        for ribbon in self.ribbon_set.all():
            if ribbon.thumb == False:
                count += 1
        return count

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.link == '':
            self.link = None
        super(Recipe, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-time_created']


class Ribbon(models.Model):
    recipe = models.ForeignKey(Recipe)
    user = models.ForeignKey(User)
    comments = models.TextField(
            blank=True, verbose_name="my comments")
    time_created = models.DateTimeField(auto_now_add=True)

    is_boxed = models.BooleanField(
            default=False, verbose_name="Include in your Recipe Box?")
    boxed_on = models.DateTimeField(blank=True, null=True)
    is_used = models.BooleanField(
            default=False, verbose_name="Have you used this recipe?")

    THUMB_CHOICES = (
        (True, 'Thumbs Up'),
        (False, 'Thumbs Down'),
        )
    thumb = models.NullBooleanField(
            blank=True, null=True, choices=THUMB_CHOICES,
            verbose_name="How's the recipe?")

    def get_tags(self):
        return sorted(self.tag_set.values_list('value', flat=True).distinct())

    def __unicode__(self):
        return u'{0} Ribbon for {1}'.format(unicode(self.recipe),
                                           unicode(self.user))

    class Meta:
        unique_together = ('recipe', 'user',)
        ordering = ['-time_created']


class Tag(models.Model):
    ribbon = models.ForeignKey(Ribbon)
    key = models.CharField(max_length=50, blank=True, help_text='Deprecated')
    value = models.CharField(max_length=50)

    def __unicode__(self):
        return u'{0}: {1}'.format(self.key, self.value)
