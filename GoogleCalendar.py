from __future__ import print_function
import datetime
import googleapiclient
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

calendarId = 'j31nedosekin@gmail.com'
SERVICE_ACCOUNT_FILE = 'innate-actor-318707-a7cf8eb2099f.json'


class GoogleCalendar(object):

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
        self.tz = datetime.timezone(datetime.timedelta(hours=3))
        self.tzn = 3

    def set_tz(self, tz, tzn):
        self.tz = tz
        self.tzn = tzn

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
        e = self.service.events().insert(calendarId=calendarId,
                                         body=event).execute()
        return e.get('id')

    # вывод списка из десяти предстоящих событий
    def update_event(self, starttime, endtime, info):
        events_result = self.service.events().list(calendarId=calendarId,
                                                   timeMin=starttime,
                                                   maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        eid = events_result.get('items', [])[0].get('id')
        e = self.service.events().update(calendarId=calendarId, eventId=eid, body={
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
        dtm_start = 'T'.join(str(dtm_start).split()) + '+{}:00'.format(
            str(self.tzn) if self.tzn > 9 else '0' + str(self.tzn))
        dtm_end = 'T'.join(str(dtm_end).split()) + '+{}:00'.format(
            str(self.tzn) if self.tzn > 9 else '0' + str(self.tzn))
        events_result = self.service.events().list(calendarId=calendarId,
                                                   timeMin=dtm_start,
                                                   maxResults=10, singleEvents=True,
                                                   orderBy='startTime').execute()
        eid = events_result.get('items', [])[0].get('id')
        e = self.service.events().update(calendarId=calendarId, eventId=eid, body={
            'summary': 'Свободно',
            'description': 'На этот сеанс ещё никто не регистрировался',
            'colorId': '1',
            'start': {
                'dateTime': dtm_start,
            },
            'end': {
                'dateTime': dtm_end,
            }
        }).execute()

    def get_events_list(self, timeutc):
        now = timeutc.isoformat() + 'Z'

        print('Getting the upcoming 10 events')
        events_result = self.service.events().list(calendarId=calendarId,
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
        if dttm.date().strftime('%d.%m') == datetime.datetime.now(tz=self.tz).strftime('%d.%m'):
            now = datetime.datetime.strptime(dttm.strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M').isoformat()
            nowd = now.split('T')[0] + 'T{}:00:00.000000Z'.format(
                str(self.tzn + 20) if self.tzn + 20 < 24 else '23')
            now += 'Z'
        else:
            nows = datetime.datetime.strptime(dttm.strftime('%Y-%m-%d'), '%Y-%m-%d').isoformat().split('T')[0]
            now = nows + 'T{}:00:00.000000Z'.format(
                str(self.tzn + 6) if self.tzn + 6 > 9 else '0' + str(self.tzn + 6))
            nowd = nows + 'T{}:00:00.000000Z'.format(
                str(self.tzn + 20) if self.tzn + 20 < 24 else '23')
        events_result = self.service.events().list(calendarId=calendarId,
                                                   timeMin=now, timeMax=nowd,
                                                   maxResults=20, singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])
        if events:
            for event in events:
                if event['summary'] == 'Свободно':
                    return True
            return False

    def valid_time(self, dttm):
        if dttm.date() == datetime.datetime.now(tz=self.tz).date():
            now = datetime.datetime.now(tz=self.tz).isoformat() + 'Z'
            nowd = datetime.datetime.now(tz=self.tz).date().isoformat() + 'T23:59:59.999999Z'
        else:
            dttm += datetime.timedelta(hours=self.tzn)
            now = (dttm).isoformat() + 'Z'
            nowd = (dttm + datetime.timedelta(hours=23, minutes=59, seconds=59)).isoformat() + 'Z'
            nows = datetime.datetime.strptime(dttm.strftime('%Y-%m-%d'), '%Y-%m-%d').isoformat().split('T')[0]
            now = nows + 'T{}:00:00.000000Z'.format(
                str(self.tzn + 6) if self.tzn + 6 > 9 else '0' + str(self.tzn + 6))
            nowd = nows + 'T{}:00:00.000000Z'.format(
                str(self.tzn + 20) if self.tzn + 20 < 24 else '23')
        now = ''.join(now.split('+{}:00'.format(str(self.tzn) if self.tzn > 9 else '0' + str(self.tzn))))
        nowd = ''.join(nowd.split('+{}:00'.format(str(self.tzn) if self.tzn > 9 else '0' + str(self.tzn))))
        events_result = self.service.events().list(calendarId=calendarId,
                                                   timeMin=now,
                                                   timeMax=nowd,
                                                   maxResults=20, singleEvents=True,
                                                   orderBy='startTime').execute()
        events = events_result.get('items', [])
        res = []
        for event in events:
            if event['summary'] == 'Свободно':
                res.append([*map(lambda x: ':'.join(x.split('T')[1].split(':')[:2]),
                                 [event['start']['dateTime'], event['end']['dateTime']]),
                            int(event['start']['dateTime'].split('+')[1].split(':')[0])])
        res = sorted(res, key=lambda x: int(x[0].split(':')[0]))
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
