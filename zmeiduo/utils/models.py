from django.db import models


class BaseModel(models.Model):

    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True # 标记为抽象模型类，只用于继承，迁移时不会生成表单

