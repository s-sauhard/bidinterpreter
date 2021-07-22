from django.urls import path
from django.conf.urls import url
from . import views

app_name = "profile"

urlpatterns = [
    #url(r'^$', views.index, name='index'),
    url(r'create/', views.CreateUserProfileView.as_view(), name='create_profile'),
    url(r'update/', views.UpdateUserProfileView.as_view(), name='update_profile'),
]
