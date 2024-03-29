from bs4 import BeautifulSoup
import requests
import json
import base64

class User:
    def __init__(self, user_info):
        self.username = user_info['username']
        self.password = user_info['password']
        self.login_data = {'submit': 'Submit', 'userid': user_info['username'], 'password': user_info['password']}
        self.booking_data = {
            'ctl00$main$ToolkitScriptManager1': 'ctl00$main$UpdatePanel3|ctl00$main$btnSubmitYes',
            'main_ToolkitScriptManager1_HiddenField':
            ';;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:'
            'en-US:47d532b1-93b1-4f26-a107-54e5292e1525:475a4ef5:effe2a26:'
            '1d3ed089:5546a2b:497ef277:a43b07eb:751cdd15:dfad98a5:3cf12cf1;',
            'ctl00$main$ddlLibrary': '', 'ctl00$main$ddlFloor': '', 'ctl00$main$ddlType': '',
            'ctl00$main$ddlFacility': '', 'ctl00$main$ddlDate': '', 'ctl00$main$txtUserDescription': '', 'ctl00$main$hBtnSubmit': '',
            'ctl00$main$hBtnEmail': '', 'ctl00$main$txtEmail': '', 'ctl00$main$hBtnResult': '',
            '__LASTFOCUS': '', '__EVENTTARGET': '', '__EVENTARGUMENT': '', '__VIEWSTATE': '',
            '__VIEWSTATEGENERATOR': '95365AFE', '__EVENTVALIDATION': '',
            '__ASYNCPOST': 'true', 'ctl00$main$btnSubmitYes': 'Yes',
        }
        self.session = requests.Session()
        self.room = user_info["room"]
        self.time = user_info["session"]
        self.session_num = user_info["session_num"]
        self.url = ''
        self.header_for_get = {
            'sec-ch-ua-platform': "Windows", 'sec-ch-ua-mobile': '?0', 'Sec-Fetch-Mode': 'navigate',
            'Host': 'booking.lib.hku.hk', 'X-MicrosoftAjax': 'Delta=true', 'Sec-Fetch-Site': 'same-origin',
            'Accept-Encoding': 'gzip,deflate,br', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1', 'Connection': 'keep-alive',
            'Referer': 'https://booking.lib.hku.hk/Secure/FacilityStatusDate.aspx',
            'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://booking.lib.hku.hk',
            'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
            'User-Agent': User_Agent}
        self.header_for_post = {
            'Accept-Encoding': 'gzip, deflate, br', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Host': 'booking.lib.hku.hk',
            'Origin': 'https://booking.lib.hku.hk',
            'Referer': 'https://booking.lib.hku.hk/Secure/NewBooking.aspx', 'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Windows", 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin', 'User-Agent': User_Agent,
            'X-MicrosoftAjax': 'Delta=true', 'X-Requested-With': 'XMLHttpRequest'}
    def _prep_data(self, resp):
        bs = BeautifulSoup(resp.text, 'html.parser')

        _data_ = {}
        script = [j for j in bs.find_all('script') if j.text][1]
        ___, process_url, _, scope, __, a, c = script.text.split('\n')
        scope = scope.split('=')[1].split('\"')[1]
        _data_['scope'] = scope

        script2 = [i for i in bs.find_all('script') if i.get('src') and 'ids.hku.hk' in i['src']][0]
        script2 = self.session.get(script2['src']).text.split('\"')[1]
        script2 = base64.b64decode(script2 + '=')
        script2 = json.loads(script2)

        del script2['relyingParty']
        _data_.update(script2)
        return _data_

    def login(self):
        _r = self.session.post("https://ids.hku.hk/idp/ProcessAuthnLib", allow_redirects=False,
                          headers=header, data=self.login_data, verify=False)
        #print(_r.headers, _r.status_code)
        #print(header_login)
        self.login_data.update(self._prep_data(self.session.get(
            'https://lib.hku.hk/hkulauth/legacy/authMain?uri=https://booking.lib.hku.hk/getpatron.aspx',
            headers=header_login)))

        #print('signature:', self.login_data['scope'].split('.')[2])

        r = self.session.post('https://ids.hku.hk/idp/ProcessAuthnLib', allow_redirects=False,
                              headers=header, data=self.login_data, verify=False)
        #print(self.login_data)
        #print(header)
        #print("location:", r.headers['Location'])
        location = 'https://ids.hku.hk' + r.headers['Location']
        print('__________')

        r = self.session.get(location, headers=header)

        #print(r.status_code, r.url)
        form = BeautifulSoup(r.content, 'html.parser').find('form')
        #print('posting to', form['action'])
        post_url = form['action']
        relay_state, saml_resp = form.find_all('input', type='hidden')

        #print(header_login)
        header_login.update({'Cache-Control': 'no-cache'})
        #print(len(relay_state["value"]) + len(saml_resp["value"]) + len("SAMLResponse=RelayState=&"))
        r = self.session.post(post_url, data={'RelayState': relay_state['value'], 'SAMLResponse': saml_resp['value'], },
                              headers=header_login, allow_redirects=False)

        post_url = r.headers['Location']
        #print(r.headers)
        #print('posting to', post_url)
        r = self.session.get(post_url, allow_redirects=False)
        #print(r.headers)
        print('Login successful')

    def getResult(self):
        self.url = "https://booking.lib.hku.hk/Secure/MyBookingRecord.aspx"
        r_get = self.session.get(self.url, headers=self.header_for_get, verify=False)
        #print(r_get)
        bs_obj = BeautifulSoup(r_get.content, 'html.parser')
        #print(bs_obj)
        resultFile = open("/Users/jadenc/Documents/Code/Python/museumgard/result.txt", "w")
        title = (bs_obj.find_all(name="table",attrs={"class":"tableGray"})[1].find_all("tr")[1]
                 .find_all(name="td",attrs={"class":"rowCenter"}))
        check = (bs_obj.find_all(name="table",attrs={"class":"tableGray"})[1].find_all("tr"))
        array = []
        index = 0
        temp2 =''
        for i in range (1,len(check)-2):
            s = ''
            for j in range (0,5):
                temp = ''
                #resultFile.write(check[i].find_all(name="td",attrs={"class":"rowCenter"})[j].text)
                if(j==1):
                    temp = (str(check[i].find_all(name="td", attrs={"class": "rowCenter"})[j]).split(">")[1].split("<")[0])[-5:] + " "
                    s += "-"+temp
                else:
                    s += (str(check[i].find_all(name="td", attrs={"class": "rowCenter"})[j]).split(">")[1].split("<")[
                        0]) + " "
            if (i>1):
                if ((s[:10] == array[i-2] [:10]) or (s[:10] == temp2)):
                    array.append(s[17:])
                    temp2 = s[:10]
                else:
                    array.append(s[:16])
                    array.append(s[17:])
            elif (i == 1):
                array.append(s[:16])
                array.append(s[17:])
            else:
                array.append(s)

        print(array)
        for i in array:
            resultFile.write(i+"\n")
        resultFile.close()



User_Agent = \
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'


header = {
    'User-Agent': User_Agent, 'Referer': 'https://lib.hku.hk/', 'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'ids.hku.hk', 'Origin': 'https://lib.hku.hk', 'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Dest': 'document', 'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.9',
    'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    'Upgrade-Insecure-Requests': '1', 'Sec-Fetch-User': '?1', 'sec-ch-ua-platform': "Windows",
    'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US, en;q = 0.9, zh-CN;q=0.8, zh;q = 0.7'}
header_login = {
    'user-agent': User_Agent,
    'connection': 'keep-alive'}

with open('config2.json', 'r') as f:
    config = json.load(f)
    print(config)
config['users'] = list(filter(lambda x: x["is_active"], config["users"]))

user_len = len(config["users"])
all_threads = [[] for i in range(user_len)]
all_users = []

def main():
    for i in range(user_len):
        all_users.append(User(config["users"][i]))
        all_users[-1].login()
    all_users[0].getResult()

main()