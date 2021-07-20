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
start_time = data['START_TIME']
end_time = data['END_TIME']
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

    def book(self, start_time, end_time, info, ev, calendarid):
        start_time = start_time.isoformat() + '+{}:00'.format(self.tz_str())
        end_time = end_time.isoformat() + '+{}:00'.format(self.tz_str())
        info += '\nСделано в telegram'
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
        e = self.service.events().insert(calendarId=calendarid,
                                         body=event).execute()

    # создание словаря с информацией о событии
    def create_work_day(self, starttime, endtime, calendarID):
        global day
        # 2021-07-03T03:00:00+03:00
        # 2021-07-03T05:00:00+03:00
        event_start = {
            'summary': day[0],
            'description': 'Сделано в telegram',
            'start': {
                'dateTime': (starttime - datetime.timedelta(hours=1)).isoformat() + '+0{}:00'.format(int(self.tzn)),
            },
            'end': {
                'dateTime': starttime.isoformat() + '+0{}:00'.format(int(self.tzn)),
            }
        }
        event_end = {
            'summary': day[1],
            'description': 'Сделано в telegram',
            'start': {
                'dateTime': endtime.isoformat() + '+0{}:00'.format(int(self.tzn)),
            },
            'end': {
                'dateTime': (endtime + datetime.timedelta(hours=1)).isoformat() + '+0{}:00'.format(int(self.tzn)),
            }
        }
        es = self.service.events().insert(calendarId=calendarID,
                                          body=event_start).execute()
        ee = self.service.events().insert(calendarId=calendarID,
                                          body=event_end).execute()
        ids = [es.get('id'), ee.get('id')]
        return ids

    def sign_out(self, dtm_start, dtm_end, calendarid):
        dtm_start = dtm_start.isoformat() + '+{}:00'.format(self.tz_str())
        dtm_end = dtm_end.isoformat() + '+{}:00'.format(self.tz_str())
        events_result = self.service.events().list(calendarId=calendarid,
                                                   timeMin=dtm_start, timeMax=dtm_end,
                                                   maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        eid = events_result.get('items', [])[0].get('id')
        e = self.service.events().delete(calendarId=calendarid, eventId=eid).execute()

    def get_events_list(self, date, calendarId):
        k = datetime.datetime.strptime(date.strftime('%d-%m-%Y'), '%d-%m-%Y')
        now = k.isoformat() + 'Z'
        k += datetime.timedelta(hours=23, minutes=59, seconds=59, milliseconds=59, microseconds=59)
        nowd = k.isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=calendarId,
                                                   timeMin=now, timeMax=nowd,
                                                   maxResults=24, singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])
        counter = 0
        all = 0
        for event in events:
            if event['summary'] not in day:
                if 'Сделано в telegram' in event['description']:
                    counter += 1
                all += 1
        return [counter, all]

    def is_valid_day(self, dttm, calendarid):
        global day

        if dttm.date().strftime('%d.%m') == datetime.datetime.now(tz=self.tz).strftime('%d.%m'):
            now = datetime.datetime.strptime(dttm.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M').isoformat()
            nowd = now.split('T')[0] + 'T{}:00:00.000000Z'.format(
                str(self.tzn + 20) if self.tzn + 20 < 24 else '23')
            now += 'Z'
            flag = True
        else:
            flag = False
            nows = datetime.datetime.strptime(dttm.strftime('%Y-%m-%d'), '%Y-%m-%d').isoformat().split('T')[0]
            now = nows + 'T{}:00:00.000000Z'.format('02')
            nowd = nows + 'T{}:00:00.000000Z'.format(
                str(self.tzn + 20) if self.tzn + 20 < 24 else '23')
        events_result = self.service.events().list(calendarId=calendarid,
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

    def valid_time(self, dttm, calendarid):
        global day

        if dttm.date() == datetime.datetime.now(tz=self.tz).date():
            st = datetime.datetime.now(tz=self.tz).isoformat().split('.')[0]
            now = datetime.datetime.strptime(st, '%Y-%m-%dT%H:%M:%S').isoformat() + 'Z'
            nowd = dttm + datetime.timedelta(hours=23, minutes=59, microseconds=59, milliseconds=59)
            nowd = nowd.isoformat() + 'Z'
        else:
            now = dttm.isoformat() + 'Z'
            nowd = dttm + datetime.timedelta(days=1)
            nowd = nowd.isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=calendarid,
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
