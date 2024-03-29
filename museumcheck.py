import requests
import time
import datetime
from bs4 import BeautifulSoup
import json
import base64
import sys
import sched
import threading
import os
sys.path.append(os.path.join(os.getcwd(), 'viewstate-decoder'))
from viewstate import ViewState


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
        log.write("prep_data(resp)" + " is executed at " + str(datetime.datetime.now()) + '\n')

        bs = BeautifulSoup(resp.text, 'html.parser')

        _data_ = {}
        script = [j for j in bs.find_all('script') if j.text][1]
        print("***script: ",script)
        ___, process_url, _, scope, __, a, c = script.text.split('\n')
        scope = scope.split('=')[1].split('\"')[1]
        _data_['scope'] = scope

        print("***scope: ",scope)

        script2 = [i for i in bs.find_all('script') if i.get('src') and 'ids.hku.hk' in i['src']][0]
        script2 = self.session.get(script2['src']).text.split('\"')[1]
        script2 = base64.b64decode(script2 + '=')
        script2 = json.loads(script2)

        del script2['relyingParty']
        _data_.update(script2)
        return _data_

    def login(self):
        log.write("login(username, password, _all_cookies)" + " is executed at " + str(datetime.datetime.now()) + '\n')

        _r = self.session.post("https://ids.hku.hk/idp/ProcessAuthnLib", allow_redirects=False,
                          headers=header, data=self.login_data, verify=False)
        print(_r.headers, _r.status_code)
        print(header_login)
        self.login_data.update(self._prep_data(self.session.get(
            'https://lib.hku.hk/hkulauth/legacy/authMain?uri=https://booking.lib.hku.hk/getpatron.aspx',
            headers=header_login)))

        print('signature:', self.login_data['scope'].split('.')[2])

        r = self.session.post('https://ids.hku.hk/idp/ProcessAuthnLib', allow_redirects=False,
                              headers=header, data=self.login_data, verify=False)
        print(self.login_data)
        print(header)
        print("location:", r.headers['Location'])
        location = 'https://ids.hku.hk' + r.headers['Location']
        print('__________')

        r = self.session.get(location, headers=header)

        print(r.status_code, r.url)
        form = BeautifulSoup(r.content, 'html.parser').find('form')
        print('posting to', form['action'])
        post_url = form['action']
        relay_state, saml_resp = form.find_all('input', type='hidden')

        print(header_login)
        header_login.update({'Cache-Control': 'no-cache'})
        print(len(relay_state["value"]) + len(saml_resp["value"]) + len("SAMLResponse=RelayState=&"))
        r = self.session.post(post_url, data={'RelayState': relay_state['value'], 'SAMLResponse': saml_resp['value'], },
                              headers=header_login, allow_redirects=False)

        post_url = r.headers['Location']
        print(r.headers)
        print('posting to', post_url)
        r = self.session.get(post_url, allow_redirects=False)
        print(r.headers)
        print('Login successful')

    def booking_specific_data(self, date):

        log.write("booking_specific_data(date, room, session, number_of_session=4)" + " is executed at " +
                  str(datetime.datetime.now()) + '\n')
        session = self.time
        room = self.room
        url = f'https://booking.lib.hku.hk/Secure/NewBooking.aspx?library' \
              f'=5&ftype=29&facility={256 + int(room)}&date={date.replace("-", "")}&session={session}'

        # floor, 10 for 1st, 11 for 2nd floor
        floor = ('1' if int(room) <= 10 else '2')
        if floor == '1':
            self.booking_data['ctl00$main$ddlFloor'] = '10'
        else:
            self.booking_data['ctl00$main$ddlFloor'] = '11'

        # date YYYY-MM-DD
        self.booking_data['ctl00$main$ddlDate'] = date

        # room
        self.booking_data['ctl00$main$ddlFacility'] = f'{256 + int(room)}'

        # session
        base = 'ctl00$main$listSession$'
        start = int(session[:2] + session[2:4].replace('30', '50'))
        session = [session[i:i + 2] for i in range(0, 8, 2)]
        self.booking_data['ctl00$main$ddlLibrary'] = '5'
        self.booking_data['ctl00$main$ddlType'] = '29'
        num = (start - 800) // 50
        if floor == '1':
            num += 12
        for i in range(self.session_num):
            self.booking_data[f'{base}{num}'] = "".join(session)
            num += 1
            if session[1] == "30":
                session[1] = "00"
                session[0] = str(int(session[0]) + 1)
                session[3] = "30"
            else:
                session[1] = "30"
                session[2] = str(int(session[0]) + 1)
                session[3] = "00"
        self.url = url

    def book(self, ):
        start = datetime.datetime.now()

        r_get = self.session.get(self.url, headers=self.header_for_get, verify=False)
        log.write(f"getter()" + " is executed at " + str(start) + ', finished at ' + str(
                datetime.datetime.now()) + '\n')

        bs_obj = BeautifulSoup(r_get.content, 'html.parser')
        self.booking_data['__VIEWSTATE'] = bs_obj.find('input', attrs={'name': '__VIEWSTATE'})['value']
        self.booking_data['__EVENTVALIDATION'] = bs_obj.find('input', attrs={'name': '__EVENTVALIDATION'})['value']

        start = datetime.datetime.now()
        r_post = self.session.post(self.url, data=self.booking_data, headers=self.header_for_post, verify=False)
        viewstate_data = BeautifulSoup(r_get.content, 'html.parser').find('input', attrs={'name': '__VIEWSTATE'})
        if viewstate_data is None:
            return
        else:
            viewstate_data = ViewState(viewstate_data['value'])
        viewstate = open("viewstate_log.txt", 'w')
        viewstate.write(viewstate_data.decode().__str__())
        viewstate.close()
        log.write('post start at ' + str(start) + ', finished at ' + str(datetime.datetime.now()) + '\n')

        post_response = open('post_response.txt', 'w')
        post_response.write(r_post.text)
        post_response.close()


def get_url(room, date, session):
    return f'https://booking.lib.hku.hk/Secure/NewBooking.aspx?library=5&ftype=29&facility={256 + int(room)}&date={date.replace("-", "")}&session={session}'


def get_delta(target_time):
    # Get the current time using a high-resolution timer
    now = time.perf_counter()

    # Calculate the time until the next midnight
    delta = (target_time - datetime.datetime.now()).total_seconds()

    # Adjust the time until midnight based on the high-resolution timer
    delta -= time.perf_counter() - now
    return delta


def book_starter():
    user_index = 0
    while user_index < user_len:
        i = 0
        while i < thread_number:
            all_threads[user_index][i].start()
            i += 1
        user_index += 1

#############################################################################
# constants
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

filename = sys.argv[0].split("\\")[-1].replace(".", "_") + ".txt"
log = open(filename, "w")

with open('config.json', 'r') as f:
    config = json.load(f)
    print(config)

thread_number = config["thread_number"]
debug = config["debug"]
if len(sys.argv) > 1 and sys.argv[1] == "run":
    debug = False


log.write("welcome to Museum Guard!\n")
log.write("current mode: " + 'debug' if debug else "run" + '.\n')

config['users'] = list(filter(lambda x: x["is_active"], config["users"]))
# all_sessions = [requests.Session() for user in config["users"]]
user_len = len(config["users"])
all_threads = [[] for i in range(user_len)]

# Create a scheduler object
scheduler = sched.scheduler(time.perf_counter, time.sleep)


all_users = []


def main():
    for i in range(user_len):
        all_users.append(User(config["users"][i]))
        all_users[-1].login()
        all_users[-1].booking_specific_data(str(datetime.datetime.now() + datetime.timedelta(days=1 if debug else 2))[:10])

    if not debug:
        target_get_time = datetime.datetime.now().replace(hour=23, minute=59, second=57, microsecond=0)
    else:
        target_get_time = datetime.datetime.now() + datetime.timedelta(seconds=3)

    user_index = 0
    while user_index < user_len:
        all_threads[user_index] = [threading.Thread(target=all_users[user_index].book,)
                                       for _ in range(thread_number)]
        user_index += 1
    scheduler.enter(get_delta(target_get_time), 1, book_starter)
    scheduler.run()


main()
