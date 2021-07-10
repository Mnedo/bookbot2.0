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

    # создание словаря с информацией о событии
    def create_event(self, starttime, endtime):
        #2021-07-03T03:00:00+03:00
        # 2021-07-03T05:00:00+03:00
        event = {
            'summary': 'Свободно',
            'description': 'На этот сеанс ещё никто не регистрировался',
            'start': {
                'dateTime': starttime + 'Z',
            },
            'end': {
                'dateTime': endtime + 'Z',
            },
            'colorId': '1'
        }
        e = self.service.events().insert(calendarId=calendarId,
                                         body=event).execute()
        return e.get('id')


    # вывод списка из десяти предстоящих событий
    def update_event(self, id):
        e = self.service.events().update(calendarId=calendarId, eventId=id, body={
            'summary': 'Занято',
            'description': '',
            'colorId': '6'
        }).execute()

    def get_events_list(self, utcdate):
        #now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=calendarId,
                                                   timeMin=utcdate,
                                                   maxResults=20, singleEvents=True,
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


calendar = GoogleCalendar()
calendar.update_event('disufamgnsp8oitklq2s3rnago')
