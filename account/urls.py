from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path("", views.index, name="home"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('short/url/', views.shorten_url, name='shorten_url'),
    path('url/list/', views.short_url_list, name='url_list'),
    path('<str:short_url>/', views.short_url_redirect, name='short_url_redirect'),
    path('short/url/create/', views.create_short_url, name='creat_short_url'),
    # path('short/url/create/', views.creat_short_url, name='creat_short_url'),
    path('url/detail/<str:short_url>/', views.short_url_detail, name='url_detail'),
]