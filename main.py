import requests
import json
import captcha
from bs4 import BeautifulSoup
import base64
import os
import subprocess
from urllib import parse
__author__ = 'chennuo'
__Date__ = '2023/4/18'

def getCaptchaVerification(session: requests.sessions.Session):
    getCaptchaUrl = "https://ids.tongji.edu.cn:8443/nidp/app/login?sid=0&sid=0/getCaptcha=1"
    checkCaptchaUrl = "https://ids.tongji.edu.cn:8443/nidp/app/login?sid=0&sid=0/checkCaptcha=1"
    for i in range(20):
        res = session.get(getCaptchaUrl)
        data = res.json()['repData']
        point = captcha.crack(data)
        enc = captcha.encrypt(json.dumps(point).replace(" ", ""), data["secretKey"])
        resp = session.post(checkCaptchaUrl,json={ "token": data["token"], "pointJson": enc }).json()
        if resp["repCode"] == "0000":
            # print(json.dumps(point).replace(" ", ""))
            raw = data["token"] + "---" + json.dumps(point).replace(" ", "")
            # 对应于verify.js:543的captchaVerification
            return(captcha.encrypt(raw, data["secretKey"]))
        else:
            print(f"Trial {i} failed")

if __name__ == '__main__':
    baseurl = "https://ids.tongji.edu.cn:8443/nidp/app/login?id=Login&sid=1&option=credential&sid=1"
    base = 'https://ids.tongji.edu.cn:8443'
    session = requests.session()
    res = session.get(baseurl, allow_redirects=False)
    soup = BeautifulSoup(res.text,features="lxml")
    # 用于加密的publicKay，被作为html的一部分返回，推测是反爬机制
    publicKey = soup.html.body.div.div.div.form.find_all('input')[2].get('value')
    # print(publicKey)
    captche = getCaptchaVerification(session)
    # print(captche)
    username = '2052538'
    password = 'HCTGhctg1'
    
    # 获取加密后的密码
    pro = subprocess.run(f"node sm2Enc.js {password} {publicKey}", stdout=subprocess.PIPE)
    _encryptData = pro.stdout
    # 转一下格式
    encryptData = _encryptData.decode().strip()
    # print(encryptData)
    data = {
        'Ecom_User_ID':username,
        'Ecom_Password':encryptData,
        'Ecom_Captche':captche,
        'option': 'credential',
    }
    # print(data)
    res = session.post('https://ids.tongji.edu.cn:8443/nidp/app/login?sid=0&sid=0', data=data, allow_redirects=False)
    res = session.get('https://1.tongji.edu.cn/api/ssoservice/system/loginIn')
    soup = BeautifulSoup(res.text,features="lxml")
    print(res.text)
    redirect_url = soup.html.body.form.get('action')
    redirect_url = parse.unquote(redirect_url)
    print(base+redirect_url)
    redirect_url = base+redirect_url
    res = session.get(redirect_url,allow_redirects=False)
    print(res.text)

