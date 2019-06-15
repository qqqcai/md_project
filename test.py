# import random
#
# sms_code = '%06d' % random.randint(0, 999999)
#
# print(sms_code)
import re

a = re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', 'qqqcai@126.com')
print(a.group())a

asd

asd