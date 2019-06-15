from django.db import models

from zmeiduo.utils.models import BaseModel


class OAuthQQuser(BaseModel):

    # "users.User" 也可以写成 User, 注意不用双引号，且需要先导包
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, verbose_name="用户")
    openid = models.CharField(max_length=64, verbose_name="openid", db_index=True)

    class Meta:
        db_table = "tb_oauth_qq"
        verbose_name = "QQ登录用户数据"
        verbose_name_plural = verbose_name
