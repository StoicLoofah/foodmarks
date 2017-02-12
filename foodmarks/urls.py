from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from fm.feeds import NewestRecipesFeed
from fm import views

admin.autodiscover()

urlpatterns = [
    url(r'^add/', views.add_recipe, name='add_recipe'),
    url(r'^action/', views.action),
    url(r'^bookmarklet/', views.bookmarklet),
    url(r'^edit/(\d+)/$', views.edit_recipe, name='edit_recipe'),
    url(r'^recipe/(\d+)/$', views.view_recipe, name='view_recipe'),
    url(r'^ribbon/delete/(\d+)/$', views.delete_ribbon),
    url(r'^search/$', views.search_recipes, name='search_recipes'),
    url(r'^tag/category/$', views.get_tag_category),
    url(r'^feed/$', NewestRecipesFeed()),
    url(r'^$', views.index, name='index'),
    # url(r'^foodmarks/', include('foodmarks.foo.urls')),
    url(r'^accounts/', include('accounts.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
]

urlpatterns += staticfiles_urlpatterns()
