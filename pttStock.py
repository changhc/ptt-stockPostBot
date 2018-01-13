#coding=utf-8
import telnetlib, sys, time, os, subprocess, re

###### CONSTANTS START ######
hostName = 'ptt.cc'
userId = ''
password = ''
boardName = 'test'
####### CONSTANTS END #######

###### GLOBAL VAR START ######
# when longer internet delay, adjust this variable manually
delayUnit = 0.5
pushLength = 48
pushContentList = []
###### GLOBAL VAR END ######

import requests
import json
from bs4 import BeautifulSoup
import datetime

def CrawlData():
    content = ''
    date = datetime.datetime.now().strftime('%Y%m%d')
    url_gtsm = 'https://goodinfo.tw/StockInfo/ShowBearishChart.asp?STOCK_ID=%E6%AB%83%E8%B2%B7%E6%8C%87%E6%95%B8&CHT_CAT=DATE'
    url_credit_sum = 'https://goodinfo.tw/StockInfo/ShowBearishChart.asp?STOCK_ID=%E5%8A%A0%E6%AC%8A%E6%8C%87%E6%95%B8&CHT_CAT=DATE'
    url_credit = 'http://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date=' + '20180112' # date
    header = { 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36' }
    text = requests.get(url_credit, headers=header).text
    obj = json.loads(text)
    content += (obj['creditTitle'] + '\r\n\r\n')
    content += ('{i[0]: <14}{i[1]: <10}{i[2]: <8}{i[3]: <9}{i[4]: <9}{i[5]: <1}'.format(i=obj['creditFields']) + '\r\n\r\n')
#    content += ('\t'.join(obj['creditFields'][1:]) + '\r\n')
    for idx in range(len(obj['creditList'])):
        content += ('{i[0]: <10}{i[1]: <12}{i[2]: <12}{i[3]: <12}{i[4]: <13}{i[5]: <13}'.format(i=obj['creditList'][idx]) + '\r\n')
    print(content)
#soup = BeautifulSoup(text, 'html.parser')
#print(soup.table.find_all('td'))
    '''
    tr = soup.find('tr', { 'id': 'row0'})
    tds = tr.find_all('td')
    print(tds[8].text, tds[14].text)
    '''

def CheckLatency(hostName):
    global delayUnit
    print("Measuring host latency...")
    ping = subprocess.Popen(['ping', '-c', '10', hostName], stdout = subprocess.PIPE, stderr=subprocess.STDOUT)
    res, nothing = ping.communicate()
    res = re.match(".*([0-9]+)% .*\/([0-9.]+)\/[0-9.]+\/.*", res.decode('ascii'), flags = re.DOTALL)
    delayCoeff = 18
    if res.group(1) != '0':
        delayCoeff = 15
    delayUnit = float(res.group(2)) / delayCoeff
    print("Testing loss {0} %. Avg response time {1} ms.".format(res.group(1), res.group(2)))
    
def ReadSettings():
    global userId, password, boardName
    print('Hello! I\'m PttAutoPushBoo!')
    userId = input('Please enter your user ID: ')
    password = input('Please enter your password: ')
    boardName = input('Please enter the name of the board that the post belongs to: ')
    print('Let\'s start!')

def Login(hostName, userId ,password) :
    global telnet
    telnet = telnetlib.Telnet(hostName)
    time.sleep(delayUnit)
    content = telnet.read_very_eager().decode('big5','ignore')
    if u"系統過載" in content :
        Exit(5)
        
    if u"請輸入代號" in content:
        #print ("輸入帳號中...")
        telnet.write((userId + "\r\n" ).encode('ascii'))
        time.sleep(delayUnit)
        #print ("輸入密碼中...")
        telnet.write((password + "\r\n").encode('ascii'))
        time.sleep(5 * delayUnit)
        content = telnet.read_very_eager().decode('big5','ignore')
        #print content
        if u"密碼不對" in content:
           Exit(4)
           #content = telnet.read_very_eager().decode('big5','ignore')
        if u"您想刪除其他重複登入" in content:
           print ('Removing other connections....')
           telnet.write(("y\r\n").encode('ascii'))
           time.sleep(15 * delayUnit)
           content = telnet.read_very_eager().decode('big5','ignore')
        if u"動畫播放中" in content:
           telnet.write(("\r\n" ).encode('ascii'))
           time.sleep(2 * delayUnit)
           content = telnet.read_very_eager().decode('big5','ignore')
        if u"請按任意鍵繼續" in content:
           #print ("資訊頁面，按任意鍵繼續...")
           telnet.write(("\r\n" ).encode('ascii'))
           time.sleep(2 * delayUnit)
           content = telnet.read_very_eager().decode('big5','ignore')
        if u"您要刪除以上錯誤嘗試" in content:
           print ("Erasing false attempts...")
           telnet.write(("y\r\n").encode('ascii'))
           time.sleep(5 * delayUnit)
           content = telnet.read_very_eager().decode('big5','ignore')
        if u"您有一篇文章尚未完成" in content:
           print ('Erasing undone posts....')
           # 放棄尚未編輯完的文章
           telnet.write(("q\r\n").encode('ascii'))
           time.sleep(5 * delayUnit)   
           content = telnet.read_very_eager().decode('big5','ignore')
        #print ("--- 登入完成 ---")
        
    else:
        Exit(7)

def Disconnect(error=False) :
    #if(not error):
    #    print ("登出中...")
    # q = 上一頁，直到回到首頁為止，g = 離開，再見
    telnet.write(("qqqqqqqqqg\r\ny\r\n" ).encode('ascii'))
    time.sleep(3 * delayUnit)
    #if(not error):
    #    print ("--- 登出完成 ---")
    telnet.close()

def Push(boardName, postId, pushType, pushContent):
    #print('--- 開始推文 ---')
    GoToBoard(boardName)
    #print('進入看板')
    # go to post
    telnet.write(('#').encode('ascii'))
    time.sleep(delayUnit)
    telnet.write((postId + '\r\n').encode('ascii'))
    time.sleep(delayUnit)

    content = telnet.read_very_eager().decode('big5','ignore')
    if u"找不到這個文章代碼" in content:
        Exit(2)
    elif u"本文已刪除" in content:
        Exit(3)
    #print('找到文章')

    # Shift-X
    telnet.write(('X').encode('ascii'))
    time.sleep(delayUnit)
    telnet.write(str(pushType).encode('ascii'))
    time.sleep(delayUnit)
    telnet.write((pushContent +'\r\n').encode('big5'))
    time.sleep(delayUnit)
    telnet.write(('y').encode('ascii'))
    time.sleep(delayUnit)
    #print ("--- 推文成功 ---")


def GoToBoard(boardName):
    # s 進入要發文的看板
    if not CheckBoardExists(boardName):
        Exit(1)
    telnet.write(('\r\n').encode('big5'))
    time.sleep(delayUnit)       
    telnet.write(("dd").encode('ascii'))   # in case of welcoming message
    time.sleep(2 * delayUnit)

def CheckBoardExists(boardName):
    telnet.write(('s').encode('ascii'))
    time.sleep(delayUnit)
    telnet.write(boardName.encode('big5'))
    time.sleep(2 * delayUnit)
    content = telnet.read_very_eager().decode('big5','ignore')
    if boardName in content:
        return True
    else:
        return False

def Exit(errorCode):
    print({
        1: "Cannot find this board.",
        2: "Cannot find this post.",
        3: "This post is removed.",
        4: "Wrong password or invalid account.",
        5: "The host is suffering heavy load. Try again later.",
        6: "Invalid Input File Name.",
        7: "The host may be offline now."
    }[errorCode])
    Disconnect()
    sys.exit(-1)

def main():

    ReadSettings()
    CheckLatency(hostName)
    start = time.time()
    print("Initializing...")
    Login(hostName, userId ,password)
    # post
    Disconnect()
    print("Successfully posted!")
    print("Total time: {0} sec.".format(time.time() - start))
	
#if __name__=="__main__" :
#    main()

