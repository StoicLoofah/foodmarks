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

    def get_tag_dict(self, user=None, dedup=True):
        if user is not None:
            try:
                ribbon = Ribbon.objects.get(recipe=self, user=user)
                return ribbon.get_tag_dict()
            except ObjectDoesNotExist:
                return {}
        if getattr(self, '_tag_dict', None) is None:
            tags = Tag.objects.filter(ribbon__recipe=self)
            tag_dict = {}
            for tag in tags:
                if not tag.key in tag_dict:
                    tag_dict[tag.key] = [tag.value]
                else:
                    tag_dict[tag.key].append(tag.value)
            for key, value in tag_dict.iteritems():
                if dedup:
                    tag_dict[key] = sorted(set(value))
                else:
                    value.sort()

            self._tag_dict = tag_dict
        return self._tag_dict

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

    def get_tag_dict(self):
        if getattr(self, '_tag_dict', None) is None:
            tags = self.tag_set.all()
            tag_dict = {}
            for tag in tags:
                if not tag.key in tag_dict:
                    tag_dict[tag.key] = [tag.value]
                else:
                    tag_dict[tag.key].append(tag.value)
            for value in tag_dict.itervalues():
                value.sort()
            self._tag_dict = tag_dict
        return self._tag_dict

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
