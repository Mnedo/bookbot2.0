from __future__ import print_function
import datetime
import json
import googleapiclient
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

# SERVICE_ACCOUNT_FILE = 'innate-actor-318707-a7cf8eb2099f.json'
settings = open('setup.json', encoding='utf-8')
data = json.load(settings)
SERVICE_ACCOUNT_FILE = data['SERVICE_ACCOUNT_FILE']
day = [data['START_DAY'], data['END_DAY']]
settings.close()



class GoogleCalendar(object):

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
        self.tz = datetime.timezone(datetime.timedelta(hours=3))
        self.tzn = 3
        self.calendarId = ''

    def set_tz(self, tz, tzn):
        self.tz = tz
        self.tzn = tzn

    def tz_str(self):
        if self.tzn > 9:
            st = str(self.tzn)
        else:
            st = '0' + str(self.tzn)
        return st

    def book(self, start_time, end_time, info, ev):
        start_time = start_time.isoformat() + '+{}:00'.format(self.tz_str())
        end_time = end_time.isoformat() + '+{}:00'.format(self.tz_str())
        event = {
            'summary': ev.service_id,
            'description': info,
            'start': {
                'dateTime': start_time,
            },
            'end': {
                'dateTime': end_time,
            },
            'colorId': '6'
        }
        e = self.service.events().insert(calendarId=self.calendarId,
                                         body=event).execute()

    # создание словаря с информацией о событии
    def create_event(self, starttime, endtime):
        # 2021-07-03T03:00:00+03:00
        # 2021-07-03T05:00:00+03:00
        event = {
            'summary': 'Свободно',
            'description': 'На этот сеанс ещё никто не регистрировался',
            'start': {
                'dateTime': starttime,
            },
            'end': {
                'dateTime': endtime,
            },
            'colorId': '1'
        }
        e = self.service.events().insert(calendarId=self.calendarId,
                                         body=event).execute()
        return e.get('id')

    # вывод списка из десяти предстоящих событий
    def update_event(self, starttime, endtime, info):
        events_result = self.service.events().list(calendarId=self.calendarId,
                                                   timeMin=starttime,
                                                   maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        eid = events_result.get('items', [])[0].get('id')
        e = self.service.events().update(calendarId=self.calendarId, eventId=eid, body={
            'summary': 'Занято',
            'description': info,
            'colorId': '6',
            'start': {
                'dateTime': starttime,
            },
            'end': {
                'dateTime': endtime,
            }
        }).execute()

    def sign_out(self, dtm_start, dtm_end):
        dtm_start = dtm_start.isoformat() + '+{}:00'.format(self.tz_str())
        dtm_end = dtm_end.isoformat() + '+{}:00'.format(self.tz_str())
        events_result = self.service.events().list(calendarId=self.calendarId,
                                                   timeMin=dtm_start, timeMax=dtm_end,
                                                   maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        eid = events_result.get('items', [])[0].get('id')
        e = self.service.events().delete(calendarId=self.calendarId, eventId=eid).execute()

    def get_events_list(self, timeutc):
        now = timeutc.isoformat() + 'Z'

        print('Getting the upcoming 10 events')
        events_result = self.service.events().list(calendarId=self.calendarId,
                                                   timeMin=now,
                                                   maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
        res = {}
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['start'].get('dateTime', event['end'].get('date'))
            name = start + ' - ' + end
            res[name] = event.get('id')
        return res

    def is_valid_day(self, dttm):
        global day

        if dttm.date().strftime('%d.%m') == datetime.datetime.now(tz=self.tz).strftime('%d.%m'):
            now = datetime.datetime.strptime(dttm.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M').isoformat()
            nowd = now.split('T')[0] + 'T{}:00:00.000000Z'.format(
                str(self.tzn + 20) if self.tzn + 20 < 24 else '23')
            now += 'Z'
        else:
            nows = datetime.datetime.strptime(dttm.strftime('%Y-%m-%d'), '%Y-%m-%d').isoformat().split('T')[0]
            now = nows + 'T{}:00:00.000000Z'.format('06')
            nowd = nows + 'T{}:00:00.000000Z'.format(
                str(self.tzn + 20) if self.tzn + 20 < 24 else '23')
        events_result = self.service.events().list(calendarId=self.calendarId,
                                                   timeMin=now, timeMax=nowd,
                                                   maxResults=20, singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])
        counter = 0

        if events:
            for event in events:
                if event['summary'] == day[0]:
                    counter += 1
                elif event['summary'] == day[1]:
                    counter += 1
            if counter == 2:
                return True
            return False

    def valid_time(self, dttm):
        global day

        if dttm.date() == datetime.datetime.now(tz=self.tz).date():
            now = datetime.datetime.now(tz=self.tz).isoformat() + 'Z'
            nowd = datetime.datetime.now(tz=self.tz) + datetime.timedelta(days=1)
            nowd = nowd.isoformat() + 'Z'
        else:
            now = dttm.isoformat() + 'Z'
            nowd = dttm + datetime.timedelta(days=1)
            nowd = nowd.isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=self.calendarId,
                                                   timeMin=now, timeMax=nowd,
                                                   maxResults=20, singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])
        res = []
        start_time = ''
        end_time = ''
        exeptions = []
        for event in events:
            if event['summary'] == day[0]:
                start_time = event['end']['dateTime']
            elif event['summary'] == day[1]:
                end_time = event['start']['dateTime']
            else:
                if [datetime.datetime.strptime(event['start']['dateTime'],
                                               '%Y-%m-%dT%H:%M:%S+03:00'),
                    datetime.datetime.strptime(event['end']['dateTime'],
                                               '%Y-%m-%dT%H:%M:%S+03:00')] not in exeptions:
                    exeptions.append([datetime.datetime.strptime(event['start']['dateTime'],
                                                                 '%Y-%m-%dT%H:%M:%S+03:00'),
                                      datetime.datetime.strptime(event['end']['dateTime'],
                                                                 '%Y-%m-%dT%H:%M:%S+03:00')])
        res.append(datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S+03:00'))
        res.append(datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S+03:00'))
        res.append(exeptions)
        return res


"""
calendar = GoogleCalendar()

lst_id = []
for i in range(7):
    for j in range(10):
        if i < 3:
            start = '2021-07-{}T{}:00:00+03:00'.format(17 + i, 10 + j)
            end = '2021-07-{}T{}:00:00+03:00'.format(17 + i, 11 + j)
        lst_id.append(calendar.create_event(start, end))

# print(calendar.get_events_list(datetime.datetime.utcnow()))
# c = input()
# calendar.update_event(event, c)
#"""
