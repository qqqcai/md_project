# -*- coding:utf-8 -*-

from verifications.libs.yuntongxun.CCPRestSDK import REST

# 说明：主账号，登陆云通讯网站后，可在"控制台-应用"中看到开发者主账号ACCOUNT SID
_accountSid = '8a216da86b2bc78f016b4115b3400bae'

# 说明：主账号Token，登陆云通讯网站后，可在控制台-应用中看到开发者主账号AUTH TOKEN
_accountToken = '96dd4ae48b884c0a8e70b8b991e75d2d'

# 请使用管理控制台首页的APPID或自己创建应用的APPID
# _appId = '8a216da86b2bc78f016b4115b3a00bb5' # 这个首页APPID
_appId = '8a216da86b2bc78f016b411a23f60bb9'  # 这是应用里的APPID

# 说明：请求地址，生产环境配置成app.cloopen.com
# _serverIP = 'sandboxapp.cloopen.com'
_serverIP='app.cloopen.com'


# 说明：请求端口 ，生产环境为8883
_serverPort = "8883"

# 说明：REST API版本号保持不变
_softVersion = '2013-12-26'

# 云通讯官方提供的发送短信代码实例
# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
# @param $tempId 模板Id
def sendTemplateSMS(to, datas, tempId):
    # 初始化REST SDK
    rest = REST(_serverIP, _serverPort, _softVersion)
    rest.setAccount(_accountSid, _accountToken)
    rest.setAppId(_appId)

    result = rest.sendTemplateSMS(to, datas, tempId)
    # print(result)
    for k, v in result.items():

        if k == 'templateSMS':
            for k, s in v.items():
                # print('%s:%s' % (k, s))
                pass
        else:
            pass
            # print('%s:%s' % (k, v))

if __name__ == '__main__':
    # 注意： 测试的短信模板编号为1
    sendTemplateSMS('13590463362', ['709394', 5], 1)