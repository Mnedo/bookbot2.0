import datetime


class AccessError(Exception):
    def __init__(self, *args):
        if args:
            args[0].bot.send_message(
                text='Кажется, Вы в черном листе и не можете совершать какие-либо действия, если это ошибка, свяжитесь с нами.',
                chat_id=args[1])


class Buttons:
    def __init__(self):
        self.keyboard = []
        self.timedate = ''
        self.timeutc = ''
        self.calendar = ''
        self.range = ''
        self.nextlevel = 0
        self.ctx = ''
        self.tz = datetime.timezone(datetime.timedelta(hours=3))
        self.tzn = 3
        self.admin = False

    def admin_panel(self):
        self.admin = True

    def rusific(self, w):
        mn = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return mn[int(w) - 1]

    def is_admin(self):
        return self.admin

    def set_calendar(self, map):
        self.calendar = map

    def set_sure(self, mes):
        self.sure = mes

    def set_tz(self, tz, tzn):
        self.tz = tz
        self.tzn = tzn
        self.calendar.set_tz(tz, tzn)

    def set_time(self, dttm):
        ff = True
        day = datetime.datetime.now(tz=self.tz) - datetime.timedelta(days=1)
        while ff:
            day += datetime.timedelta(days=1)
            if day.strftime('%d.%m') == dttm:
                ff = False
                self.timedate = datetime.datetime.strptime(day.strftime('%d.%m.%Y'), '%d.%m.%Y')

    def set_range(self, rng):
        self.range = range(int(rng[0].split(':')[0]), int(rng[1].split(':')[0]) + 1)

    def set_context(self, ctx):
        self.ctx = ctx

    def get_range(self):
        return self.range

    def get_utc(self):
        return 'T'.join(str(self.timeutc).split()) + '+00:00'

    def is_valid_day(self, dttm):
        return self.calendar.is_valid_day(dttm)

    def sign_out(self, dtm_start, dtm_end):
        self.calendar.sign_out(dtm_start, dtm_end)

    def create_admin(self, command):
        if self.is_admin():
            if command == 'start':
                self.keyboard.append(['/admin', '/user_info', '/main_menu'])
                self.keyboard.append(['/ban_user', '/disban_user'])
                self.keyboard.append(['/set_description', '/set_timezone'])
                self.keyboard.append(['/set_contact_number', '/set_address'])
                self.keyboard.append(['/data_clear'])
                self.keyboard.append(['/get_feedbacks'])
        else:
            self.keyboard.append(['/Главное меню'])

    def create(self, command, *args):
        if self.nextlevel == -1:
            command = 'appointment'
        if command == 'next':
            self.nextlevel += 1
            counter = 0
            var = datetime.datetime.today() - datetime.timedelta(days=1)
            self.vt = datetime.datetime.today()
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
                if self.is_admin():
                    self.keyboard.append(['/admin_panel'])
            elif command == 'account':
                self.keyboard.append(['/Статус', '/Оставить отзыв'])
                self.keyboard.append(['/Сменить телефон', '/Главное меню'])
            elif command == 'registration':
                sp = self.calendar.valid_time(self.timedate)
                mainrow = []
                c1 = '/В {}:00-{}:00'.format(str(self.tzn + 6) if self.tzn + 6 < 24 else '24',
                                             str(self.tzn + 9) if self.tzn + 9 < 24 else '24')
                c2 = '/В {}:00-{}:00'.format(str(self.tzn + 9) if self.tzn + 9 < 24 else '24',
                                             str(self.tzn + 14) if self.tzn + 14 < 24 else '24')
                c3 = '/В {}:00-{}:00'.format(str(self.tzn + 14) if self.tzn + 14 < 24 else '24',
                                             str(self.tzn + 20) if self.tzn + 20 < 24 else '24')
                for el in sp:
                    starttime = int(el[0].split(':')[0]) + int(int(el[0].split(':')[0]) // 60)
                    endtime = int(el[1].split(':')[0]) + int(int(el[1].split(':')[0]) // 60)
                    tz = el[2]
                    if starttime - tz + self.tzn in range(6 + self.tzn, 9 + self.tzn):
                        if c1 not in mainrow:
                            mainrow.append(c1)
                    if starttime - tz + self.tzn in range(self.tzn + 9, self.tzn + 14):
                        if c2 not in mainrow:
                            mainrow.append(c2)
                    if starttime - tz + self.tzn in range(self.tzn + 14, self.tzn + 20):
                        if c3 not in mainrow:
                            mainrow.append(c3)
                skip = ['/Назад к неделе']
                self.keyboard.append(mainrow)
                self.keyboard.append(skip)
            elif 'time' in command:
                sp = self.calendar.valid_time(self.timedate)
                mainrow = []
                for el in sp:
                    if int(el[0].split(':')[0]) - el[2] + self.tzn in self.range:
                        t1 = str('{}:{}'.format(
                            str(int(el[0].split(':')[0]) - el[2] + self.tzn) if int(el[0].split(':')[0]) - el[
                                2] + self.tzn > 9 else '0' + str(int(el[0].split(':')[0]) - el[2] + self.tzn),
                            str(int(el[0].split(':')[1])) if int(el[0].split(':')[1]) > 9 else '0' + str(
                                int(el[0].split(':')[1]))))
                        t2 = str('{}:{}'.format(
                            str(int(el[1].split(':')[0]) - el[2] + self.tzn) if int(el[1].split(':')[0]) - el[
                                2] + self.tzn > 9 else '0' + str(int(el[1].split(':')[0]) - el[2] + self.tzn),
                            str(int(el[1].split(':')[1])) if int(el[1].split(':')[1]) > 9 else '0' + str(
                                int(el[1].split(':')[1]))))
                        if int(t1.split(':')[0]) < 24 and int(t2.split(':')[0]) < 24:
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
                now = self.timedate.strftime('%d.%m')
                skip = ['/Назад к расписанию ' + now]
                self.keyboard.append(skip)
            elif 'sure' == command:
                self.keyboard.append(['Да', 'Нет'])
            elif 'sign_out' == command:
                if self.ctx['events']:
                    text = 'Выберите вариант, который хотите отменить.'
                    for el in self.ctx['events']:
                        if el[0] > datetime.datetime.today():
                            self.keyboard.append(['/Запись ' + el[0].strftime('%d.%m.%Y') + ' в ' +
                                                  el[0].strftime('%H:%M') + ' - ' + el[1].strftime('%H:%M')])
                    if not self.keyboard:
                        text = 'Кажется, Вы ещё не записаны. /appointment - запишитесь!'
                else:
                    text = 'Кажется, Вы ещё не записаны. /appointment - запишитесь!'
                self.keyboard.append(['/Записаться', '/Главное меню'])
                return text

    def reset(self):
        self.keyboard = []
