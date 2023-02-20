import json
import time
import requests

electUrl = 'https://1.tongji.edu.cn/api/electionservice/student/elect'
electResUrl = 'https://1.tongji.edu.cn/api/electionservice/student/5276/electRes'

cookies={"sessionid":""}
data={}

times = 1
resJson = {}
while (1):
    print('第' + str(times) + '次请求：')
    times += 1
    res=requests.post(electUrl,cookies=cookies,json=data)
    print(res.text)
    time.sleep(3)
    res = requests.post(electResUrl, cookies=cookies)
    resJson = json.loads(res.text)
    print(resJson)