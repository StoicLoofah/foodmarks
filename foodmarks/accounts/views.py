from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import PreferencesForm


@login_required(login_url='/accounts/login/')
def preferences(request):
    form = PreferencesForm(request.POST or None, instance=request.user.userprofile)

    if form.is_valid():
        form.save()

    return render(request, 'accounts/preferences.html', {'form': form})
