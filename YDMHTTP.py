import httplib, mimetypes, urlparse, json, time

class YDMHttp:

    apiurl = 'http://api.yundama.com/api.php'
    
    username = ''
    password = ''
    appid = ''
    appkey = ''

    def __init__(self, username, password, appid, appkey):
        self.username = username  
        self.password = password
        self.appid = str(appid)
        self.appkey = appkey

    def request(self, fields, files=[]):
        try:
            response = post_url(self.apiurl, fields, files)
            response = json.loads(response)
        except Exception as e:
            response = None
        return response
    
    def balance(self):
        data = {'method': 'balance', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey}
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['balance']
        else:
            return -9001
    
    def login(self):
        data = {'method': 'login', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey}
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['uid']
        else:
            return -9001

    def upload(self, filename, codetype, timeout):
        data = {'method': 'upload', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey, 'codetype': str(codetype), 'timeout': str(timeout)}
        file = {'file': filename}
        response = self.request(data, file)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['cid']
        else:
            return -9001

    def result(self, cid):
        data = {'method': 'result', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey, 'cid': str(cid)}
        response = self.request(data)
        return response and response['text'] or ''

    def decode(self, filename, codetype, timeout):
        cid = self.upload(filename, codetype, timeout)
        if (cid > 0):
            for i in range(0, timeout):
                result = self.result(cid)
                if (result != ''):
                    return cid, result
                else:
                    print 'retry again'
                    time.sleep(0.1)
            return -3003, ''
        else:
            return cid, ''

    def report(self, cid):
        data = {'method': 'report', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey, 'cid': str(cid), 'flag': '0'}
        response = self.request(data)
        if (response):
            return response['ret']
        else:
            return -9001

######################################################################

def post_url(url, fields, files=[]):
    urlparts = urlparse.urlsplit(url)
    return post_multipart(urlparts[1], urlparts[2], fields, files)

def post_multipart(host, selector, fields, files):
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('Host', host)
    h.putheader('Content-Type', content_type)
    h.putheader('Content-Length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    return h.file.read()

def encode_multipart_formdata(fields, files=[]):
    BOUNDARY = 'WebKitFormBoundaryJKrptX8yPbuAJLBQ'
    CRLF = '\r\n' 
    L = [] 
    for field in fields:
        key = field
        value = fields[key]
        L.append('--' + BOUNDARY) 
        L.append('Content-Disposition: form-data; name="%s"' % key) 
        L.append('') 
        L.append(value) 
    for field in files:
        key = field
        filepath = files[key]
        L.append('--' + BOUNDARY) 
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filepath))
        L.append('Content-Type: %s' % get_content_type(filepath)) 
        L.append('')
        L.append(open(filepath, 'rb').read())
    L.append('--' + BOUNDARY + '--') 
    L.append('') 
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY 
    return content_type, body 

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

#=======================================================

def YDM(filename):

    username    = 'wemark'
    password    = '741852'
    appid       = 6445
    appkey      = '5a192d7c238872bbeb1c79f54336dfb1'  
    codetype    = 1005
    timeout     = 5
    yundama     = YDMHttp(username, password, appid, appkey)
    balance     = yundama.balance()
    cid, result = yundama.decode(filename, codetype, timeout)
    # print 'YDM balance: %s cid: %s\n'%(balance,cid)
    print 'Yundama Captcha Code: %s\n'%result
    return cid, result

def report(cid):
    username    = 'wemark'
    password    = '741852'
    appid       = 6445
    appkey      = '5a192d7c238872bbeb1c79f54336dfb1'  
    codetype    = 1005
    timeout     = 30
    errorcode   = YDMHttp(username, password, appid, appkey)
    errorcode.report(cid)
    # print 'report code cid for checking.'
    # print 'captcha code incorrect, report now.'
        


if __name__ == '__main__':
    ######################################################################

    username    = 'wemark'
    password    = '741852'
    appid       = 6445
    appkey      = '5a192d7c238872bbeb1c79f54336dfb1'
    codetype    = 1005
    timeout     = 0.5                     
    
    filename    = 'C:/ea/a.gif'

    if (username == 'username'):
        print 'please write your key.'
    else:
        yundama = YDMHttp(username, password, appid, appkey)

        uid = yundama.login();
        print 'uid: %s' % uid

        balance = yundama.balance();
        print 'balance: %s' % balance

        cid, result = yundama.decode(filename, codetype, timeout);
        print 'cid: %s, result: %s' % (cid, result)
        yundama.report(cid)

    ######################################################################
