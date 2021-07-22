from django.urls import path
from django.conf.urls import url

from . import views

app_name = "invite"

urlpatterns = [
    #url(r'^$', views.index, name='index'),
    # \b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b
    url(r'^(?P<invite_code>\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b)$', views.InviteView.as_view(), name='invite'),
]