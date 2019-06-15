

# send_mall()方法介绍
# 在django.core.mail模块提供了send_mail()来发送邮件。
# 方法参数：
# send_mail(subject, message, from_email, recipient_list, html_message=None)

# subject 邮件标题
# message 普通邮件正文，普通字符串
# from_email 发件人
# recipient_list 收件人 注意是：列表 形式
# html_message 多媒体邮件正文，可以是html字符串

from celery_tasks.main import celery_app
from django.core.mail import send_mail
from django.conf import settings

# bind：保证task对象会作为第一个参数自动传入
# name：异步任务别名
# retry_backoff：异常自动重试的时间间隔 第n次(retry_backoff×2^(n-1))s
# max_retries：异常自动重试次数的上限

@celery_app.task(bind=True, name='send_verify_email', retry_backoff=3)
def send_verify_email(self, to_email, verify_url):
    subject = "好大条粉肠邮箱验证"
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   f'<p>您的邮箱为：{to_email} 。请点击此链接激活您的邮箱：</p>' \
                   f'<p><a href="{verify_url}">{verify_url}<a></p>'
    try:
        send_mail(subject, '', settings.EMAIL_FROM, [to_email], html_message=html_message)
    except Exception as e:
        print(e)
        # 有异常自动重试三次,固定写法
        raise self.retry(exc=e, max_retries=3)
