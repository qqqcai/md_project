"""zmeiduo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view(), name="register"),
    url(r'^login/$', views.LoginView.as_view(), name="login"),
    url(r'^logout/$', views.LogoutView.as_view(), name="logout"),
    url(r'^info/$', views.UserInfoView.as_view(), name="info"),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_]{5,20})/count/$', views.UsernameCountView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
]


# 验证是否已经登录，如果没有登录会自动跳转到设定页 LOGIN_URL = '/login/' (setting.py中设定)

# 方法一：
# from django.contrib.auth.decorators import login_required  # login_required()
# url(r'^info/$', login_required(views.UserInfoView.as_view()), name="info"),

# 方法二：
# views.py中导入  from django.contrib.auth.mixins import LoginRequiredMixin
# 在class中加入父类继承   class xxx(LoginRequiredMixin, View):

