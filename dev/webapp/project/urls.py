"""BidCentral URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required, permission_required # Future test..
from django.views.generic.base import RedirectView
from django.conf import settings
from decorator_include import decorator_include
import debug_toolbar

urlpatterns = [
    path(r'admin/', admin.site.urls),
    url('^$', RedirectView.as_view(url = "bidinterpreter/"), name = "index"),
    path('bidinterpreter/', decorator_include(login_required, include('project.apps.bidinterpreter.urls'))),
    path('profile/', decorator_include(login_required, include('project.apps.profile.urls'))), # new
    path('invite/', include('project.apps.invite.urls')), # new
    path('accounts/', include('allauth.urls')), # new
    url(r'^social/', include("allauth.socialaccount.urls")), # new
    path('__debug__/', include(debug_toolbar.urls)),
    #url('^profile/', include('user_profile.urls'))
    ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
