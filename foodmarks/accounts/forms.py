from django import forms
from django.forms import ModelForm

from .models import *


class PreferencesForm(ModelForm):

    class Meta:
        fields = ('copy_tags',)
        model = UserProfile

