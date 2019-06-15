from random import randint
from django.views import View
from django.http import HttpResponse, JsonResponse
from django_redis import get_redis_connection

from . import constants
from verifications.libs.captcha.captcha import captcha
from zmeiduo.utils.response_code import RETCODE
# from celery_tasks.sms.tasks import send_sms_code


class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        """
        :param request: 请求对象
        :param uuid: 唯一标识图形验证码属于用户
        :return: image/jpg
        """
        # 生成图片验证码 name唯一标识 text是校验码的文字，image是2进制图片
        name, text, image = captcha.generate_captcha()

        # 保存图片验证码, "verify_code"在setting中设定
        redis_conn = get_redis_connection("verify_code")
        # 第2个参数是有效时间
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 响应图片验证码
        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    """发送短信验证码"""

    def get(self, request, mobile):

        redis_conn = get_redis_connection("verify_code")
        send_flag = redis_conn.get(f"send_flag_{mobile}")
        if send_flag:
            sms_code_delay = redis_conn.ttl(f"send_flag_{mobile}")
            print("短信再获取剩余时间：", sms_code_delay)
            print(type(sms_code_delay))
            # 返回多少秒，让体验更好点
            return JsonResponse({'code':RETCODE.THROTTLINGERR, 'errmsg':"获取短信验证码过于频繁，请稍后再试", 'sms_code_delay':sms_code_delay})

        # 获取参数
        image_code_client = request.GET.get("image_code")
        uuid = request.GET.get("uuid")

        # 判断参数是否齐全
        if not all([image_code_client, uuid]):
            return JsonResponse({"code": RETCODE.NECESSARYPARAMERR, "errmsg": "缺少必要的参数"})

        # 读取数据库里的image_code 和客户填写的来对比，有问题就返回
        image_code_server = redis_conn.get("img_%s" % uuid)

        if image_code_server is None:
            return JsonResponse({"code": RETCODE.IMAGECODEERR, "errmsg": "图形验证码失效"})

        # 删除图形验证码, 防止恶意验证
        redis_conn.delete("img_%s" % uuid)

        if image_code_server.decode().lower() != image_code_client.lower():
            return JsonResponse({"code": RETCODE.IMAGECODEERR, "errmsg": "图形验证码错误"})


        # 生成6位随机码
        sms_code = "%06d" % randint(0, 999999)

        # 用队列 保存短信验证码
        pl = redis_conn.pipeline()
        pl.setex(f"sms_{mobile}", constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex(f"send_flag_{mobile}", constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        print(f"生成了短信随机码 {sms_code} ")
        # 向mobile号码发送短信验证码

        # sendTemplateSMS(手机号, [短信验证码, 短信中提示的过期时间-分钟], 容联云的模版)
        # 原本没通过Celery的用这个
        # result = sendTemplateSMS(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], constants.SEND_SMS_TEMPLATE_ID)

        # 用Celery的用这个
        # send_sms_code.delay(mobile, sms_code)  # 生产任务
        return JsonResponse({"code": RETCODE.OK, "errmsg": "发送短信成功"})
