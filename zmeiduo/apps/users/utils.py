import re

from django.contrib.auth.backends import ModelBackend
from users.models import User

def get_user_by_account(account):

    try:
        if re.match(r"^1[3-9]\d{9}$", account):
            user = User.objects.get(mobile=account)
        elif re.match(r"^[A-Za-z\d]+([-_.][A-Za-z\d]+)*@([A-Za-z\d]+[-.])+[A-Za-z\d]{2,5}$", account):
            user = User.objects.get(email=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist: # 不懂这个
        return None

    return user

class UsernameMobileAuthBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方法，实现多账号登录
        :param request: 请求对象
        :param username: 用户名
        :param password: 密码
        :param kwargs: 其他参数
        :return: user
        """
        user = get_user_by_account(username)
        print(user)
        if user and user.check_password(password):
            return user

