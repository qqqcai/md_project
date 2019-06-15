import re

from django.conf import settings  # 注意这样导就可以拿到manage.py中指定的settings文件
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views import View
from django_redis import get_redis_connection

from oauth.models import OAuthQQuser
from oauth.utils import generate_openid_signature, check_openid_sign # 自己创建的加解密工具
from users.models import User
from zmeiduo.utils.response_code import RETCODE

from QQLoginTool.QQtool import OAuthQQ


class OAuthURLView(View):

    def get(self, request):
        next_url = request.GET.get("next", "/") # 这个位置最好给默认值

        # print(settings.QQ_CLIENT_ID, settings.QQ_CLIENT_SECRET, settings.QQ_REDIRECT_URI)
        # 获取QQ登录页面网址
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next_url)

        login_url = oauth.get_qq_url()

        print(f"准备登录让前台跳转{login_url}")
        # 暂时不知道errmsg有什么用
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


class OAuthUserView(View):

    def get(self, request):
        print(f"整个回调地址={request.get_full_path()}")
        print(f"回调地址中获取{request.GET}")
        # 获取回来的 Authorization /ɔːθəraɪ'zeɪʃ(ə)n/ Code
        code = request.GET.get('code')
        if not code:
            return redirect('/login/')

        # 拿着 Authorization Code 获取 access_token
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            access_token = oauth.get_access_token(code)  # 问QQ服务器拿access_token
            openid = oauth.get_open_id(access_token)  # 拿着 access_token 向QQ服务器请求 openid
        except Exception as e:
            # logger.error(e)
            print(f"获取QQ openid出错{e}")
            return HttpResponseServerError('OAuth2.0认证失败')  # 只是空白页面显示这几个字

        # 判断数据库中，这个openid之前在这里有没有绑定了用户，有就帮他登录
        try:
            oauth_user = OAuthQQuser.objects.get(openid=openid)
        except:  #  OAuthQQUser.DoesNotExist 讲义上
            # 没有绑定就 拿 openid(注意加密和解密) 放在oauth_callback模版中让用户填完其他注册数据
            openid = generate_openid_signature(openid)
            return render(request, 'oauth_callback.html', {"openid": openid})
        else:
            qq_user = oauth_user.user
            print(f"绑定的改对象为{qq_user}")
            login(request, qq_user)
            next_url = request.GET.get("state", "/")
            response = redirect(next_url)
            response.set_cookie("username", qq_user.username, max_age=3600 * 24 * 15)
            return response

    def post(self, request):
        # 用户带着openid和帐号 密码 手机 验证码等数据一并发过来
        mobile = request.POST.get("mobile")
        password = request.POST.get("password")
        # image_code = request.POST.get("image_code")
        sms_code_client = request.POST.get("sms_code")
        openid = request.POST.get("openid")

        if not all([mobile, password, sms_code_client, openid]):
            context = {
                "openid": openid,
                "qq_login_errmsg": "缺少必填项",
            }
            return render(request, 'oauth_callback.html', context)

        # 校验各种数据
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('请输入正确的手机号码')

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')

        if not re.match(r'^[0-9]{6}$', sms_code_client):
            return HttpResponseForbidden('请输入正确的短信验证码')


        redis_conn = get_redis_connection('verify_code')

        sms_code_server = redis_conn.get(f"sms_{mobile}")
        if sms_code_server is None:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效的短信验证码', 'openid': openid})

        redis_conn.delete(f"sms_{mobile}")
        if sms_code_server.decode() != sms_code_client: # 纯数字不用转小写
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '输入的短信验证码有误', 'openid': openid})

        openid = check_openid_sign(openid) # 解密openid，并判断是否有效
        if not openid: # 如果openid只可以用一次，那为什么要返回绑定页面？？
            return render(request, 'oauth_callback.html', {'openid_errmsg': '无效的openid'})

        # 判断这个帐号 和 手机号 是否存在，存在就验证一下密码是否对，不对返回错误，对就继续
        try:
            user = User.objects.get(mobile=mobile)
            # print(f'{mobile}密码为{}')
        except: # except User.DoesNotExist:
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            print(f"密码校验{user.check_password(password)}")
            if not user.check_password(password): # django是不是没有获取密码？？
                return render(request, 'oauth_callback.html', {'qq_login_errmsg': '用户名或密码错误'})

        try:
            # 密码对就将这个帐号绑定openid( 在OAuthQQuser中创建 user = create())
            OAuthQQuser.objects.create(user=user, openid=openid) # 不用create_user
        except: #讲义上为什么DatabaseError,不用是否可以？？
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})

        login(request, user)

        next_url = request.GET.get("state")
        print(f'注册前网址：｛next_url｝')
        response = redirect(next_url)
        response.set_cookie("username", user.username, max_age=3600*24*15)
        # login()保持登录状态
        return response
