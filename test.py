import random

sms_code = '%06d' % random.randint(0, 999999)

print(sms_code)