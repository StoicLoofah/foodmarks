from django.conf.urls import include, url
from django.contrib.auth.views import login, logout

from . import views

urlpatterns = [
    url(r'^preferences/$', views.preferences, name='preferences'),
    url(r'^login/', login,
        {'template_name': 'accounts/login.html'}),
    url(r'^logout/', logout, {'next_page': '/',}),
]


