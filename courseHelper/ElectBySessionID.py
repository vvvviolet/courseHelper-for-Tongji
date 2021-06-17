import json
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests


class courseElect:
    def __init__(self, Ecom_User_ID, sessionid, courseCode, toEmail, fromEmail):
        self.Ecom_User_ID = Ecom_User_ID
        self.sessionid = sessionid
        self.courseCode = courseCode
        self.toEmail = toEmail
        self.fromEmail = fromEmail
        self.message = ''
        self.session = requests.session()

    def messageSend(self, string):
        msg_from = self.fromEmail
        passwd = 'zzwsqitnxoduchde'
        to = [self.toEmail]
        msg = MIMEMultipart()
        content = string
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        msg['Subject'] = "选课提醒"
        msg['From'] = msg_from
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(msg_from, passwd)
        s.sendmail(msg_from, to, msg.as_string())
        print("邮件发送成功")

    def courseElect(self):
        getRoundIdUrl = 'https://1.tongji.edu.cn/api/electionservice/student/getRounds'
        data = {
            'projectId': '1',
        }
        headers = {
            'Cookie': 'sessionid=' + self.sessionid
        }
        res = self.session.post(getRoundIdUrl, headers=headers, data=data)
        roundId = str(json.loads(res.text)['data'][0]['id'])

        getCourseInfoUrl = 'https://1.tongji.edu.cn/api/electionservice/student/getTeachClass4Limit'
        payload = {
            'roundId': roundId,
            'courseCode': courseCode,
            'studentId': Ecom_User_ID,
        }
        res = self.session.post(getCourseInfoUrl, headers=headers, params=payload)
        resJson = (json.loads(res.text))['data']
        courseName = resJson[0]['courseName']

        print('符合要求的共有' + str(len(resJson)) + '节课：')
        for i in resJson:
            print('排课信息：')
            print('名称：' + courseName)
            print('teachClassId：' + str(i['times'][0]['teachClassId']))
            print('teachClassCode：' + str(i['times'][0]['teachClassCode']))
            for j in i['timeTableList']:
                print(j)
            print('\n')

        teachClassId = input('请输入选择课的teachClassId：')
        teachClassCode = input('请输入选择课的teachClassCode：')

        data = {"roundId": roundId, "elecClassList": [
            {"teachClassId": int(teachClassId), "teachClassCode": teachClassCode, "courseCode": courseCode}],
                "withdrawClassList": []}

        electUrl = 'https://1.tongji.edu.cn/api/electionservice/student/elect'
        electResUrl = 'https://1.tongji.edu.cn/api/electionservice/student/' + roundId + '/electRes'
        self.session.post(electUrl, headers=headers, json=data)
        time.sleep(1)
        res = self.session.post(electResUrl, headers=headers)
        resJson = json.loads(res.text)
        times = 1
        while (1):
            print('第' + str(times) + '次请求：')
            if len(resJson['data']['successCourses']):
                self.messageSend(courseName + ' 选课成功' + '，共请求' + str(times) + '次')
                break
            else:
                print(res.text)
                times += 1
                self.session.post(electUrl, headers=headers, json=data)
                time.sleep(3)
                res = self.session.post(electResUrl, headers=headers)
                resJson = json.loads(res.text)

    def start(self):
        self.courseElect()


if __name__ == '__main__':
    with open('config.json', encoding='utf-8')as f:
        config = json.load(f)

    Ecom_User_ID = config['uid']
    sessionid = config['sessionid']
    courseCode = config['courseCode']
    toEmail = config['msg_to']
    fromEmail = config['msg_from']
    s = courseElect(Ecom_User_ID, sessionid, courseCode, toEmail, fromEmail)
    s.start()
