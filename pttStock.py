#coding=utf-8
import telnetlib, sys, re, subprocess, time
import requests
import json
from bs4 import BeautifulSoup
import datetime

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
header = { 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36' }
###### GLOBAL VAR END ######

def CreatePost():
    title, content = CrawlCreditTable()
    content += ('-' * 70 + '\r\n\r\n')
    content += '櫃買信用交易統計\r\n\r\n'
    content += GetGTSM()
    return title, content

def CrawlCreditTable():
    content = ''
    date = datetime.datetime.now().strftime('%Y%m%d')
    url_credit = 'http://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date=' + date
    text = requests.get(url_credit, headers=header).text
    obj = json.loads(text)
    content += (obj['creditTitle'] + '\r\n\r\n')
    content += ('{i[0]: <14}{i[1]: <10}{i[2]: <8}{i[3]: <9}{i[4]: <9}{i[5]: <1}'.format(i=obj['creditFields']) + '\r\n\r\n')
#    content += ('\t'.join(obj['creditFields'][1:]) + '\r\n')
    for idx in range(len(obj['creditList'])):
        content += ('{i[0]: <10}{i[1]: <12}{i[2]: <12}{i[3]: <12}{i[4]: <13}{i[5]: <13}'.format(i=obj['creditList'][idx]) + '\r\n')

    content += '\r\n\r\n'
    data = [
        int(obj['creditList'][2][-1].replace(',', '')) - \
            int(obj['creditList'][2][-2].replace(',', '')),
        int(obj['creditList'][1][-1].replace(',', '')) - \
            int(obj['creditList'][1][-2].replace(',', ''))
    ]
    data[0] = int(data[0] / 1000) / 100
    content += '%s\r\n' % ProcessSign(data[0], False)
    content += '%s\r\n\r\n' % ProcessSign(data[1], True)
    
    yr = int(date[:4]) - 1911
    title = '%d年%s月%s日信用交易統計\r\n' % (yr, date[4:6], date[6:])
    return title, content

def GetGTSM():
    content = ''
    date = datetime.datetime.now()
    data = CrawlGTSM(date)
    data_prev = CrawlGTSM(date - datetime.timedelta(days=1))
    data = [data[0] - data_prev[0], data[1] - data_prev[1]]
    data[0] = int(data[0] / 1000) / 100
    content += '%s\r\n' % ProcessSign(data[0], False)
    content += '%s\r\n\r\n' % ProcessSign(data[1], True)
    return content

def CrawlGTSM(date):
    date_string = date.strftime('%m/%d')
    url = 'http://www.tpex.org.tw/web/stock/margin_trading/margin_balance/margin_bal_result.php?d=%d/%s' % \
            (date.year - 1911, date_string)
    text = requests.get(url, headers=header).text
    obj = json.loads(text)
    data = [
        int(obj['tfootData_two'][-1].replace(',', '')),
        int(obj['tfootData_one'][-1].replace(',', ''))
    ]
    return data

def ProcessSign(t, isSelling):
    if isSelling:
        toks = ['券', '張']
    else:
        toks = ['資', '億']

    text = chr(21) + '[1;'
    if t < 0:
        t *= -1
        text += '32m'
        text += '%s減\t%s\t%s' % (toks[0], '{:,}'.format(t), toks[1])
    else:
        if t > 0:
            text += '31m'
        else:
            text += '37m'
        text += '%s增\t%s\t%s' % (toks[0], '{:,}'.format(t), toks[1])
    text += '%s' % chr(3)
    return text

def CheckLatency(hostName):
    global delayUnit
    print("Measuring host latency...")
    ping = subprocess.Popen(['ping', '-c', '10', hostName], stdout = subprocess.PIPE, stderr=subprocess.STDOUT)
    res, nothing = ping.communicate()
    res = re.match(".*([0-9]+)% .*\/([0-9.]+)\/[0-9.]+\/.*", res.decode('ascii'), flags = re.DOTALL)
    delayCoeff = 15
    if res.group(1) != '0':
        delayCoeff = 12
    delayUnit = float(res.group(2)) / delayCoeff
    print("Testing loss {0} %. Avg response time {1} ms.".format(res.group(1), res.group(2)))
    
def ReadSettings():
    global userId, password, boardName
    print('Hello! I\'m PttStockPoster!')
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
        #print ('ID...')
        telnet.write((userId + "\r\n" ).encode('ascii'))
        time.sleep(delayUnit)
        #print ('Pasword...')
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
           print ('Skipping Info Page...')
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
        telnet.write(('ddd').encode('ascii'))
        time.sleep(delayUnit)
        print ('--- Logged in ---')
        
    else:
        Exit(7)

def Disconnect(error=False) :
    if(not error):
        print ('Logging out...')
    # q = 上一頁，直到回到首頁為止，g = 離開，再見
    telnet.write(('qqqqqqqqqg\r\ny\r\n' ).encode('ascii'))
    time.sleep(3 * delayUnit)
    if(not error):
        print ('--- Logged out ---')
    telnet.close()

def GoToBoard(boardName):
    # s 進入要發文的看板
    if not CheckBoardExists(boardName):
        Exit(1)
    telnet.write(('\r\n').encode('big5'))
    time.sleep(delayUnit)       
    telnet.write(('gg').encode('ascii'))   # in case of welcoming message
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

def Post(boardName, title, content):
    #print('--- 開始推文 ---')
    GoToBoard(boardName)
    print('Entered the board')
    print('--- Start Posting --- ')
    telnet.write(chr(16).encode('ascii'))
    time.sleep(delayUnit)
    telnet.write('6\r\n'.encode('ascii'))
    time.sleep(delayUnit)
    telnet.write(title.encode('big5'))
    time.sleep(delayUnit)
    telnet.write((chr(25) * 3).encode('ascii'))
    time.sleep(delayUnit)

    # Write Content
    telnet.write(content.encode('big5'))
    time.sleep(10 * delayUnit)
    telnet.write(chr(24).encode('ascii'))
    time.sleep(5 * delayUnit)
    telnet.write('s\r\n'.encode('ascii'))
    time.sleep(5 * delayUnit)
    telnet.write('\r\n'.encode('ascii'))
    time.sleep(10 * delayUnit)

    print ("--- Done Posting ---")

def main():
    title, content = CreatePost()
    ReadSettings()
    CheckLatency(hostName)
    start = time.time()
    print("Initializing...")
    Login(hostName, userId ,password)
    Post(boardName, title, content)
    Disconnect()
    print("Successfully posted!")
    print("Total time: {0} sec.".format(time.time() - start))

if __name__=="__main__" :
    main()
