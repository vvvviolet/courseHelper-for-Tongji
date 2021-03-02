import base64
import time
import json
import requests
from PIL import Image
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class courseElect:
    def __init__(self,Ecom_User_ID,Ecom_Password,courseCode,toEmail,fromEmail):
        self.Ecom_User_ID = Ecom_User_ID
        self.Ecom_Password = Ecom_Password
        self.courseCode = courseCode
        self.toEmail = toEmail
        self.fromEmail = fromEmail
        self.message = ''
        self.session=requests.session()

    def messageSend(self,string):
        msg_from = self.fromEmail
        passwd = 'zzwsqitnxoduchde' 
        to= []
        to.append(self.toEmail) 
        msg = MIMEMultipart()
        content=string
        msg.attach(MIMEText(content,'plain','utf-8'))
        msg['Subject']="选课提醒"
        msg['From']=msg_from
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(msg_from, passwd)
        s.sendmail(msg_from,to,msg.as_string())
        print("邮件发送成功")

    def login(self):
        startUrl = 'https://ids.tongji.edu.cn:8443/nidp/app/login?id=2811&sid=1&option=credential&sid=1'
        res = self.session.get(startUrl)
        codeUrlReq = "https://ids.tongji.edu.cn:8443/nidp/app/login?sid=2&sid=2&flag=true"
        codeUrl =self.session.get(codeUrlReq)
        decodedCodeUrl = base64.b64decode(codeUrl.text[len("data:image/jpg;base64,"):-1] + "=")
        with open('code.jpg', 'wb')as f:
            f.write(decodedCodeUrl)
        im = Image.open('./code.jpg')
        im.show()
        code = input("请输入验证码：")

        loginUrl = "https://ids.tongji.edu.cn:8443/nidp/app/login?sid=0&sid=0"
        data = {
            'option': 'credential',
            'Ecom_User_ID': self.Ecom_User_ID,
            'Ecom_Password': self.Ecom_Password,
            'Ecom_code': code,
        }

        res = self.session.post(loginUrl, data=data)
        url='https://ids.tongji.edu.cn:8443/nidp/oauth/nam/authz'
        payload = {'scope': 'profile',
        'response_type': 'code',
        'redirect_uri': 'https://1.tongji.edu.cn/api/ssoservice/system/loginIn',
        'client_id': '5fcfb123-b94d-4f76-89b8-475f33efa194',#需改动
        }
        headers={
            'Cookie':'JSESSIONID='+res.cookies.get(name='JSESSIONID')+';UrnNovellNidpClusterMemberId='+self.session.cookies.get(name='UrnNovellNidpClusterMemberId'),
        }

        res=self.session.get(url,params=payload,headers=headers,allow_redirects=False)
        url=res.headers.get('Location')
        res=self.session.get(url,allow_redirects=False,headers=headers)
        url=res.headers.get('Location')
        token=url[url.find('=')+1:url.find('&')]
        ts=url[url.find('ts')+3:]

        data={
            'token':token,
            'uid':Ecom_User_ID,
            'ts':ts,
        }
        url='https://1.tongji.edu.cn/api/sessionservice/session/login'
        res=self.session.post(url,allow_redirects=False,headers=headers,data=data)
        
    def courseElect(self):
        getRoundIdUrl='https://1.tongji.edu.cn/api/electionservice/student/getRounds'
        data={
            'projectId': '1',
        }
        res=self.session.post(getRoundIdUrl,data=data)
        roundId=str(json.loads(res.text)['data'][0]['id'])

        getCourseInfoUrl='https://1.tongji.edu.cn/api/electionservice/student/getTeachClass4Limit'
        payload={
            'roundId': roundId,
            'courseCode': courseCode,
            'studentId': Ecom_User_ID,
        }
        res=self.session.post(getCourseInfoUrl,params=payload)
        resJson=(json.loads(res.text))['data']
        courseName=resJson[0]['courseName']

        print('符合要求的共有'+str(len(resJson))+'节课：')
        for i in resJson:
            print('排课信息：')
            print('名称：'+courseName)
            print('teachClassId：'+str(i['times'][0]['teachClassId']))
            print('teachClassCode：'+str(i['times'][0]['teachClassCode']))
            for j in i['timeTableList']:
                print(j)
            print('\n')

        teachClassId=input('请输入选择课的teachClassId：')
        teachClassCode=input('请输入选择课的teachClassCode：')
        #data={"roundId":5133,"elecClassList":[{"teachClassId":1111111124851507,"teachClassCode":"11006002","courseCode":"110060"}],"withdrawClassList":[]}
        data={"roundId":roundId,"elecClassList":[{"teachClassId":int(teachClassId),"teachClassCode":teachClassCode,"courseCode":courseCode}],"withdrawClassList":[]}

        electUrl='https://1.tongji.edu.cn/api/electionservice/student/elect'
        electResUrl='https://1.tongji.edu.cn/api/electionservice/student/'+roundId+'/electRes'
        res=self.session.post(electUrl,json=data)
        time.sleep(1)
        res=self.session.post(electResUrl)
        resJson=json.loads(res.text)
        times=1
        while(1):
            print('第'+str(times)+'次请求：')
            if(len(resJson['data']['successCourses'])):
                self.messageSend(courseName+' 选课成功'+'，共请求'+str(times)+'次')
                break
            else:
                print(res.text)
                times+=1
                res=self.session.post(electUrl,json=data)
                time.sleep(3)
                res=self.session.post(electResUrl)
                resJson=json.loads(res.text)

    def start(self):
        self.login()
        self.courseElect()

if __name__ == '__main__':
    with open('config.json',encoding='utf-8')as f:
        config = json.load(f)

    Ecom_User_ID = config['uid']
    Ecom_Password = config['password']
    courseCode = config['courseCode']
    toEmail=config['msg_to']
    fromEmail=config['msg_from']
    s = courseElect(Ecom_User_ID,Ecom_Password,courseCode,toEmail,fromEmail)
    s.start()