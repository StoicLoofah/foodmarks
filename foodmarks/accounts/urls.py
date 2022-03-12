from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout

from . import views

app_name = 'accounts'

urlpatterns = [
    url(r'^preferences/$', views.preferences, name='preferences'),
    url(r'^login/', auth_views.LoginView.as_view(template_name='accounts/login.html')),
    url(r'^logout/', auth_views.LogoutView.as_view()),
]


