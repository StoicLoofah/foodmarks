from django import forms
from django.forms import ModelForm

from .models import *

class RecipeForm(ModelForm):

    class Meta:
        model = Recipe

        fields = (
            'title',
            'link',
            'servings',
            'description',
            'ingredients',
            'directions',
        )

        widgets = {
                'title': forms.TextInput(attrs={'size': '50'}),
                'link': forms.TextInput(attrs={'size': '50'})
                }


class RibbonForm(ModelForm):

    class Meta:
        model = Ribbon
        exclude = ('recipe', 'user', 'boxed_on')
