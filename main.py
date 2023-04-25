import time
import requests
import json
import captcha
from bs4 import BeautifulSoup
import base64
import os
import subprocess
from urllib import parse

__author__ = 'chennuo'
__Date__ = '2023/4/18-2023/4/25'

def sm2Enc(password, publicKey):
      # 获取加密后的密码
    pro = subprocess.run(f"node sm2Enc.js {password} {publicKey}", 
                         stdout=subprocess.PIPE)
    _encryptData = pro.stdout
    data = _encryptData.decode().strip()
    return data

def getCaptchaVerification(headers):
    getCaptchaUrl = "https://ids.tongji.edu.cn:8443/nidp/app/login?sid=0&sid=0/getCaptcha=1"
    checkCaptchaUrl = "https://ids.tongji.edu.cn:8443/nidp/app/login?sid=0&sid=0/checkCaptcha=1"
    for i in range(20):
        res = requests.get(getCaptchaUrl,headers=headers)
        data = res.json()['repData']
        point = captcha.crack(data)
        enc = captcha.encrypt(json.dumps(point).replace(" ", ""), data["secretKey"])
        resp = requests.post(checkCaptchaUrl,json={ "token": data["token"], "pointJson": enc },headers=headers).json()
        if resp["repCode"] == "0000":
            raw = data["token"] + "---" + json.dumps(point).replace(" ", "")
            # 对应于verify.js:543的captchaVerification
            return(captcha.encrypt(raw, data["secretKey"]))
        else:
            pass

if __name__ == '__main__':
    base = 'https://ids.tongji.edu.cn:8443/nidp/app'
    headers = {
        'Cookie':''
    }
    res = requests.get(base)

    headers['Cookie'] += ('JSESSIONID='+res.cookies.get_dict()['JSESSIONID'])
    headers['Cookie'] += '; '
    headers['Cookie'] += ('UrnNovellNidpClusterMemberId='+res.cookies.get_dict()['UrnNovellNidpClusterMemberId'])
    headers['Cookie'] += '; '

    res = requests.post('https://ids.tongji.edu.cn/nidp/app/login?id=Login&sid=0&option=credential&sid=0',headers=headers)
    soup = BeautifulSoup(res.text,features="lxml")
    # 用于加密的publicKay，被作为html的一部分返回，推测是反爬机制
    publicKey = soup.html.body.div.div.div.form.find_all('input')[2].get('value')
    captche = getCaptchaVerification(headers)

    username = '2052538'
    password = 'HCTGhctg1'
    
    # 密码加密
    encryptData = sm2Enc(password,publicKey)

    data = {
        'option': 'credential',
        'Ecom_User_ID':username,
        'Ecom_Password':encryptData,
        'Ecom_Captche':captche,
    }

    res = requests.post('https://ids.tongji.edu.cn:8443/nidp/app/login?sid=0&sid=0', data=data, headers=headers)

    headers['Cookie'] += ('JSESSIONID='+res.cookies.get_dict()['JSESSIONID'])
    headers['Cookie'] += '; '
    res=requests.get('https://ids.tongji.edu.cn:8443/nidp/app?sid=0',headers=headers)
    
    # authz
    res=requests.get('https://ids.tongji.edu.cn:8443/nidp/oauth/nam/authz?scope=profile&response_type=code&redirect_uri=https://1.tongji.edu.cn/api/ssoservice/system/loginIn&client_id=5fcfb123-b94d-4f76-89b8-475f33efa194'
                     ,headers=headers
                     ,allow_redirects=False)
    redirect_url = res.headers.get('location')
    # print(redirect_url)
    
    #authz和loginIn之间差token

    headers['Cookie'] += ('_PA_SDK_SSO_='+res.cookies.get_dict()['_PA_SDK_SSO_'])
    headers['Cookie'] += '; '

    # loginIn
    res = requests.get(redirect_url,headers=headers,allow_redirects=False)
    location=res.headers.get('Location')




    # ssologin
    parsedLocation=parse.urlparse(location).query.split('&')
    print(parsedLocation)

    token=parsedLocation[0][6:]
    uid=parsedLocation[1][4:]

    headers['cookie']=headers['Cookie']
    print(token)
    print(uid)
    jsonData={
        'token':token,
        'uid':uid,
        'ts':str(int(time.time()*1000))
    }
    print(jsonData)
    print(headers)
    res = requests.post('https://1.tongji.edu.cn/api/sessionservice/session/login',json=jsonData,headers=headers)

    print(res.headers)
    print(res.cookies)
   

