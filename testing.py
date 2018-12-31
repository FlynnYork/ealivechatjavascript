#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import json
import time
import base64 # 生成加密验证token
import urllib # 调用urlencode
import random
import requests
import platform         # 系统识别
# import threading      # 多线程
import multiprocessing  # 多进程
from PIL import Image   # 显示验证码
from pytesseract import *
from retrying import retry
import sys
if platform.system() == 'Windows':
    '''windows 命令行模式能正常显示中文，必须填写reload(sys)'''
    reload(sys)
    sys.setdefaultencoding('GB18030') #字库比较完整
from YDMHTTP import YDM, report



# print response.status_code    # 打印状态码
# print response.url            # 打印请求url
# print response.headers        # 打印头信息
# print response.cookies        # 打印cookie信息
# print response.text           # 以文本形式打印网页源码
# print response.content        # 以字节流形式打印
# print response.history        # 打印出所有跳转的网址记录
# allow_redirects=false         # 是否允许这个URL重定向到下个URL


'''避免warning级别的警告(不显示)'''
requests.packages.urllib3.disable_warnings()
'''设置超时和最大尝试次数'''
s = requests.Session()  # 开启会话, 所有相同的请求直接共享cookies, headers
a = requests.adapters.HTTPAdapter(max_retries=5) # 挂载适配器
s.mount('http://', a)   # 此会话中适用所有http请求
s.mount('https://', a)  # 此会话中适用所有https请求
s.verify = False  # 所有相同实例会话不再校验SSL

def sysFilePath(): # 指定不同系统的文件存取路径
    global filePath
    if platform.system() == 'Windows':
        filePath = 'C:/ea/'
    elif platform.system() == 'Darwin':
        filePath = ''
    else:
        print 'cannot found sysFilePath, Please specify a path.'
    # print filePath
    return filePath
def printOut(value): # 设置特殊符号或者中文在Windows控制台中显示 #设置中文和特殊字符在Windows下正常显示
    try:
        '''
        Python明文为Unicode，类似 u'\u2122\u300a\u6230'编码开头已定义为UTF-8
        '''
        print value 
    except:
        '''
        Windows命令行控制台显示，ignore忽略gbk中不含的特殊字符比如右上角TM贸易符号
        '''
        print value.encode('gbk','ignore')
def readtext(): # 读取文档
    file_obj = open(sysFilePath()+'game.txt')
    all_lines = file_obj.readlines()
    allgame=[]
    for line in all_lines:
        try:
            game = user_info(line)
            allgame.append(game)
        except:
            print 'this line is space or format incorrect. %s'%line
    file_obj.close()
    for m,n,k,j in allgame:
        print '%s %s %s %s'%(m,n,k,j)
    return allgame
def mycardAccount(paymentContent):  # 提取MyCard付费账户信息
    payment_account = paymentContent.replace('\r',' ').replace('\n',' ').replace('\t',' ')#去掉回车符，换行符，制表符  
    payment_account = re.sub(ur'[帳賬號密碼秘注册账户帐号登录陆密码这是第一个邮箱已未读橘子我的/，：；。,:; ]+', " ", payment_account) #最后一位是空格过滤
    myaccount = payment_account.split(' ')[0]
    mypwd = payment_account.split(' ')[1]
    secCode = payment_account.split(' ')[2]     
    
    print '\nmycard account\t %s\nmycard password\t %s\nmycard secCode\t %s\n'%(myaccount,mypwd,secCode)
    return myaccount, mypwd, secCode
def user_info(userContent): # 提取购买游戏的账户信息
    '''python默认使用unicode作为解码'''
    # user_account    = userContent.decode('gbk')  #从命令行输入使用gbk解码成unicode
    user_account    = userContent.decode('utf-8')  #从文本读取使用utf-8解码成unicode
    '''先将回车符，换行符，制表符都换成空格再用RE方法去除多余空格'''
    user_account    = user_account.replace('\r','').replace('\n',' ').replace('\t',' ') 
    user_account    = re.sub(ur'[帳賬號密碼秘注册账户帐号登录陆密码这是第一个邮箱已未读橘子我的/，：；。,:; ]+', " ", user_account) #最后一位是空格过滤
    user_account    = user_account.strip(' ')  # 去掉首尾空格
    account         = str(user_account.split(' ')[0])  # unicode设置成str类型，不然云打码不识别
    accountPwd      = str(user_account.split(' ')[1])
    gameEdition     = user_account.split(' ')[2].lower() # 使用lower先将游戏版本的英文字符转为小写
    try:
        gateCountry = user_account.split(' ')[3].lower() # 临时切换激活区域代码hk,tw
    except:
        gateCountry = ''
    return account, accountPwd, gameEdition, gateCountry
def gamedata(gameEdition):  # 字典集，游戏offerId，城市，货币
 
    game    = {

                u'圣歌标准':                {'offerId':'Origin.OFR.50.0002745', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'圣歌豪华':                {'offerId':'Origin.OFR.50.0002752', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'战地5标准':           {'offerId':'Origin.OFR.50.0002862', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'战地5豪华':           {'offerId':'Origin.OFR.50.0002874', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'战地5豪华升级':         {'offerId':'Origin.OFR.50.0002818', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'fifa19标准':            {'offerId':'Origin.OFR.50.0002732', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'fifa19终极':            {'offerId':'Origin.OFR.50.0002771', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'fifa19绿点1.2万':        {'offerId':'Origin.OFR.50.0002571', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'fifa19绿点4600':        {'offerId':'Origin.OFR.50.0002570', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'fifa19绿点2200':        {'offerId':'Origin.OFR.50.0002569', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'fifa19绿点1600':        {'offerId':'Origin.OFR.50.0002568', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'fifa19绿点1050':        {'offerId':'Origin.OFR.50.0002567', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'fifa19绿点750':     {'offerId':'Origin.OFR.50.0002566', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'fifa19绿点500':     {'offerId':'Origin.OFR.50.0002560', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'fifa19绿点250':     {'offerId':'Origin.OFR.50.0002565', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'fifa19绿点100':     {'offerId':'Origin.OFR.50.0002564', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'战地1标准':           {'offerId':'Origin.OFR.50.0000557', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'战地1终极':           {'offerId':'Origin.OFR.50.0002321', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'战地1高级会员':         {'offerId':'Origin.OFR.50.0001581', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'20标准':                {'offerId':'Origin.OFR.50.0001684', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'20豪华':                {'offerId':'Origin.OFR.50.0002167', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'20豪华升级包':         {'offerId':'Origin.OFR.50.0002308', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'质量效应2标准':         {'offerId':'Origin.OFR.50.0001536', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'星战2标准':           {'offerId':'Origin.OFR.50.0002022', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'星战1标准':           {'offerId':'Origin.OFR.50.0001211', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'fifa18标准':            {'offerId':'Origin.OFR.50.0001974', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'战地4标准':           {'offerId':'OFB-EAST:109546867',    'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'战地4豪华':           {'offerId':'OFB-EAST:109552316',    'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'战地硬仗标准':          {'offerId':'Origin.OFR.50.0000426', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'战地硬仗终极':          {'offerId':'Origin.OFR.50.0000846', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'fifa18标准':            {'offerId':'Origin.OFR.50.0001974', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'19标准':                {'offerId':'Origin.OFR.50.0000994', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'19豪华':                {'offerId':'Origin.OFR.50.0001006', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'19豪华升级包':         {'offerId':'Origin.OFR.50.0000992', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'镜之边缘2标准':         {'offerId':'Origin.OFR.50.0001000', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'花园战争2标准':         {'offerId':'Origin.OFR.50.0000786', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'花园战争2豪华':         {'offerId':'Origin.OFR.50.0001051', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'逃出生天':                {'offerId':'Origin.OFR.50.0002490', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},
                u'极品飞车20所有车型包': {'offerId':'Origin.OFR.50.0002651', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'}, #299twd
                u'极品飞车20好运谷':       {'offerId':'Origin.OFR.50.0002428', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'}, #40hk 179twd
                u'极品18标准':        {'offerId':'OFB-EAST:109550809', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'}, #599twd
                u'极品18完全':        {'offerId':'Origin.OFR.50.0000677', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'}, #240hk
                u'泰坦2终极':           {'offerId':'Origin.OFR.50.0002303', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'}, #240hk
                u'龙腾3标准':           {'offerId':'OFB-EAST:51937', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'}, #599twd
                u'龙腾3豪华':           {'offerId':'OFB-EAST:1000032', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'}, #599twd
                u'龙腾3终极':           {'offerId':'Origin.OFR.50.0001131', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'}, #599twd
                u'模拟4标准':         {'offerId':'OFB-EAST:109552299', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'模拟4豪华':         {'offerId':'OFB-EAST:109552414', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'模拟4星梦起飞':         {'offerId':'SIMS4.OFF.SOLP.0x0000000000030553', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'模拟4春夏秋冬':         {'offerId':'SIMS4.OFF.SOLP.0x000000000002E2C7', 'currencyCode':'HKD', 'countryCode':'HK', 'COUPON':'No'},
                u'模拟4丛林探险':         {'offerId':'SIMS4.OFF.SOLP.0x000000000002B073', 'currencyCode':'TWD', 'countryCode':'TW', 'COUPON':'No'},

                }

    offerId = game[gameEdition]['offerId']
    countryCode = game[gameEdition]['countryCode']
    currencyCode = game[gameEdition]['currencyCode']
    couponStatus = game[gameEdition]['COUPON']
    payload = str({"offers":{"offer":[{"offerId":"%s","quantity":1}]},"bundleType":"NONE_BUNDLE","bundlePromotionRuleId":""})%offerId
    payload = eval(payload) #使用eval将字符转为字典
    offerId = payload['offers']['offer'][0]['offerId'] # 显示完整的offerId值
    print '\nofferId is %s\ncountryCode is %s, and currencyCode is %s\n'%(offerId,countryCode,currencyCode) # 用户信息设置
    '''有折扣则显示，没有折扣显示为空'''
    print 'couponStatus===>%s'%couponStatus if couponStatus == 'Yes' else ''
    return countryCode, currencyCode, payload, offerId, couponStatus
def CaptchaTotext(filePath):  # 图片识别函数
    if platform.system() == 'Windows':
        '''使用pytesseract 和PIL方法识别简单图片验证码'''
        img = Image.open(filePath)
        img_grey = img.convert('L') #灰度

        threshold = 140
        table = []
        for j in range(256):
            if j < threshold:
                table.append(0)
            else:
                table.append(1)
        img_out = img_grey.point(table, '1')

        text = image_to_string(img_grey)  # 将图片转成字符串
        # text = re.sub('\.|©|-|:|\ |°|\||;', '',text) #过滤特殊字符
        text = re.findall(r'\d+',text)[0] # 只要数字
        Captcha = text
        print 'Captcha Code: %s'%Captcha
        return Captcha #使用return返回，方便其他函数调用这个值

    # elif platform.system() == 'Darwin':
    else:
        '''
        使用云打码，同时注册用户和开发者
        http://www.yundama.com
        '''
        cid, Captcha = YDM(filePath)
        '''上传验证码id复查'''
        report(cid)
        return Captcha
def Create_html_page(htmldata): # 生成网页格式
    print '\n------------------------------------------\nEnd script and show webpage\n------------------------------------------\n'
    '''生成网页数据'''
    # reg_17 = reg_17.json()

    email = htmldata['email']
    orderNumber = htmldata['orderNumber']
    myCardPoint= htmldata['myCardPoint']
    thumbnail = htmldata['products'][0]['thumbnail']
    name = htmldata['products'][0]['name']
    '''FIFA19绿点等无gameEditionTypeFacet，因此使用异常处理'''

    try:
        typevalue = htmldata['products'][0]['gameEditionTypeFacet']
        gameEdition = {'Standard Edition':u'標準版', 'Deluxe Edition':u'豪華版', 'Ultimate Edition':u'終極版', 'Revolution Edition':u'革命'}
        gameEdition = gameEdition[typevalue]
        print typevalue
        print gameEdition
    except:
        print 'gameEdition is not included. Pass.'
        # 设置为空格
        gameEdition = ' '
    
    

    print email
    print orderNumber
    print myCardPoint
    # print thumbnail # 不要输出显示
    
    printOut(name) #由于可能有特殊符号™TM符号，windows命令行不显示utf-8编码，调用设置好的函数printOut
    

    html = u''' 

    <html lang="zh"><head>
        <link rel="icon" type="image/png" href="data:image/png;base64,iVBORw0KGgo=">
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
        <title>Checkout | Origin</title>
        <noscript>Your browser does not support JavaScript!</noscript>
        <meta http-equiv="Cache-Control" content="NO-CACHE">
        <meta http-equiv="Content-type" content="text/html;charset=UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, minimum-scale=1, maximum-scale=1">


    <link rel="stylesheet" type="text/css" href="https://rawcdn.githack.com/FlynnYork/ealivechatjavascript/ec4776a49bd25a356ed72f11bcdd8b67441e3179/otk.v_1541401314.min.css">
    <link rel="stylesheet" type="text/css" href="https://rawcdn.githack.com/FlynnYork/ealivechatjavascript/ec4776a49bd25a356ed72f11bcdd8b67441e3179/origin_zh_tw.v_1541401314.min.css">
    <style></style></head>
    <body><div class="checkout-content otkmodal-content"><div class="otkmodal-header"><h4 class="otkmodal-title otktitle-2" id="title">太棒了！感謝您的購買！</h4></div><div class="otkmodal-body post-points-purchase"><div id="orderNumber"><p class="otkc order-confirmation-text">收據會以電子郵件寄送到: <strong>%s</strong>. <a app="download" href="https://www.origin.com/zh_TW/download" class="otka">下載</a>或啟動 Origin 以進行遊玩。</p><p class="otkc order-confirmation-text"><a href="https://myaccount.ea.com/cp-ui/orderhistory/index" class="otka">檢視訂購記錄</a></p><div class="cart-total-price clearfix post-purchase-price"><div class="cart-tax clearfix"><div class="cart-tax-label"><h4 class="otktitle-4"><strong>訂購編號</strong></h4></div><div class="cart-tax-cost"><h4 class="otkc">%s</h4></div></div><div class="cart-total clearfix"><div class="cart-total-label"><h4 class="otktitle-4"><strong>總計</strong></h4></div><div class="cart-total-cost"><h4 class="otktitle-2">%s MyCard 點數</h4></div></div></div></div><div class="what-you-purchased"><ul class="cart"><li class="cart-item has-poster clearfix"><!--the img should be %s, current use fake img for viewing--><img class="cart-item-poster cart-item-poster-confirmation" src="%s" onerror="javascript:this.src='https://eaassets-a.akamaihd.net/statics_lockbox/dist/origin/assets/images/default_thumbnail.v_1541401314.png'"><div class="cart-item-details has-download-action clearfix"><div class="cart-item-details-wrapper clearfix"><h4 class="otkc"><strong>%s</strong></h4><h5 class="otkc edition-details">%s</h5></div></div></li></ul></div></div><div class="otkmodal-footer clearfix" style="display: none;"></div><div id="ProcessLoading" class="otkloader-bg"><div class="otkloader otkloader-light"></div></div></div>


     '''%(email,orderNumber,myCardPoint,thumbnail,thumbnail,name,gameEdition)


    htmlPath = sysFilePath()+'orderHTML/%s.html'%orderNumber
    print htmlPath

    with open( htmlPath,'wb' ) as f: #with as语法直接生成f文件
        f.write(html.encode('UTF-8')) #使用UTF-8编码输出，不编码就是乱码

    '''
    显示网页：
    iOS手机使用ui,os命令，直接显示网页 iOS系统叫Darwin
    '''
    if platform.system() == 'Darwin':
        import ui,os # 读取网页文件,ui命令只限pythonista
        iOS_file_path = htmlPath
        iOS_file_path = os.path.abspath(iOS_file_path)
        w = ui.WebView()
        w.load_url(iOS_file_path)
        w.present()
    else:
        import webbrowser
        webbrowser.open_new_tab(htmlPath)


class mycard(object):
    """mycard blance checking"""
    def __init__(self,payment_account):
        '''赋值'''
        self.myaccount, self.mypwd, self.secCode = mycardAccount(payment_account)
    def headers(self):
        s.headers.clear()
        s.headers.update(
            {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'})
        s.headers.update(
            {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'})
        s.headers.update(
            {'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6'})
        # s.headers.update({'Upgrade-Insecure-Requests': '1'})
        s.headers.update({'Accept-Encoding': 'gzip, deflate, br'})
        # s.headers.update({'X-Requested-With': 'XMLHttpRequest'})
    def a(self):
        url = 'https://member.mycard520.com.tw/Login/MyCardMemberLogin.aspx?ReturnUrl=%2fdefault.aspx'
        r = s.get(url=url,verify=False)
        self.mycardContent = r.content
    def captcha(self):
        url = 'https://member.mycard520.com.tw/Login/Captcha.aspx'
        r = s.get(url=url,verify=False)
        img     = r.content
        '''IOS pythonista 图片控制台直接显示代码,不需要添加图片路径：'''
        '''with as语法直接生成f文件'''
        with open(sysFilePath()+'a.jpg','wb' ) as f:
            f.write(img)
        Captcha = CaptchaTotext(sysFilePath()+'a.jpg')
        return Captcha
    def mycardPage_post_data(self,content):
        '''生成Mycard页面的加密数据'''     
        content = re.findall(r'"__VIEWSTATE"\svalue=\S+|"__VIEWSTATEGENERATOR"\svalue=\S+|"__EVENTVALIDATION"\svalue=\S+', content)
        '''通过列表截取需要的字符内容'''
        # print content[0][21:-1]
        # print content[1][30:-1]
        # print content[2][26:-1]

        VIEWSTATE           = content[0][21:-1]
        VIEWSTATEGENERATOR  = content[1][30:-1]
        EVENTVALIDATION     = content[2][27:-1]
        return VIEWSTATE, VIEWSTATEGENERATOR, EVENTVALIDATION 
    @retry(stop_max_attempt_number=10,wait_fixed=3000)
    def b(self):
        s.headers.update({'X-MicrosoftAjax': 'Delta=true'})
        url = 'https://member.mycard520.com.tw/Login/MyCardMemberLogin.aspx?ReturnUrl=%2fdefault.aspx'
        VIEWSTATE, VIEWSTATEGENERATOR, EVENTVALIDATION = self.mycardPage_post_data(content = self.mycardContent)
        ''' Login page data'''
        data                = {
                                '__EVENTTARGET': '',
                                '__EVENTARGUMENT': '',
                                '__VIEWSTATE': VIEWSTATE,
                                '__VIEWSTATEGENERATOR': VIEWSTATEGENERATOR,
                                '__EVENTVALIDATION': EVENTVALIDATION,
                                'TextBox1': self.myaccount,
                                'TextBox2': self.mypwd,
                                'txtCaptchaCode': '',
                                'Button1': 'Login',
                                }
        r                   = s.post(url=url, data=data, verify=False, timeout=4)
        if r.content.split('|')[0] == '69':
            print 'Login successfully.'
        else:
            raise exception('Login failed')
    def c(self):        
        url = 'https://member.mycard520.com.tw/default.aspx'
        r = s.get(url=url,verify=False)
        myCardPoint = re.findall(r'MyCardPoint">\d+',r.text)[0]
        myCardPoint = re.findall(r'\d+',myCardPoint)[0]
        print 'mycard blance: %s'%myCardPoint
    def run(self):
        T0 = int(time.time())
        self.headers()
        self.a()
        self.b()
        self.c()
        T1 = int(time.time())
        print str(T1-T0)


class ea(object):
    """main ea auto shopping"""
    def __init__(self, user_account, payment_account):
        '''self.account类型设置为str，不然云打码文件路径不识别'''
        self.myaccount, self.mypwd, self.secCode = mycardAccount(payment_account)
        self.account, self.accountPwd, self.gameEdition, self.gateCountry = list(user_account) # 元组转列表
        self.countryCode, self.currencyCode, self.payload, self.offerId, self.couponStatus = gamedata(self.gameEdition)
        '''rest country临时切换激活区域'''
        self.restCountry(self.gateCountry)

    def a(self):  # build headers
        s.headers.clear()
        s.headers.update(
            {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4'})
        s.headers.update(
            {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
        s.headers.update(
            {'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6'})
        s.headers.update({'Upgrade-Insecure-Requests': '1'})
        s.headers.update({'Accept-Encoding': 'gzip, deflate, br'})
    def b(self):  # GET signin_ea executionId
        url                 = 'https://accounts.ea.com/connect/auth?client_id=customer_portal'\
                              '&response_type=code&redirect_uri=https://myaccount.ea.com/cp-ui/aboutme/login&locale=zh_TW'
        r                   = s.get(url=url, timeout=4)
        self.executionId    = re.findall(r'e\d{1,10}s', str(r.url))[0]
    def c(self):  # POST signin_JSESSIONID
        url     =   'https://signin.ea.com/p/web2/login'
        params  = {
                    'execution': self.executionId+'1',
                    'initref': 'https://accounts.ea.com:443/connect/auth?client_id=customer_portal'\
                    '&response_type=code&redirect_uri=https://myaccount.ea.com/cp-ui/aboutme/login&locale=zh_TW',
                    }
        data    = {
                    'email': self.account,
                    'password': self.accountPwd,
                    'country': 'HK',
                    'phoneNumber': '',
                    'passwordForPhone': '',
                    '_rememberMe': 'on',
                    'rememberMe': 'on',
                    '_eventId': 'submit',
                    'gCaptchaResponse': '',
                    'isPhoneNumberLogin': 'false',
                    'isIncompletePhone': ''
                    }
        r       = s.post(url=url, params=params, data=data, allow_redirects=True, timeout=4,)
    def d(self):  # GET login to ea _nx_mpcid security code
        url     =   'https://signin.ea.com/p/web2/login'
        params  = { 'execution': self.executionId+'2',
                    'initref': 'https://accounts.ea.com:443/connect/auth?client_id=customer_portal&'\
                    'response_type=code&redirect_uri=https://myaccount.ea.com/cp-ui/aboutme/login&locale=zh_TW',
                    '_eventId': 'end'}
        r       =   s.get(url=url, params=params, allow_redirects=False, timeout=4,)   
        '''
        如果链接转到验证页面，或者提示错误退出
        executionId = 尾数为3是验证码界面
        '''
        executionId_3 = None
        try:
            executionId_3 = re.findall(r'e\d{1,10}s3',str(r.headers))[0]
        except:
            pass

        if executionId_3 is not None:
            '''如不需要处理验证这里可以屏蔽'''
            r.headers = self.GET_security_verify(r.headers)
            # print '\n%s executionId is %s, please unlock Security code\n\n\n\n\n\n\n\n\n\n\n\n'%(self.account, executionId_3)
            # quit()
        elif r.status_code == 409:
            print '\n%s email or pwd is incorrect, Please check again.\n\n\n\n\n\n\n\n\n\n\n\n'%self.account
            quit()
        else:
            pass
        url = r.headers['Location']
        print '\n%s Login successfully\n'%self.account
        return url
    def e(self):  # GET sid, remid
        url     = self.d()
        r       = s.get(url=url,allow_redirects=False,timeout=4,)
    def f(self):  # GET Authorization access_token = AuthToken
        url                 = 'https://accounts.ea.com/connect/auth?client_id=ORIGIN_JS_SDK'\
                              '&response_type=token&redirect_uri=nucleus:rest&prompt=none&release_type=prod'
        r                   = s.get(url=url, timeout=4,)
        access_token        = r.json()['access_token']
        # self.AuthToken      = str(access_token)
        self.Authorization  = str('Bearer %s' % access_token)
        s.headers.update({'Authorization': self.Authorization})
        s.headers.update({'AuthToken': access_token})
        # return Authorization
    def pid(self):
        '''X-Extended-Pids,X-Include-UnderAge非必须'''
        s.headers.update({'Accept': '*','X-Extended-Pids': 'true','X-Include-UnderAge': 'true'})
        url         = 'https://gateway.ea.com/proxy/identity/pids/me'
        r           = s.get(url=url, timeout=4,)
        userId      = r.json()['pid']['externalRefValue']
        serverid    = str(random.randint(1,4))
        url         = 'https://api%s.origin.com/ecommerce2/consolidatedentitlements/%s?machine_hash=1'%(serverid, userId)
        s.headers.update({'Accept': 'application/vnd.origin.v3+json; x-cache/force-write'})
        return url
    def gameCheck(self):
        '''获取游戏库游戏数据，使用字典提取json中的offerId数据判断游戏是否已经激活过'''
        print '----------------------\ngame Library\n----------------------'
        url             = self.pid()
        r               = s.get(url=url, timeout = 4,)
        offerIdDict     = {}
        entitlements    = r.json()['entitlements']
        for titleId in entitlements:
            i = {titleId['offerId']:{'grantDate':titleId['grantDate']}}
            offerIdDict.update(i)
        if self.offerId in offerIdDict.keys():
            print '\n%s has been activated.\n\nAt UTC Time: %s'%(self.account, offerIdDict[self.offerId]['grantDate'])
            quit()
        else:
            print 'not activate before. continue...'
    def g(self):  # POST game payload json
        #'client_id': 'ORIGIN_JS_SDK', 'Nucleus-RequestorId': 'Ebisu-Platform',非必须
        self.a()
        s.headers.update({'Authorization': self.Authorization})
        s.headers.update({'Accept': 'application/json', 'X-CART-REQUESTORID': 'Ebisu-Platform', })
        timestamp       = str(int(time.time()*1000)) #乘以1000得出13位的时间戳，最后转为字符型
        self.cartName   = 'store-cart-purchase-'+timestamp
        url             = 'https://gateway.ea.com/proxy/commerce/carts2/%s/offerEntries?storeId=Store-Origin'\
                          '&currencyCode=%s&needFullCartInfo=true&needClearCart=true&countryCode=%s'%(self.cartName,self.currencyCode,self.countryCode)
        r               = s.post(url=url, data=json.dumps(self.payload), timeout=4,)
        if r.status_code == 400:
            print 'Proxy country incorrect, quit now'
            quit()
        else:
            currency    = r.json()['cartInfo']['currency']
            totalPrice  = r.json()['cartInfo']['totalPriceWithoutTax']
            print '\n%s %s%s'%(self.gameEdition, totalPrice, currency)
            self.a()
    def h(self):  # GET X_SESSION_TOKEN
        url          = 'https://checkout.ea.com/checkout/origin?gameId=originX&cartName=%s&locale=zh_TW'\
                       '&currency=%s&countryCode=%s&invoiceSource=ORIGIN-STORE-WEB-HK'%(self.cartName,self.currencyCode,self.countryCode)
        r            = s.get(url=url, timeout=4,)
        sessionToken = self.token()
        return sessionToken
    def GET_rest_accounts(self): # GET postAccount data
        print   '\n----------------------\nGET_rest_accounts\n----------------------\n'
        s.headers.update({'X-SESSION-TOKEN': self.h()})
        s.headers.update({'Content-Type': 'application/x-www-form-urlencoded',})
        timestamp   = str(int(time.time()*1000)) #乘以1000得出13位的时间戳，最后转为字符型     
        url         = 'https://checkout.ea.com/rest/accounts?_='+timestamp
        r           = s.get(url=url, timeout=4)
        if 'myCard' in r.json():
            '''实际只要获得邮箱和accountId数据即可'''
            '''进行urlencode编码，防止用户名中有中文，无法输入，发出后编码加密，却会引起第二次无法正确显示账单中文名字'''
            email       = r.json()['myCard'][0]['email']
            firstName   = r.json()['myCard'][0]['firstName']
            lastName    = r.json()['myCard'][0]['lastName']
            accountId   = r.json()['myCard'][0]['accountId']
            data        = {'email':email, 'firstName': firstName, 'lastName': lastName, 'selectedAccountId': accountId, 'selectedPaymentType': 'MYCARD_MEMBER' }
            data        = urllib.urlencode(data)
            print 'Default data:\n',data
        else:
            data        = 'email=Yogo%40mail.com&firstName=Yo&lastName=Go&selectedPaymentType=MYCARD_MEMBER&selectedAccountId=0'
            print 'Set default data:\n', data
        return data
    def POST_postAccount(self):  # POST postAccount
        url     = 'https://checkout.ea.com/rest/postAccount'
        data    = self.GET_rest_accounts()        
        r       = s.post(url=url, data=data,) 
    def GET_reviewOrder(self):   # GET reviewOrder=>transactionToken
        timestamp               = str(int(time.time()*1000)) #乘以1000得出13位的时间戳，最后转为字符型
        url                     = 'https://checkout.ea.com/rest/reviewOrder?_='+timestamp
        r                       = s.get(url=url,timeout = 4,)
        self.transactionToken   = r.json()['transactionToken']
        self.totalPrice         = r.json()['totalPrice']
        self.myCardPoint        = r.json()['myCardPoint']
        print '\n**********NO COUPON CODE APPLY**********\n'
        print 'hkPrice: %s\nmyCardPoint: %s\n'%(self.totalPrice,self.myCardPoint)
    def POST_applyCoupon(self):  # POST applyCoupon
        '''COUPON 30% Discount'''
        if  self.couponStatus   == 'Yes':
            url                 = 'https://checkout.ea.com/rest/applyCoupon'
            data                = {'couponCode':'SAVE30'}
            r                   = s.post(url=url, data=data,)
            self.totalPrice     = r.json()['totalPrice']
            self.myCardPoint    = r.json()['myCardPoint']
            print '\n----------------------\nPOST_applyCoupon\n----------------------\n'
            print '\n**********WITH COUPON SAVE30**********\n'
            print 'hkPrice: %s\nmyCardPoint: %s\n'%(self.totalPrice,self.myCardPoint) 
        elif self.couponStatus       == 'No':
            print   'No another discount for this game.'
        else:
            raise Exception('there is an error occured at POST_applyCoupon.')
    def POST_placeOrder(self):   # POST placeOrder
        s.headers.update({'X-TRANSACTION-TOKEN': self.transactionToken})
        try:
            print '\n----------------------\nPOST_placeOrder\n----------------------\n'
            url         = 'https://checkout.ea.com/rest/placeOrder'
            r           = s.post(url=url,)
            actionUri   = r.json()['actionUri']
            self.a()
            print 'placeOrder successfully.'
            return actionUri
        except:
            error_code  = r.json()['errorResponses'][0]['error_code']
            # raise Exception('cannot placeOrder now. error_code is %s.'%error_code)
            print 'cannot placeOrder now. error_code is %s.'%error_code
    def GET_mycardPage(self):    # mycardContent, mycardurl
        actionUri               = self.POST_placeOrder()
        url                     = actionUri+'&redirectUri=https://www.origin.com/views/checkout.html'
        r                       = s.get(url=url, timeout=4,)        
        self.mycardContent      = r.content
        self.mycardurl          = r.url
        print   '\n----------------------\nGot_mycardPage\n----------------------\n'
        print   '%s mycardPage got Done'%self.account
    def mycardPage_post_data(self,content):
        '''生成Mycard页面的加密数据'''     
        content = re.findall(r'"__VIEWSTATE"\svalue=\S+|"__VIEWSTATEGENERATOR"\svalue=\S+|"__EVENTVALIDATION"\svalue=\S+', content)
        '''通过列表截取需要的字符内容'''
        VIEWSTATE           = content[0][21:-1]
        VIEWSTATEGENERATOR  = content[1][30:-1]
        EVENTVALIDATION     = content[2][27:-1]

        return VIEWSTATE, VIEWSTATEGENERATOR, EVENTVALIDATION  
    def GET_captcha_code(self):    # Captcha
        '''自动输入Mycard验证码'''
        print   '\n----------------------\nGET_captcha_code\n----------------------\n'
        url     = 'https://member.mycard520.com.tw/Login/Captcha.aspx'
        r       = s.get(url=url, allow_redirects=False, timeout=4,)
        img     = r.content
        '''IOS pythonista 图片控制台直接显示代码,不需要添加图片路径：'''
        with open(sysFilePath()+self.account.split('@')[0]+'a.jpg','wb' ) as f:
            f.write(img)
        Captcha = CaptchaTotext(sysFilePath()+self.account.split('@')[0]+'a.jpg')
        return Captcha
    @retry(stop_max_attempt_number=10,wait_fixed=3000)  # 设置次数10，避免验证码10次都错
    def POST_login_mycard(self):   # MyCardMemberLogin, verifyCodeUrl, AuthContent
        url                 = self.mycardurl
        VIEWSTATE, VIEWSTATEGENERATOR, EVENTVALIDATION = self.mycardPage_post_data(self.mycardContent)
        ''' Login page data'''
        data                = {
                                '__EVENTTARGET': '',
                                '__EVENTARGUMENT': '',
                                '__VIEWSTATE': VIEWSTATE,
                                '__VIEWSTATEGENERATOR': VIEWSTATEGENERATOR,
                                '__EVENTVALIDATION': EVENTVALIDATION,
                                'TextBox1': self.myaccount,
                                'TextBox2': self.mypwd,
                                'txtCaptchaCode': self.GET_captcha_code(),
                                'Button1': 'Login',
                                }
        r                   = s.post(url=url, data=data, timeout=4)
        self.verifyCodeUrl  = r.url
        self.AuthContent    = r.content
        print   '\n----------------------\nPosted_login_mycardPage\n----------------------\n'
        print   'Login mycard page data:\n%s\n'%data
        '''cookies中.MyCardMemberLogin的值未找到则报错，retry'''
        print '.MyCardMemberLogin \n%s'%s.cookies['.MyCardMemberLogin']
    @retry(stop_max_attempt_number=5,wait_fixed=5000)
    def POST_input_mycard_secCode(self):  # self.invoiceIdurl
        print   '\n----------------------\nPOST_input_mycard_secCode\n----------------------\n'
        url         = self.verifyCodeUrl
        VIEWSTATE, VIEWSTATEGENERATOR, EVENTVALIDATION = self.mycardPage_post_data(self.AuthContent)
        '''verifyCode page data'''
        data        = {
                        '__EVENTTARGET': '',
                        '__EVENTARGUMENT': '',
                        '__VIEWSTATE': VIEWSTATE,
                        '__VIEWSTATEGENERATOR': VIEWSTATEGENERATOR,
                        '__EVENTVALIDATION': EVENTVALIDATION,
                        'txtSecCode': self.secCode,
                        'btnLogin': 'Login now',
                        }
        r           = s.post(url=url, data=data,) 
        print 'Input mycard secCode page data:\n%s\n'%data
        if r.url    == 'https://member.mycard520.com.tw/MyCardMemberBlackMsg.aspx':
            print 'MyCard was banned.'
            ''' 
            没有设置quit()退出，重复尝试5次后会报异常退出
            且设置后，quit()之后的命令不执行'''
            quit()
        invoiceId           = re.findall(r'"invoiceId"\svalue=\S+\w"',str(r.content))[0]
        invoiceId           = invoiceId[19:-1]
        timestamp           = str(int(time.time()*1000)) #乘以1000得出13位的时间戳，最后转为字符型
        self.invoiceIdurl   = 'https://checkout.ea.com/checkout/paymentStatus?invoiceId=%s&_=%s'%(invoiceId,timestamp)
        print '\ninvoiceIdurl===>\n%s\n' % self.invoiceIdurl
        '''If the MyCard points is enough to deduation, 
            when you saw this url, whatever error information, 
            please do not place order again. Just waiting 30 min. order will be complete.'''
    @retry(stop_max_attempt_number=3,wait_fixed=5000)
    def GET_paymentStatus(self):   # fidUrl
        print   '\n----------------------\nGET_paymentStatus\n----------------------\n'
        url             = self.invoiceIdurl
        r               = s.get(url=url, timeout=4,)
        content         = eval(r.content) #得到的内容是字符型的str需要转成字典, 使用eval
        statusCheck     = content['actionUri']
        if statusCheck  == '/checkout/origin/complete':
            fid         = content['fid']
            self.fidUrl = 'https://checkout.ea.com/checkout/origin/complete?token=%s&gameId=originX'%fid
            print 'paymentStatus Completed.'
        else:
            print 'Order deduction failed. No enough MyCard Points.'
            self.log('Failed')
            quit()
    @retry(stop_max_attempt_number=3,wait_fixed=5000)
    def GET_orderCompleted(self):  # txnToken
        print   '\n----------------------\nGET_orderCompleted\n----------------------\n'
        '''到这步完成后，订单状态也显示完成'''
        '''https://checkout.ea.com/checkout/origin/complete?token=F5cZZZQJedBtBDfJ&gameId=originX'''
        url             = self.fidUrl
        r               = s.get(url=url, allow_redirects=False,)
        self.txnToken   = re.findall(r'txnToken=\w+.\w+',str(r.headers))[0]
        self.log('Completed')
        print   'Order status Completed.'
    @retry(stop_max_attempt_number=3,wait_fixed=5000)
    def GET_orderReceipt(self):    # refresh x_session_token
        print '\n----------------------\nGET_orderReceipt\n----------------------\n'
        s_txn   = s.cookies['s_txn']  # s_txn before orderReceipt
        url     = 'https://checkout.ea.com/checkout/origin?gameId=originX&cartName=%s&locale=zh_TW&currency=%s'\
                  '&countryCode=%s&%s&invoiceSource=ORIGIN-STORE-WEB-HK'%(self.cartName,self.currencyCode,self.countryCode,self.txnToken)
        r       = s.get(url=url, timeout=7,)
        print 'GET_orderReceipt successfully.' if s_txn != s.cookies['s_txn'] else 'GET_orderReceipt failed.'
    def POST_orderReceipt(self):   # end
        print   '\n----------------------\nPOST_orderReceipt\n----------------------\n'
        s.headers.update({'X-SESSION-TOKEN': self.token()})
        s.headers.update({'X-Requested-With': 'XMLHttpRequest'})
        s.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
        url             = 'https://checkout.ea.com/rest/orderReceipt'
        r               = s.post(url=url, timeout=7,)
        self.jsondata   = r.json()


    '''Helper function'''
    def token(self):  # 生成X-SESSION-TOKEN加密值
        # 用s.cookies中更新的s_txn值生成base64加密值
        X_SESSION_TOKEN = base64.b64encode(s.cookies['s_txn']) 
        X_SESSION_TOKEN = re.findall(r'VTFR\w+',X_SESSION_TOKEN)[0]
        return X_SESSION_TOKEN
    def log(self,status):  # 生成日志
        timenow     = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        detail = '\n%s\t%s\t%s\t%s\t%s\t%s\t%s' % (self.account, self.gameEdition, self.totalPrice, self.myCardPoint, self.myaccount, status, timenow)
        with open( sysFilePath()+'detail.txt','a+' ) as f:
            f.write(detail.encode('UTF-8'))
    def restCountry(self, gateCountry):  # 临时切换激活区域
        # print 'gateCountry %s'%gateCountry
        if gateCountry != None and gateCountry == 'hk':
            self.countryCode, self.currencyCode = 'HK', 'HKD'
            print 'reset country: %s %s' % (self.countryCode, self.currencyCode)
        elif gateCountry != None and gateCountry == 'tw':
            self.countryCode, self.currencyCode = 'TW', 'TWD'
            print 'reset country: %s %s' % (self.countryCode, self.currencyCode)
    @retry(stop_max_attempt_number=5,wait_fixed=3000)
    def GET_security_verify(self,headers):  # 有验证码的帐号进入验证环节
        print '\nSecurity verify page. checking...\n'
        '''
        重新转到验证码页面
        转到验证码页面,网址中删除参数'_eventId'键值
        并更新'execution'值为executionId+'3','''         
        url     = 'https://signin.ea.com/p/web2/login'
        params  = {
                    'execution': self.executionId+'3',
                    'initref': 'https://accounts.ea.com:443/connect/auth?client_id=customer_portal'\
                    '&response_type=code&redirect_uri=https://myaccount.ea.com/cp-ui/aboutme/login&locale=zh_TW',
                    }
        data    = {'_eventId': 'submit', 'codeType': 'EMAIL'}
        r       = s.post(url=url, params=params, data=data, timeout=4,)
        '''输入邮箱验证码'''
        oneTimeCode = (u'%s'%raw_input('Please input oneTimeCode from email.\n\n\n'))
        '''字符不等于6位长度时，循环提示输入6位码 '''
        while len(oneTimeCode) != 6:
            oneTimeCode = (u'%s'%raw_input('Please input oneTimeCode in right format 6 No.\n\n\n'))
        '''更新'execution'值为executionId+'4'''
        params['execution'] = self.executionId+'4',
        data                = {'_eventId': 'submit', '_trustThisDevice': 'on', 'oneTimeCode': oneTimeCode}
        r                   = s.post(url=url, params=params, data=data, allow_redirects=False, timeout=4,)
        '''
        检测headers值是否含有'_nx_mpcid'的Cookie
        有就通过，出现异常就使用retry方法再次输入验证码'''
        Cookie = r.headers['Set-Cookie']
        print '\nverify successfully!;D\n'
        headers = r.headers
        return headers
    
    '''Main function'''
    def login(self):
        self.a()  # reset headers
        self.b()  # GET signin_ea executionId
        self.c()  # POST signin_JSESSIONID
        self.e()  # GET sid, remid
        self.f()  # GET Authorization
        self.gameCheck()  # check game Library
    @retry(stop_max_attempt_number=5,wait_fixed=3000)
    def postOrder(self):  # 下单过程可能出错，采用retry重复尝试下单过程
        self.g()  # POST game payload json
        self.POST_postAccount()
        self.GET_reviewOrder()
        self.POST_applyCoupon()
        self.GET_mycardPage()
    def shopping(self):  # main run fuction
        T0 = int(time.time())
        self.login()
        self.postOrder()
        self.POST_login_mycard()
        self.POST_input_mycard_secCode()
        self.GET_paymentStatus()
        self.GET_orderCompleted()
        self.GET_orderReceipt()
        self.POST_orderReceipt()
        Create_html_page(self.jsondata)
        T1 = int(time.time())
        print str(T1-T0)


def running(user_account,payment_account):
    # mycardAccount()
    account, accountPwd, gameEdition, gateCountry = list(user_account)
    print '\nuser account\t %s\nuserpassword\t %s\ngame edition\t %s\n'%(account, accountPwd, gameEdition)
    shoppingGame = ea(user_account, payment_account).shopping()
def Process(allgame):
    a = []
    for user_account in allgame:
        # t=threading.Thread(target=running, args=(game,))
        # print 'running game is %s'%game
        t = multiprocessing.Process(target=running, args=(user_account,payment_account))
        a.append(t)
    for i in a:
        i.start()
        timenum = random.randint(5,10)
        time.sleep(timenum)
    for i in a:
        i.join()

if __name__ == '__main__':
    '''单进程手机用'''

    # payment_account = str(raw_input('Please in put payment account info.\n\n\n'))
    # payment_account = 'betaqfqj@163.com     xyzasd123   z000' # 封禁测试号
    # payment_account = 'gangsongxingpo4@163.com  zz110110    x000'
    # payment_account = 'tmdt58198715@yeah.net    zz110110    x000' # 点数不足测试号
    payment_account = 'fulun7431@163.com    qq123123    w232'
    
    '''在Windows命令行中有中文输入时，字符转成unicode模式，再encode加密成utf-8模式，方便后期函数统一调用'''
    user_account    = (u'%s'%raw_input('Please input user account info.\n\n\n')).encode('utf-8')
    user_account = user_info(user_account)  # 元组
    shoppingGame = ea(user_account, payment_account).shopping()
    mycard = mycard(payment_account)
    mycard.run()