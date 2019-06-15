import logging
import re
import json

from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse
from zmeiduo.utils.response_code import RETCODE
from django_redis import get_redis_connection
from .models import User
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.conf import settings # 代表导入了settings + global_settings

from celery_tasks.email.tasks import send_verify_email


logger = logging.getLogger('django')  # 创建日志输出器对象

class RegisterView(View):
    """用户注册"""

    def get(self, request):
        print(f"检查是否登录过{request.user.is_authenticated}")
        if request.user.is_authenticated: # 如果已经登录过，就跳转首页
            return redirect(reverse('contents:index'))

        return render(request, "register.html")


    def post(self, request):
        """
        接收表单数据，判断是否合规，不合规返回辣鸡，合规尝试添加用户并重定向主页
        """
        print("拿到注册表单", request.POST)

        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        sms_code_client = request.POST.get('sms_code')

        # 判断参数是否齐全 "" () [] {} None 用if判断都是false
        if not all([username, password, password2, mobile, allow, sms_code_client]):
            return HttpResponseForbidden('缺少必传参数')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入5-20个字符的用户名')
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否一致
        if password != password2:
            return HttpResponseForbidden('两次输入的密码不一致')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('请输入正确的手机号码')

        if not re.match(r'^[0-9]{6}$', sms_code_client):
            return HttpResponseForbidden('请输入正确的短信验证码')

        # allow 判断是否勾选用户协议 没有value值，则默认勾选是on，没勾是None，前面all()就会判断为false了，所以不用判断allow值

        content = {'username': username,
                   'password': password,
                   'password2': password,
                   'mobile': mobile}


        # 校验 短信验证码
        redis_conn = get_redis_connection("verify_code")
        redis_conn.delete(f"send_flag_{mobile}") # 提交了一次注册，都允许他重新发送验证码
        sms_code_server = redis_conn.get(f"sms_{mobile}")

        if sms_code_server is None:
            content['register_errmsg'] = '无效的短信验证码'
            return render(request, 'register.html', content)

        redis_conn.delete(f"sms_{mobile}")  # 取出来后如果不是空，要删除

        if sms_code_server.decode() != sms_code_client:
            content['register_errmsg'] = '短信验证码有误'
            return render(request, 'register.html', content)

        # 保存注册数据 create_user 属于django自带含密码加密
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except Exception as e:
            content['register_errmsg'] = '注册失败'
            return render(request, 'register.html', content)

        # user = User.objects.create()
        # user.set_password(password) #如果不用create_user ，也可以这样
        # user.save()

        # 注册成功同时帮他登录  实现状态保持的方式 # 本质是将当前用户id储存到session
        login(request, user)

        response = redirect(reverse('contents:index'))
        response.set_cookie("username", user.username, max_age=3600 * 24 * 15)

        # 响应注册结果
        return response


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        """
        :param request: 请求对象
        :param username: 地址栏传来的用户名
        :return: json
        """
        count = User.objects.filter(username=username).count()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param username: 地址栏传来的手机号
        :return: json
        """
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class LoginView(View):
    """帐号登录"""

    def get(self, request):
        print("进入了帐号登录")
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        remembered = request.POST.get("remembered")
        print(f"拿到登录界面表单帐号：{username},密码：{password}")
        if not all([username, password]):
            return HttpResponseForbidden("登录信息不齐")

        # 成功返回对象，失败返回0
        user = authenticate(username=username, password=password)

        # User.USERNAME_FIELD = 'mobile'  # 修改这个，直接令authenticate判断的帐号变为手机号而不需要重写
        # User.USERNAME_FIELD = 'username'


        if not user:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 记住当前登录信息
        login(request, user)

        next_url = request.GET.get("next", reverse('contents:index'))
        response = redirect(next_url)
        response.set_cookie("username", user.username, max_age=(3600 * 24 * 15 if remembered else None ))

        # 如果没有选记住用户，就把session有效期设为0
        if not remembered:
            # set_expiry(None) -- None 代表默认两周(14天) , 0代表 关闭浏览器就删除
            request.session.set_expiry(0)

            # cookie如果指定过期时间为None，关闭浏览器删除，如果指定0,还没出生就byebye了
        print(f"登录成功返回主页{username}")
        return response


class LogoutView(View):
    """退出用户"""
    def get(self, request):
        logout(request)  # 退出登录标准用法
        response = redirect(reverse('contents:index'))
        response.delete_cookie("username")  # 清除cookies中username的记录
        return response


class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""
    def get(self, request):
        return render(request, 'user_center_info.html')

        # LoginRequiredMixin 等于做了下面的事
        # user = request.user # 如果没有登录就是匿名用户
        # if user.is_authenticated:
        #     return render(request, 'user_center_info.html')
        # else:
        #     # 如果没有登录就重定向界面
        #     return redirect('/login/?next=/info/')


class EmailView(View):
    def put(self, request):
        # 拿前端put过来的body信息
        email_dict = json.loads(request.body.decode())
        email_client = email_dict.get('email')
        print(f'验证的邮箱是{email_client}')

        # 校验邮箱
        if not email_client:
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email_client):
            print("匹配不到")
            return JsonResponse({'code': RETCODE.EMAILERR, 'errmsg': '邮箱格式错误'})

        # 添加邮箱
        user = request.user
        print("搜到可以改邮箱的用户为：", User.objects.filter(username=user.username, email=""))
        # 这种写法基本上就是只有空的用户才可以填邮箱，用户只有一次填入邮箱的机会
        User.objects.filter(username=user.username, email="").update(email=email_client)

        # 发送邮箱验证邮件
        try:
            request.user.email = email_client
            request.user.save()
        except Exception as e:
            print(e)
            logger.error(f'发送邮件出错{e}')
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})

        # 异步发送验证邮件
        verify_url = 'http://www.baidu.com'
        send_verify_email.delay(email_client, verify_url)



        return JsonResponse({'code':RETCODE.OK, 'errmsg': '已发送验证邮件'}) # 添加邮箱成功??



        # 验证邮箱



