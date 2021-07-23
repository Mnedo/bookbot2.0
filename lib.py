import datetime
import json

from data.users import UserRes


class AccessError(Exception):
    def __init__(self, *args):
        if args:
            args[0].bot.send_message(
                text='Кажется, Вы в черном листе и не можете совершать какие-либо действия, если это ошибка, свяжитесь с нами /manager',
                chat_id=args[1])


class Event:
    def __init__(self, reg_time, start_time, end_time, user_id, master_id, service_id, has_notified=False):
        self.reg_time = reg_time
        self.start_time = start_time
        self.end_time = end_time
        self.user_id = user_id
        self.master_id = master_id
        self.has_notified = has_notified
        self.service_id = service_id
        self.format = '%Y-%m-%d %H:%M'

    def __iter__(self):
        yield 'user_id', self.user_id
        yield 'registration_time', self.reg_time.strftime('%d.%m.%Y %H:%M:%S')
        yield 'start_time', self.start_time.strftime('%d.%m.%Y %H:%M:%S')
        yield 'end_time', self.end_time.strftime('%d.%m.%Y %H:%M:%S')
        yield 'master', self.master_id
        yield 'has_notified', self.has_notified
        yield 'service', {'service_name': self.service_id}

    def notify(self):
        self.has_notified = True

    def set_format(self, format):
        self.format = format

    def update(self, ltzn, tzn):
        self.reg_time -= datetime.timedelta(hours=ltzn) - datetime.timedelta(hours=tzn)
        self.start_time -= datetime.timedelta(hours=ltzn) - datetime.timedelta(hours=tzn)
        self.end_time -= datetime.timedelta(hours=ltzn) - datetime.timedelta(hours=tzn)

    def __str__(self):
        date = self.start_time.strftime('%d.%m.%Y')
        starttime = self.start_time.strftime('%H:%M')
        endtime = self.end_time.strftime('%H:%M')
        txt = date + ' в ' + starttime + ' - ' + endtime + ' - ' + self.service_id
        return txt


class User:
    def __init__(self, update, tz, tzn, db_sess):

        self.id = update.message.chat.id
        self.name = update.message.chat.first_name
        self.surname = update.message.chat.last_name if update.message.chat.last_name else ''
        self.username = update.message.chat.username if update.message.chat.username else ''
        self.is_admin = False
        self.is_banned = False
        self.phone = 0
        self.events = []
        self.tz = tz
        self.tzn = tzn
        self.reg_time = datetime.datetime.strptime(datetime.datetime.now(tz=self.tz).strftime('%H:%M %d.%m.%Y'),
                                                   '%H:%M %d.%m.%Y')
        user = UserRes(
            user_id=self.id,
            name=self.name,
            surname=self.surname,
            user_name=self.username,
            is_admin=self.is_admin,
            is_banned=self.is_banned,
            phone=self.phone,
            reg_time=self.reg_time,
            events=''
        )
        db_sess.add(user)
        db_sess.commit()


    def __iter__(self):
        events = []
        for event in self.events:
            events.append(dict(event))
        yield 'id', self.id
        yield 'name', self.name
        yield 'surname', self.surname
        yield 'phone', self.phone
        yield 'events', events
        yield 'is_admin', self.is_admin
        yield 'is_banned', self.is_banned
        yield 'registration_time', self.reg_time.strftime('%H:%M %d.%m.%Y')

    def get_sign(self):
        if self.surname:
            txt = self.name + ' ' + self.surname
        else:
            txt = self.name
        return txt

    def set_tz(self, tz, tzn):
        ltzn = self.tzn
        self.tz = tz
        self.tzn = tzn
        self.reg_time -= datetime.timedelta(hours=ltzn) - datetime.timedelta(hours=tzn)
        for event in self.events:
            event.update(ltzn, tzn)

    def create_info(self, update, banned, admins):
        self.id = int(update['message']['chat']['id'])
        try:
            self.name = update['message']['chat']['first_name']
            if not self.name:
                self.name = ''
        except KeyError:
            self.name = ''
        try:
            self.surname = update['message']['chat']['last_name']
            if not self.surname:
                self.surname = ''
        except KeyError:
            self.surname = ''
        try:
            self.nickname = update['message']['chat']['username']
            if not self.nickname:
                self.nickname = ''
        except KeyError:
            self.nickname = ''
        if self.id in banned:
            self.is_banned = True
        if self.id in admins:
            self.is_admin = True

    def book_info(self, event):
        text = """{} {}
Контактный номер: {}
ID в системе: {}
{}""".format(self.name, self.surname, self.phone, self.id, event.reg_time.strftime('%d.%m.%Y %H:%M'))
        return text

    def __str__(self):
        status = 'заблокирован' if self.is_banned else 'пользователь'
        if status == 'пользователь':
            if self.is_admin:
                status = 'модератор'
        phone = str(self.phone) if self.phone else 'Не указан'
        if self.events:
            posts = '\n'
            for event in self.events:
                posts += str(event) + '\n'
        else:
            posts = '\n     Записи отсутствуют'
        text = """#{} Пользователь {} {}
Дата регистрации: {}
Статус: {}
Контакт: {}
Активные записи: {}""".format(self.id, self.name, self.surname, self.reg_time.strftime('%d.%m.%Y в %H:%M'), status,
                              phone, posts)
        return text

    def add_event(self, event: Event):
        self.events.append(event)


class Master:
    def __init__(self, mastername, calendarId, id, duration=1):
        self.name = mastername
        self.id = id
        self.calendarId = calendarId
        self.duration = duration
        self.services = {}

    def __eq__(self, other):
        if self.name == other.name and self.calendarId == other.calendarId and self.duration == other.duration:
            return True
        return False

    def __iter__(self):
        serv = {}
        i = 0
        for key in self.services.keys():
            i += 1
            serv[i] = {'name': key, 'duration': self.services[key]}
        yield 'id', self.id
        yield 'name', self.name
        yield 'calendarID', self.calendarId
        yield 'services', serv

    def add_service(self, name, duration=1.0):
        self.services[name] = duration


class Buttons:
    def __init__(self, id):
        self.id = id
        self.keyboard = []
        self.timedate = ''
        self.timeutc = ''
        self.calendar = ''
        self.range = ''
        self.nextlevel = 0
        self.ctx = ''
        self.tz = datetime.timezone(datetime.timedelta(hours=3))
        self.tz_int = 3
        self.admin = []
        self.services = {}
        self.master_id = 0
        self.service_id = ''
        self.date = ''
        self.delta_time = ''
        self.time = ''
        self.calendarId = ''

    def admin_panel(self, superusers):
        self.admin = superusers

    def service(self, mn):
        self.services = mn

    def rusific(self, w):
        mn = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return mn[int(w) - 1]

    def is_admin(self, id):
        if int(id) in self.admin:
            return True
        return False

    def set_calendar(self, map):
        self.calendar = map

    def set_time(self, mes):
        self.timedate = datetime.datetime.strptime((self.date.strftime('%Y-%d-%m ') + mes.split('-')[0]),
                                                   '%Y-%d-%m %H:%M')

    def set_tz(self, tz, tzn):
        self.tz = tz
        self.tz_int = tzn
        self.calendar.set_tz(tz, tzn)

    def set_weekday(self, dttm):
        ff = True
        day = datetime.datetime.now(tz=self.tz) - datetime.timedelta(days=1)
        while ff:
            day += datetime.timedelta(days=1)
            if day.strftime('%d.%m') == dttm:
                ff = False
                self.date = datetime.datetime.strptime(day.strftime('%d.%m.%Y'), '%d.%m.%Y')

    def set_range(self, rng):
        self.range = range(int(rng[0].split(':')[0]), int(rng[1].split(':')[0]) + 1)

    def set_context(self, ctx):
        self.ctx = ctx

    def get_range(self):
        return self.range

    def get_utc(self):
        return 'T'.join(str(self.timeutc).split()) + '+00:00'

    def is_valid_day(self, dttm):
        return self.calendar.is_valid_day(dttm, self.calendarId)

    def sign_out(self, dtm_start, dtm_end):
        self.calendar.sign_out(dtm_start, dtm_end, self.calendarId)

    def create_admin(self, command):
        if self.is_admin(self.id):
            if command == 'start':
                self.keyboard.append(['/admin', '/user_info', '/main_menu'])
                self.keyboard.append(['/ban_user', '/unban_user'])
                self.keyboard.append(['/add_superuser', '/del_superuser'])
                self.keyboard.append(['/set_contact_number', '/set_address'])
                self.keyboard.append(['/set_description'])
                self.keyboard.append(['/add_master', '/del_master'])
                self.keyboard.append(['/add_service', '/del_service'])
                self.keyboard.append(['/makemigration', '/applymigration'])
                self.keyboard.append(['/data_clear', '/create_work_days'])
                self.keyboard.append(['/get_feedbacks'])
                self.keyboard.append(['/system'])
        else:
            self.keyboard.append(['/Главное меню'])

    def create(self, command, *args):
        if self.nextlevel == -1:
            command = 'appointment'
        if command == 'next':
            self.nextlevel += 1
            counter = 0
            var = datetime.datetime.now(tz=self.tz) - datetime.timedelta(days=1)
            self.vt = datetime.datetime.now(tz=self.tz)
            mainrow = []
            while len(mainrow) <= 2:
                counter += 1
                var += datetime.timedelta(days=1)
                if self.is_valid_day(var):
                    mainrow.append(datetime.datetime.strptime(str(var.strftime('%Y.%m.%d')), '%Y.%m.%d'))
            starttime = mainrow[-1] + datetime.timedelta(days=1) + datetime.timedelta(
                days=7) * self.nextlevel - datetime.timedelta(days=7)
            mainrow = []
            gr = []
            skip = ['/Следующая', '/Назад', '/Главное меню']
            while len(mainrow) <= 2:
                counter += 1
                if counter > 14:
                    mainrow.append(gr)
                    del skip[0]
                    break
                if self.is_valid_day(starttime):
                    gr.append('/' + self.rusific(starttime.strftime('%w')) + ' ' + starttime.strftime('%d.%m'))
                    if len(gr) == 3:
                        mainrow.append(gr)
                        gr = []
                    elif len(gr) == 1 and len(mainrow) == 2:
                        mainrow.append(gr)
                starttime += datetime.timedelta(days=1)

            for ell in mainrow:
                self.keyboard.append(ell)
            self.keyboard.append(skip)
        else:
            self.nextlevel = 0
            if command == 'appointment':
                # %w - номер дня недели
                day = datetime.datetime.now(tz=self.tz) - datetime.timedelta(days=1)
                mainrow = []
                while len(mainrow) <= 2:
                    day += datetime.timedelta(days=1)
                    if self.is_valid_day(day):
                        if day.strftime('%d.%m.%Y') == (datetime.datetime.now(tz=self.tz)).strftime('%d.%m.%Y'):
                            btn = '/Сегодня ' + day.strftime('%d.%m')
                        else:
                            btn = '/' + self.rusific(day.strftime('%w')) + ' ' + day.strftime('%d.%m')
                        mainrow.append(btn)
                skip = ['/Следующая', '/Главное меню']
                self.keyboard.append(mainrow)
                self.keyboard.append(skip)
            elif command == 'start':
                self.keyboard.append(['/Записаться', '/Отменить запись', '/Контакты'])
                self.keyboard.append(['/Личный кабинет', '/Помощь'])
                if self.is_admin(self.id):
                    self.keyboard.append(['/admin_panel'])
            elif command == 'account':
                self.keyboard.append(['/Статус', '/Оставить отзыв'])
                self.keyboard.append(['/Сменить телефон', '/Главное меню'])
            elif command == 'registration':
                sp = self.calendar.valid_time(self.date, self.calendarId)
                ex1 = []
                for el in sp[2]:
                    sm = int(el[0].strftime('%H')) * 60 + int(el[0].strftime('%M'))
                    em = int(el[1].strftime('%H')) * 60 + int(el[1].strftime('%M'))
                    ex1.append([sm, em])
                sttm = int(sp[0].strftime('%H')) * 60 + int(sp[0].strftime('%M'))
                endtm = int(sp[1].strftime('%H')) * 60 + int(sp[1].strftime('%M'))
                d = 60 * float(self.services[self.master_id].services[self.service_id])
                d = int(d)
                res = []
                ex1 = list(map(lambda x: [x[0], x[1] + 1], ex1))
                p1 = []
                for el in ex1:
                    for i in range(el[0], el[1]):
                        p1.append(i)
                for i in range(sttm, endtm + 1, d):
                    if i + 1 not in p1 and i + d - 1 not in p1:
                        res.append([datetime.timedelta(minutes=i), datetime.timedelta(minutes=(i + d))])
                res = list(
                    map(lambda x: [(x[0] + self.date).strftime('%H:%M'), (x[1] + self.date).strftime('%H:%M')], res))
                # next res
                mainrow = []
                c1 = '/В {}-{}'.format(sp[0].strftime('%H:%M'), '12:00')
                c2 = '/В {}-{}'.format('12:00', '16:00')
                c3 = '/В {}-{}'.format('16:00', sp[1].strftime('%H:%M'))
                for el in res:
                    starttime = int(el[0].split(':')[0]) + int(int(el[0].split(':')[0]) // 60)
                    if starttime in range(int(sp[0].strftime('%H')), 12):
                        if c1 not in mainrow:
                            mainrow.append(c1)
                    if starttime in range(12, 16):
                        if c2 not in mainrow:
                            mainrow.append(c2)
                    if starttime in range(16, int(sp[1].strftime('%H'))):
                        if c3 not in mainrow:
                            mainrow.append(c3)
                skip = ['/Назад к неделе']
                self.keyboard.append(mainrow)
                self.keyboard.append(skip)
            elif 'time' in command:
                sp = self.calendar.valid_time(self.date, self.calendarId)
                ex1 = []
                for el in sp[2]:
                    sm = int(el[0].strftime('%H')) * 60 + int(el[0].strftime('%M'))
                    em = int(el[1].strftime('%H')) * 60 + int(el[1].strftime('%M'))
                    ex1.append([sm, em])
                sttm = int(sp[0].strftime('%H')) * 60 + int(sp[0].strftime('%M'))
                endtm = int(sp[1].strftime('%H')) * 60 + int(sp[1].strftime('%M'))
                d = 60 * float(self.services[self.master_id].services[self.service_id])
                d = int(d)
                res = []
                ex1 = list(map(lambda x: [x[0], x[1] + 1], ex1))
                p1 = []
                for el in ex1:
                    for i in range(el[0], el[1]):
                        p1.append(i)
                for i in range(sttm, endtm + 1, d):
                    if i + 1 not in p1 and i + d - 1 not in p1:
                        res.append([datetime.timedelta(minutes=i), datetime.timedelta(minutes=(i + d))])
                res = list(
                    map(lambda x: [(x[0] + self.date).strftime('%H:%M'), (x[1] + self.date).strftime('%H:%M')], res))
                mainrow = []
                for el in res:
                    if int(el[0].split(':')[0]) in self.range and int(el[1].split(':')[0]) in self.range:
                        t1 = el[0]
                        t2 = el[1]
                        time = t1 + '-' + t2
                        mainrow.append(time)
                mainrow_res = []
                gr = []
                for el in mainrow:
                    gr.append(el)
                    if len(gr) == 3:
                        mainrow_res.append(gr)
                        gr = []
                mainrow_res.append(gr)
                mainrow = mainrow_res
                for el in mainrow_res:
                    self.keyboard.append(el)
                now = self.date.strftime('%d.%m')
                skip = ['/Назад к расписанию ' + now]
                self.keyboard.append(skip)
            elif 'sure' == command:
                self.keyboard.append(['Да', 'Нет'])
            elif 'sign_out' == command:
                if self.ctx.events:
                    text = 'Выберите вариант, который хотите отменить.'
                    for el in self.ctx.events:
                        if el.start_time > datetime.datetime.strptime(
                                datetime.datetime.now(tz=self.tz).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'):
                            self.keyboard.append(['/Запись ' + str(el)])
                    if not self.keyboard:
                        text = 'Кажется, Вы ещё не записаны. /appointment - запишитесь!'
                else:
                    text = 'Кажется, Вы ещё не записаны. /appointment - запишитесь!'
                self.keyboard.append(['/Записаться', '/Главное меню'])
                return text
            elif 'master' == command:
                mainrow = []
                for key in self.services.keys():
                    mainrow.append(self.services[key].name)
                self.keyboard.append(mainrow)
                self.keyboard.append(['/Главное меню'])
            elif 'service' == command:
                mainrow = []
                master = self.services[self.master_id]
                for name in master.services:
                    mainrow.append(name)
                self.keyboard.append(mainrow)
                self.keyboard.append(['/Главное меню'])

    def reset(self):
        self.keyboard = []
