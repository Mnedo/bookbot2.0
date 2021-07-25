import os

import git
from git import Repo

from requests import get
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters
import datetime
import json
from EditedClasses import EditCommandHandler
from data import db_session
from data.events import EventRes
from data.feedback import Feedback
from data.masters import MasterRes
from data.notification import NotifRes
from data.services import ServiceRes
from data.system import System
from data.users import UserRes
from lib import Buttons, AccessError, Master, Event, User, Service
from GoogleCalendar import GoogleCalendar

settings = open('setup.json', encoding='utf-8')
data = json.load(settings)
REQUEST_KWARGS = data['REQUEST_KWARGS']
TOKEN = data['TOKEN']
account_name = data['SERVICE_ACCOUNT']
# account_name = 'test-155@innate-actor-318707.iam.gserviceaccount.com'
# TOKEN = "1765029934:AAG3PWNX_bBlUtllnaK6ZWKH9fMaEp8fKrs"
# REQUEST_KWARGS = {
#     'urllib3_proxy_kwargs': {
#         'assert_hostname': 'False',
#         'cert_reqs': 'CERT_NONE',
#         'username': 'user',
#         'password': 'password'}
# }
updater = Updater(TOKEN, use_context=True,
                  request_kwargs=REQUEST_KWARGS)
day = [data['START_DAY'], data['END_DAY']]

notification = data['NOTIFICATION_TIME']
SUPERUSERS = data['SUPERUSERS']
BANNEDUSERS = data['BANNEDUSERS']
phone = data['MANAGER']['phone']
first_name = data['MANAGER']['first_name']
last_name = data['MANAGER']['last_name']
start_time = data['START_TIME']
end_time = data['END_TIME']
settings.close()
calendar = GoogleCalendar()
if os.path.exists('database.db'):
    loaded = False
else:
    loaded = True
db_session.global_init("database.db")
db_sess = db_session.create_session()
dt = datetime.datetime.utcnow()

master = []


# master = [Master('Писхолог', '6ogmjjrvnn9c7qjco3pbvnck3s@group.calendar.google.com', db_sess, 1)]
# master[0].add_service(Service('Поговорим', db_sess, master[0]), db_sess)
# master[0].add_service(Service('Будем рисуем', db_sess, master[0], 2), db_sess)


def start(update, context):
    global SUPERUSERS, calendar, BANNEDUSERS, loaded

    try:
        if not loaded:
            load_config(context)
            loaded = True
            context.job_queue.run_monthly(data_clear, when=datetime.time(1), day=28,
                                          context=context)
            context.job_queue.run_daily(analyze, time=datetime.time(20, 58, 59, 59),
                                        context=context)
            context.job_queue.run_daily(save_config, time=datetime.time(20, 59, 59, 59), context=context)
        if 'Главное меню' not in update['message']['text'] and 'main_menu' not in update['message']['text']:
            if 'user' not in context.chat_data.keys():
                tz = datetime.timezone(datetime.timedelta(hours=3))
                tzn = 3
                if 'tz' in context.bot_data.keys():
                    tz = context.bot_data['tz']
                    tzn = context.bot_data['tz_int']
                if 'users' not in context.bot_data.keys():
                    context.chat_data['user'] = User(update, tz, tzn, db_sess)
                    context.chat_data['user'].create_info(update, BANNEDUSERS,
                                                          SUPERUSERS, db_sess)
                else:
                    if update.message.chat_id not in context.bot_data['users']:
                        context.chat_data['user'] = User(update, tz, tzn, db_sess)
                        context.chat_data['user'].create_info(update, BANNEDUSERS,
                                                              SUPERUSERS, db_sess)
                    else:
                        context.chat_data['user'] = context.bot_data['users'][int(update.message.chat_id)]
            if context.chat_data['user'].user_id in BANNEDUSERS:
                raise AccessError(context, update.message.chat_id)
            if 'users' not in context.bot_data.keys():
                context.bot_data['tz'] = datetime.timezone(datetime.timedelta(hours=3))
                context.bot_data['tz_int'] = 3
                context.bot_data['booked'] = 0
                context.bot_data['all_books'] = 0

                # context.job_queue.run_daily(analyze, time=datetime.time(23, 58), context=context)
                # context.job_queue.run_daily(backup, time=datetime.time(23, 59), context=context)
                context.bot_data['users'] = {context.chat_data['user'].user_id: context.chat_data['user']}
            else:
                if context.chat_data['user'].user_id not in context.bot_data['users'].keys():
                    context.bot_data['users'][context.chat_data['user'].user_id] = context.chat_data['user']
                else:
                    context.bot_data['users'][context.chat_data['user'].user_id].create_info(update, BANNEDUSERS,
                                                                                             SUPERUSERS, db_sess)
            if 'feedbacks' not in context.bot_data.keys():
                context.bot_data['feedbacks'] = {}
            if 'info' not in context.bot_data.keys():
                context.bot_data['info'] = {'description': 'Я очень известный кто-то приходите ко мне',
                                            'number': '80000000000', 'address': 'Москва, ул. Пушкина'}
            context.chat_data['keyboard'] = Buttons(update['message']['chat']['id'])
            context.chat_data['keyboard'].service(master)
            context.chat_data['keyboard'].set_calendar(calendar)
            context.chat_data['keyboard'].set_tz(context.bot_data['tz'], context.bot_data['tz_int'])
            if context.chat_data['user'].user_id in SUPERUSERS:
                context.chat_data['keyboard'].admin_panel(SUPERUSERS)
            context.chat_data['sure'] = False
            context.chat_data['feedback'] = False
            context.chat_data['phone'] = False
            context.chat_data['after_phone'] = False
            context.chat_data['change_phone'] = False
            context.chat_data['set_phone'] = False
            context.chat_data['cancel'] = False
            text = 'Привет! Это бот, который поможет Вам записаться на приём к мастеру.\n' \
                   'Выберите действие, и я Вам помогу!\n\n' \
                   'Обращайтесь к подсказкам на клавиатуре, они Вам помогут. '
        else:
            text = 'Что-то ещё? Выберите подсказку /Контакты, чтобы узнать о нас больше!'
            context.chat_data['keyboard'].service_id = 0
            context.chat_data['keyboard'].master_id = 0
            context.chat_data['feedback'] = False
            context.chat_data['phone'] = False
            context.chat_data['cancel'] = False
            context.chat_data['change_phone'] = False
        context.chat_data['change_phone'] = False
        context.chat_data['book'] = False
        context.chat_data['app'] = False
        context.chat_data['file'] = False
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].create('start')
        reply_keyboard = context.chat_data['keyboard'].keyboard
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True,
                                     input_field_placeholder='Выберите действие из подсказок')
        context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)
    except AccessError:
        pass
    except Exception as e:
        print(e)
        context.bot.send_message(
            text='Произошла ошибка, пропишите /start для перезапуска или /manager для связи с менеджером',
            chat_id=update.message.chat_id)


def load_config(context, update=''):
    global SUPERUSERS, BANNEDUSERS, master

    flag = True
    if update:
        variable = context
        context = update
        update = variable
        if not context.chat_data['keyboard'].is_admin(update.message.chat_id):
            flag = False
            context.bot.send_message(text='Нет доступа.', chat_id=update.message.chat_id)
    if flag:
        # +system -> +master -> +services -> users -> events -> feedbacks -> notif
        system = db_sess.query(System).first()
        users = db_sess.query(UserRes).all()
        services = db_sess.query(ServiceRes).all()
        notifications = db_sess.query(NotifRes).all()
        masters = db_sess.query(MasterRes).all()
        feedbacks = db_sess.query(Feedback).all()
        events = db_sess.query(EventRes).all()
        # system load
        context.bot_data['all_books'] = system.all_posts
        context.bot_data['booked'] = system.telegram_posts
        context.bot_data['tz_int'] = system.timezone_int
        context.bot_data['tz'] = datetime.timezone(datetime.timedelta(hours=int(system.timezone_int)))
        if system.banned_users:
            for user_id in system.banned_users.split(';'):
                if int(user_id) not in BANNEDUSERS:
                    BANNEDUSERS.append(int(user_id))
        if system.superusers:
            for user_id in system.superusers.split(';'):
                if int(user_id) not in SUPERUSERS:
                    SUPERUSERS.append(int(user_id))
        context.bot_data['info'] = {'description': system.about,
                                    'number': system.phone, 'address': system.title}
        event_result = {}

        for event_load_info in events:
            event_result[event_load_info.id] = (
                event_load_info.reg_time, event_load_info.start_time, event_load_info.end_time,
                event_load_info.user_id, event_load_info.master_id, event_load_info.service_id, db_sess,
                event_load_info.event_id)
            db_sess.delete(event_load_info)
        masters_to_append = []
        for master_load_info in masters:
            masters_to_append.append(
                [(master_load_info.mastername, master_load_info.calendarId, db_sess),
                 (master_load_info.services.split(';') if master_load_info.services else master_load_info.services)])
            db_sess.delete(master_load_info)
        services_res = {}
        for service_load_info in services:
            info = [service_load_info.servicename, db_sess, service_load_info.master_id, service_load_info.duration]
            services_res[service_load_info.id] = info
            db_sess.delete(service_load_info)
        for mst in masters_to_append:
            master_obj = Master(*mst[0])
            master.append(master_obj)
            for service_id in mst[1]:
                info = services_res[int(service_id)]
                master_obj.add_service(Service(info[0], info[1], master_obj, info[3]), db_sess)

        user_info = []
        for user_load_ifo in users:
            user_info.append(
                [context.bot_data['tz'], context.bot_data['tz_int'], user_load_ifo.user_id, user_load_ifo.name,
                 user_load_ifo.surname, user_load_ifo.user_name, user_load_ifo.is_admin,
                 user_load_ifo.is_banned,
                 user_load_ifo.phone, user_load_ifo.reg_time, user_load_ifo.events])
            db_sess.delete(user_load_ifo)
        if 'users' not in context.bot_data.keys():
            context.bot_data['users'] = {}
        for user_ in user_info:
            user = User('', user_[0], user_[1], db_sess, load=True, user_id=user_[2], name=user_[3], surname=user_[4],
                        username=user_[5], is_admin=user_[6], is_banned=user_[7], phone=user_[8], reg_time=user_[9])
            if user_[10]:
                for ev_id in user_[10].split(';'):
                    ev = Event(*event_result[int(ev_id)], special_id=True)
                    user.add_event(ev, db_sess)
            context.bot_data['users'][int(user_[2])] = user
        if 'feedbacks' not in context.bot_data.keys():
            context.bot_data['feedbacks'] = {}
        for fdb in feedbacks:
            context.bot_data['feedbacks'][int(fdb.user_id)] = fdb.content
        for notice in notifications:
            if notice.trigger_func.split(':')[1] == 'task':
                due = (notice.trigger - datetime.datetime.utcnow()).total_seconds()
                chat_id = notice.context
                name = notice.name
                context.job_queue.run_once(
                    task,
                    due,
                    context=chat_id,
                    name=name
                )
            elif notice.trigger_func.split(':')[1] == 'feedback_note':
                due = (notice.trigger - datetime.datetime.utcnow()).total_seconds()
                chat_id = notice.context
                name = notice.name
                context.job_queue.run_once(
                    feedback_note,
                    due,
                    context=chat_id,
                    name=name
                )
        if update:
            context.bot.send_message(text='Config применён к системе.',
                                     chat_id=update.message.chat_id)


def save_config(context, update=''):
    flag = True
    if update:
        variable = context
        context = update
        update = variable
        if not context.chat_data['keyboard'].is_admin(update.message.chat_id):
            flag = False
            context.bot.send_message(text='Нет доступа.',
                                     chat_id=update.message.chat_id)

    if flag:
        system = System(
            last_update=dt,
            all_posts=context.bot_data['all_books'],
            telegram_posts=context.bot_data['booked'],
            all_users=len(context.bot_data['users']),
            timezone_int=int(context.bot_data['tz_int']),
            banned_users=';'.join(list(map(lambda x: str(x), BANNEDUSERS))),
            superusers=';'.join(list(map(lambda x: str(x), SUPERUSERS))),
            title=context.bot_data['info']['address'],
            phone=context.bot_data['info']['number'],
            about=context.bot_data['info']['description'],
        )
        db_sess.add(system)
        for user_id in context.bot_data['feedbacks']:
            if len(context.bot_data['feedbacks'][user_id]) == 1:
                feedback = Feedback(
                    user_id=int(user_id),
                    content=context.bot_data['feedbacks'][user_id][0]
                )
                db_sess.add(feedback)
            else:
                for com in context.bot_data['feedbacks'][user_id]:
                    feedback = Feedback(
                        user_id=int(user_id),
                        content=com
                    )
                    db_sess.add(feedback)
        current_jobs = context.job_queue.jobs()
        for job in current_jobs:
            if '.' in job.name:
                ctx = job.context
                notif = NotifRes(
                    context=ctx,
                    name=job.job.name,
                    trigger=job.job.next_run_time,
                    system_id=job.job.id,
                    trigger_func=job.func_ref,
                )
                db_sess.add(notif)
        db_sess.commit()
        if update:
            context.bot.send_message(text='Config сохранён. /import_config - чтобы посмотреть database.',
                                     chat_id=update.message.chat_id)
        """
        repo = git.Repo(os.getcwd())
        files = repo.git.diff(None, name_only=True)
        for f in files.split('\n'):
            if f != 'main.py':
                repo.git.add(f)
        print(files)
        username = "Mnedo"
        password = "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"
        repo = Repo(os.getcwd())
        origin = repo.remote(name="origin")
    
        remote = f"https://{username}:{password}@github.com/Mnedo/bookbot2.0.git"
        os.system(f"git remote add bookbot2.0 {remote}")
        origin.push()
    
        #repo.git.commit('-m', 'test commit', author='Mnedo <Basecam@yandex.ru>')
        #origin = repo.remote(name='origin')
        #origin.push()
        """


def import_config(update, context):
    if context.chat_data['keyboard'].is_admin(update.message.chat_id):
        context.bot.send_message(text='Это активная база данных. Будьте аккуратны изменяя ее.',
                                 chat_id=update.message.chat_id)
        context.bot.send_document(chat_id=update.message.chat_id, document=open('database.db', 'rb'),
                                  filename='База_данных_BookBot.db')
    else:
        context.bot.send_message(text='Нет доступа.',
                                 chat_id=update.message.chat_id)


def load_cnf(update, context):
    if context.chat_data['keyboard'].is_admin(update.message.chat_id):

        if update.message.caption == '/load_config':
            file_info = context.bot.get_file(update.message.document.file_id)
            file = get(file_info.file_path).content
            db = open('database.db', 'wb')
            db.write(file)
            db.close()
            context.bot.send_message(text='База данных обновлена', chat_id=update.message.chat_id)
    else:
        context.bot.send_message(text='Нет доступа.',
                                 chat_id=update.message.chat_id)


def insrt(update, context):
    if context.chat_data['keyboard'].is_admin(update.message.chat_id):
        context.bot.send_message(text='Отправьте базу данных с этой подписью.', chat_id=update.message.chat_id)
    else:
        context.bot.send_message(text='Нет доступа.',
                                 chat_id=update.message.chat_id)


def analyze(context):
    global master

    ids = []
    for key in master:
        ids.append(key.calendarId)
    for id in ids:
        res = calendar.get_events_list(datetime.datetime.now(tz=context.bot_data['tz']), id)
        context.bot_data['booked'] += res[0]
        context.bot_data['all_books'] += res[1]


def makemigration(update, context):
    global master, SUPERUSERS, BANNEDUSERS

    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            if context.args:
                flag = context.args[0]
                if flag == '-f':
                    context.chat_data['file'] = True
                    context.bot.send_message(text='В ожидании json файла.',
                                             chat_id=update.message.chat_id)
                elif flag == '-clear':
                    data = json.load(open('migrations.json'))
                    data = {}
                    with open('migrations.json', 'w') as file:
                        json.dump(data, file, ensure_ascii=False,
                                  indent=2, sort_keys=False)
                        file.close()
                    context.bot.send_message(text='База данных очищена, приятной модерации.',
                                             chat_id=update.message.chat_id)
                else:
                    context.bot.send_message(text='Неизвестный флаг. Ознакомьтесь с документацией.',
                                             chat_id=update.message.chat_id)
            else:
                data = json.load(open('migrations.json'))
                dct = {}
                users = {}
                masters = {}
                for key in master:
                    masters[key] = dict(master[key])
                for user_id in context.bot_data['users']:
                    users[user_id] = dict(context.bot_data['users'][user_id])
                bot_data = {'timezone': str(context.bot_data['tz_int']),
                            'info': context.bot_data['info'], 'users': users,
                            'feedbacks': context.bot_data['feedbacks'],
                            'masters': masters, 'SUPERUSERS': SUPERUSERS, 'BANNEDUSERS': BANNEDUSERS}
                dct['bot_data'] = bot_data
                data[datetime.datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')] = dct
                with open('migrations.json', 'w') as file:
                    json.dump(data, file, ensure_ascii=False,
                              indent=2, sort_keys=False)
                file.close()
                context.bot.send_message(text='Миграция успешно выполнена. Ознакомьтесь с миграциями.',
                                         chat_id=update.message.chat_id)
                context.bot.send_document(chat_id=update.message.chat_id, document=open('migrations.json', 'rb'),
                                          filename='migrations.json')
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)


def applymigration(update, context):
    global master, SUPERUSERS, BANNEDUSERS

    data = json.load(open('migrations.json'))
    keys = data.keys()
    i = 0
    key_res = []
    for key in keys:
        key_res.append([i, key])
        i += 1
    try:

        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            key = int(context.args[0])
            dt = data[key_res[key][1]]['bot_data']
            for id in dt['SUPERUSERS']:
                if id not in SUPERUSERS:
                    SUPERUSERS.append(id)
            for id in dt['BANNEDUSERS']:
                if id not in BANNEDUSERS:
                    BANNEDUSERS.append(id)
            for mst in dt['masters']:
                mt = Master(dt['masters'][mst]['name'], dt['masters'][mst]['calendarID'], len(master) + 1)
                for serb in dt['masters'][mst]['services']:
                    mt.add_service(dt['masters'][mst]['services'][serb]['name'],
                                   dt['masters'][mst]['services'][serb]['duration'])
                master_list = []
                for el in master.keys():
                    master_list.append(master[el])
                if mt not in master_list:
                    master[len(master) + 1] = mt
            for user_id in dt['users']:
                if int(user_id) not in context.bot_data['users'].keys():
                    user_data = dt['users'][user_id]
                    events = []
                    if user_data['events']:
                        for el in user_data['events']:
                            event = Event(datetime.datetime.strptime(el['registration_time'], '%d.%m.%Y %H:%M:%S'),
                                          datetime.datetime.strptime(el['start_time'], '%d.%m.%Y %H:%M:%S'),
                                          datetime.datetime.strptime(el['end_time'], '%d.%m.%Y %H:%M:%S'),
                                          el['user_id'],
                                          el['master'], el['service']['service_name'], el['has_notified'])
                            events.append(event)
                    user = User(int(user_data['id']), int(user_data['id']),
                                datetime.timezone(datetime.timedelta(hours=int(dt['timezone']))), int(dt['timezone']))
                    user.name = user_data['name']
                    user.surname = user_data['surname']
                    user.is_admin = user_data['is_admin']
                    user.is_banned = user_data['is_banned']
                    user.phone = user_data['phone']
                    user.events = events
                    user.reg_time = datetime.datetime.strptime(user_data['registration_time'], '%H:%M %d.%m.%Y')
                    context.bot_data['users'][int(user_id)] = user
                else:
                    user_data = dt['users'][user_id]
                    user = context.chat_data['user']
                    user.is_admin = user_data['is_admin']
                    user.is_banned = user_data['is_banned']
                    user.reg_time = datetime.datetime.strptime(user_data['registration_time'], '%H:%M %d.%m.%Y')
                    for el in user_data['events']:
                        master_id = el['master']
                        for eln in master_list:
                            if eln.id == master_id:
                                old_master = eln
                        for eln in master:
                            if master[eln] == old_master:
                                master_id = master[eln].id

                        event = Event(datetime.datetime.strptime(el['registration_time'], '%d.%m.%Y %H:%M:%S'),
                                      datetime.datetime.strptime(el['start_time'], '%d.%m.%Y %H:%M:%S'),
                                      datetime.datetime.strptime(el['end_time'], '%d.%m.%Y %H:%M:%S'), el['user_id'],
                                      master_id, el['service']['service_name'], el['has_notified'])
                        user.events.append(event)
            for user_id in dt['feedbacks']:
                if int(user_id) not in context.bot_data['feedbacks']:
                    context.bot_data['feedbacks'][int(user_id)] = dt['feedbacks'][user_id]
                else:
                    for el in dt['feedbacks'][user_id]:
                        context.bot_data['feedbacks'][int(user_id)].append(el)
            context.bot_data['info']['description'] = dt['info']['description']
            context.bot_data['info']['number'] = dt['info']['number']
            context.bot_data['info']['address'] = dt['info']['address']

            context.bot.send_message(text='Миграция завершена.',
                                     chat_id=update.message.chat_id)
        else:
            raise AccessError
    except (ValueError, IndexError):
        ids = 'Доступные записи:\n'
        for el in key_res:
            ids += '{} - {}\n'.format(el[0], datetime.datetime.strptime(el[1], '%d.%m.%Y %H:%M:%S').strftime(
                '%H:%M:%S | %d-%m-%Y'))
        context.bot.send_message(text='Использование: /applymigration <ID>\n{}'.format(ids),
                                 chat_id=update.message.chat_id)
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)


def appointment(update, context):
    context.chat_data['app'] = True
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    context.chat_data['phone'] = False
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('master')
    text = 'Выберите мастера, к которому хотите попасть на приём'
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)


def correct_mobile(message):
    message = list(message)
    st = '+1234567890'
    for rl in message:
        if rl not in st:
            return False
    if '+' in message:
        if message.index('+') == 0:
            if message[1] == '7':
                if len(message) == 12:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        if message[0] == '8':
            if len(message) == 11:
                return True
            else:
                return False
        else:
            return False


def handler(update, context):
    global master

    context.chat_data['keyboard'].reset()
    if context.chat_data['book']:
        context.chat_data['book'] = False
        if '-' in update.message.text and update.message.text.count(':') == 2:
            if int(update.message.text.split(':')[0]) in context.chat_data['keyboard'].range:
                context.chat_data['keyboard'].set_time(update.message.text)
                context.chat_data['keyboard'].reset()
                if context.chat_data['user'].phone and context.chat_data['user'].phone != '0':
                    context.chat_data['keyboard'].create('sure')
                    reply_keyboard = context.chat_data['keyboard'].keyboard
                    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
                    context.chat_data['sure'] = True
                    context.bot.send_message(text='Уверены, что хотите записаться?', chat_id=update.message.chat_id,
                                             reply_markup=markup)
                else:
                    context.chat_data['keyboard'].reset()
                    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton('/Ввести в ручную')], [
                        KeyboardButton('/Отправить свой контакт\n(рекомендуем)',
                                       request_contact=True)]],
                                                 one_time_keyboard=False, resize_keyboard=True)
                    context.bot.send_message(text='Выберите вариант ввода телефона.',
                                             chat_id=update.message.chat_id, reply_markup=markup)
    elif context.chat_data['sure']:
        context.chat_data['sure'] = False
        if update.message.text == 'Да':
            event = Event(datetime.datetime.strptime(
                datetime.datetime.now(tz=context.bot_data['tz']).strftime('%Y-%m-%d %H:%M:S'), '%Y-%m-%d %H:%M:S'),
                context.chat_data['keyboard'].timedate,
                context.chat_data['keyboard'].timedate + datetime.timedelta(
                    minutes=int(60 * float(context.chat_data['keyboard'].service_id.duration))),
                context.chat_data['user'].user_id, context.chat_data['keyboard'].master_id,
                context.chat_data['keyboard'].service_id, db_sess)
            context.chat_data['user'].add_event(event, db_sess)
            context.chat_data['user'].create_info(update, BANNEDUSERS, SUPERUSERS, db_sess)
            chat_id = update.message.chat_id
            tmd = []
            for el in context.chat_data['user'].events:
                ddt = datetime.datetime.now(tz=context.bot_data['tz'])
                ddt = datetime.datetime.strptime(ddt.strftime('%Y-%m-%d %H:%M:S'), '%Y-%m-%d %H:%M:S')
                elm = el.reg_time
                delta = ddt - elm
                if delta < datetime.timedelta(hours=1):
                    tmd.append(el)
            if len(tmd) > 2:
                del context.chat_data['user'].events[-1]
                reply_keyboard = [['/Главное меню']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
                text = 'Вы записываетесь слишком часто за последний час. Повторите попытку позже или обратитесь на горячую линюю.'
                context.bot.send_message(text=text, chat_id=update.message.chat_id,
                                         reply_markup=markup)
            else:
                context.chat_data['book'] = False
                ddt = datetime.datetime.strptime(ddt.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                delta = event.start_time - ddt
                due = int((delta - datetime.timedelta(
                    hours=1)).total_seconds())
                context.job_queue.run_once(
                    task,
                    due,
                    context=chat_id,
                    name=str(chat_id) + str(event)
                )
                delta = event.end_time - ddt
                due = int((delta + datetime.timedelta(
                    hours=int(notification))).total_seconds())
                context.job_queue.run_once(
                    feedback_note,
                    due,
                    context=chat_id,
                    name=str(chat_id) + str(event)
                )
                time = event.start_time
                timeend = event.end_time
                ev_id = calendar.book(time, timeend, context.chat_data['user'].book_info(event), event,
                                      context.chat_data['keyboard'].calendarId, context.chat_data['user'])
                event.set_eventid(ev_id, db_sess)
                reply_keyboard = [['/Главное меню']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
                text = 'Мы будем вас ждать {}!'.format(str(event))
                context.chat_data['keyboard'].reset()
                context.bot.send_message(text=text, chat_id=update.message.chat_id,
                                         reply_markup=markup)
        else:
            context.chat_data['book'] = True
            context.chat_data['keyboard'].reset()
            context.chat_data['keyboard'].create('time')
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.bot.send_message(text='В какое время Вас ждать?', chat_id=update.message.chat_id,
                                     reply_markup=markup)
    elif context.chat_data['phone']:
        context.chat_data['keyboard'].reset()
        context.chat_data['phone'] = False
        if correct_mobile(update.message.text):
            context.chat_data['after_phone'] = True
            context.chat_data['cancel'] = False
            context.chat_data['keyboard'].create('sure')
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.chat_data['sure'] = True
            context.chat_data['feedback'] = False
            context.chat_data['phone'] = False
            context.chat_data['user'].phone = update.message.text
            context.chat_data['user'].create_info(update, BANNEDUSERS, SUPERUSERS, db_sess)
            context.bot.send_message(text='Уверены, что хотите записаться?', chat_id=update.message.chat_id,
                                     reply_markup=markup)
        else:
            context.chat_data['keyboard'].create('sure')
            reply_keyboard = context.chat_data['keyboard'].keyboard
            context.chat_data['cancel'] = True
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            context.bot.send_message(text='Телефон не соответствует требованиям, отменить запись?',
                                     chat_id=update.message.chat_id,
                                     reply_markup=markup)
    elif context.chat_data['cancel']:
        context.chat_data['keyboard'].reset()
        context.chat_data['cancel'] = False
        if update.message.text == 'Да':
            context.chat_data['keyboard'].master_id = 0
            context.chat_data['keyboard'].service_id = ''
            text = 'Что-то ещё? Выберите подсказку /Контакты, чтобы узнать о нас больше!'
            context.chat_data['keyboard'].reset()
            context.chat_data['keyboard'].create('start')
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)
        else:
            context.chat_data['phone'] = True
            context.bot.send_message(text='Введите номер ещё раз.', chat_id=update.message.chat_id)
    elif context.chat_data['after_phone']:
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].create('sure')
        reply_keyboard = context.chat_data['keyboard'].keyboard
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        context.chat_data['sure'] = True
        context.chat_data['feedback'] = False
        context.chat_data['after_phone'] = False
        context.chat_data['phone'] = False
        context.chat_data['cancel'] = False
        context.bot.send_message(text='Уверены, что хотите записаться?', chat_id=update.message.chat_id,
                                 reply_markup=markup)
    elif context.chat_data['change_phone']:
        context.chat_data['change_phone'] = False
        if update.message.text == 'Да':
            context.chat_data['set_phone'] = True
            context.bot.send_message(text='Оставьте свой телефон для связи без разделительных знаков.',
                                     chat_id=update.message.chat_id)
        else:
            context.chat_data['keyboard'].reset()
            context.chat_data['keyboard'].create('account')
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.bot.send_message(text='Вы в личном кабинете.',
                                     chat_id=update.message.chat_id, reply_markup=markup)
    elif context.chat_data['set_phone']:
        context.chat_data['set_phone'] = False
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].create('account')
        if correct_mobile(update.message.text):
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.chat_data['feedback'] = False
            context.chat_data['user'].phone = update.message.text
            context.chat_data['user'].create_info(update, BANNEDUSERS, SUPERUSERS, db_sess)
            context.bot.send_message(text='Телефон успешно изменён.', chat_id=update.message.chat_id,
                                     reply_markup=markup)
        else:
            context.chat_data['change_phone'] = True
            context.chat_data['keyboard'].reset()
            context.chat_data['keyboard'].create('sure')
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.bot.send_message(text='Телефон не правильный, уверены, что хотите сменить его?',
                                     chat_id=update.message.chat_id,
                                     reply_markup=markup)
    elif context.chat_data['feedback']:
        if context.chat_data['user'].user_id not in context.bot_data['feedbacks'].keys():
            context.bot_data['feedbacks'][context.chat_data['user'].user_id] = [update.message.text]
        else:
            context.bot_data['feedbacks'][context.chat_data['user'].user_id].append(update.message.text)
        context.chat_data['feedback'] = False
        context.bot.send_message(text='Спасибо за отзыв!', chat_id=update.message.chat_id)
    elif not context.chat_data['keyboard'].master_id and context.chat_data['app']:
        for mst in master:
            if mst.name == update.message.text:
                context.chat_data['keyboard'].calendarId = mst.calendarId
                context.chat_data['keyboard'].master_id = mst
                break
        if context.chat_data['keyboard'].master_id:
            context.chat_data['keyboard'].set(db_sess)
            context.chat_data['keyboard'].create('service')
            text = 'Выберите услугу'
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)
        else:
            context.bot.send_message(text='Такого мастера нет, выберите вариант из подсказок',
                                     chat_id=update.message.chat_id)
    elif not context.chat_data['keyboard'].service_id and context.chat_data['app']:
        context.chat_data['book'] = False
        ftr = list(map(lambda x: int(x),
                       ';'.join(list(map(lambda x: str(x.id), context.chat_data['keyboard'].master_id.services))).split(
                           ';')))
        svss = []
        for id in ftr:
            qw = db_sess.query(ServiceRes).filter(ServiceRes.id == id).first()
            if qw:
                svss.append(qw)
        for service in svss:
            if service.servicename == update.message.text:
                context.chat_data['keyboard'].service_id = service
        if context.chat_data['keyboard'].service_id:
            context.chat_data['keyboard'].create('appointment')
            text = 'Выберите день, в который Вы сможете к нам прийти'
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)
        else:
            context.bot.send_message(text='Такой услуги нет, выберите из подсказок', chat_id=update.message.chat_id)
    else:
        context.bot.send_message(text='Кажется, я Вас не понимаю',
                                 chat_id=update.message.chat_id)


def task(context):
    job = context.job
    date = ':'.join(''.join(job.name.split(str(job.context))).split(':')[:2])
    context.bot.send_message(job.context, text='Напоминаю, что мы ждем вас {} на приёме!'.format(date))


def feedback_note(context):
    job = context.job
    date = ' - '.join(''.join(job.name.split(str(job.context))).split(' - ')[:2])
    service = job.name.split(' - ')[-1]
    mainrow = [['/Оставить отзыв'], ['/Главное меню']]
    markup = ReplyKeyboardMarkup(mainrow, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(job.context,
                             text='Вы были {} на приёме. Что скажите о своих впечатлениях? Как {}?'.format(date,
                                                                                                           service),
                             reply_markup=markup)


def registration(update, context):
    message = update.message.text
    if '.' in message:
        weekday = message.split()[-1]
        context.chat_data['keyboard'].set_weekday(weekday)
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].create('registration')
        reply_keyboard = context.chat_data['keyboard'].keyboard
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        context.bot.send_message(text='Когда бы вы могли подойти?', chat_id=update.message.chat_id,
                                 reply_markup=markup)
    else:
        context.bot.send_message(text='Используй подсказку.', chat_id=update.message.chat_id)


def time(update, context):
    context.chat_data['book'] = True
    message = update.message.text
    if '-' in message:
        delta = message.split()[-1].split('-')
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].set_range(delta)
        context.chat_data['keyboard'].create('time')
        reply_keyboard = context.chat_data['keyboard'].keyboard
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        context.bot.send_message(text='В какое время Вас ждать?', chat_id=update.message.chat_id,
                                 reply_markup=markup)
    else:
        context.bot.send_message(text='Используй подсказку.', chat_id=update.message.chat_id)


def back_week(update, context):
    context.chat_data['book'] = False
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('appointment')
    text = 'Выберите день, в который Вы сможете к нам прийти'
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)


def share_contact(update, context):
    context.chat_data['user'].phone = update.message.contact.phone_number
    context.chat_data['user'].create_info(update, BANNEDUSERS, SUPERUSERS, db_sess)
    if context.chat_data['change_phone']:
        context.chat_data['change_phone'] = False
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].create('account')
        reply_keyboard = context.chat_data['keyboard'].keyboard
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        context.bot.send_message(text='Вы в личном кабинете. Телефон успешно изменён.',
                                 chat_id=update.message.chat_id, reply_markup=markup)

    else:
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].create('sure')
        reply_keyboard = context.chat_data['keyboard'].keyboard
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        context.chat_data['sure'] = True
        context.bot.send_message(text='Уверены, что хотите записаться?', chat_id=update.message.chat_id,
                                 reply_markup=markup)
    context.chat_data['feedback'] = False
    context.chat_data['phone'] = False
    context.chat_data['cancel'] = False


def self_contact(update, context):
    if context.chat_data['change_phone']:
        context.chat_data['set_phone'] = True
    else:
        context.chat_data['phone'] = True
    context.chat_data['keyboard'].reset()
    context.chat_data['change_phone'] = False
    markup = ReplyKeyboardRemove()
    context.bot.send_message(text='Оставьте свой телефон без разделительных знаков.',
                             chat_id=update.message.chat_id, reply_markup=markup)


def change_phone(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['change_phone'] = True
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('sure')
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton('/Ввести в ручную')], [
        KeyboardButton('/Отправить свой контакт\n(рекомендуем)',
                       request_contact=True)]],
                                 one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text='Выберите вариант ввода телефона.',
                             chat_id=update.message.chat_id, reply_markup=markup)


def variant(update, context):
    if update['message']['text'].count(' ') >= 7:
        dtm_start = datetime.datetime.strptime(
            ' '.join([update['message']['text'].split()[1], update['message']['text'].split()[3]]), '%d.%m.%Y %H:%M')
        dtm_end = datetime.datetime.strptime(
            ' '.join([update['message']['text'].split()[1], update['message']['text'].split()[5]]), '%d.%m.%Y %H:%M')
        name = update['message']['text'].split(' - ')[-1]

        reply_keyboard = [['/Контакты', '/Главное меню']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

        for el in context.chat_data['user'].events:
            if el.start_time == dtm_start and el.end_time == dtm_end and name == el.service_id.servicename:
                master_f = el.master_id
                del context.chat_data['user'].events[context.chat_data['user'].events.index(el)]
                break
        context.chat_data['keyboard'].calendarId = master_f.calendarId
        context.chat_data['keyboard'].cancel(el.event_id, db_sess)
        # context.chat_data['keyboard'].sign_out(dtm_start, dtm_end)
        current_jobs = context.job_queue.get_jobs_by_name(str(update.message.chat_id) + str(el))
        for job in current_jobs:
            job.schedule_removal()
        context.chat_data['user'].create_info(update, BANNEDUSERS,
                                              SUPERUSERS, db_sess)
        context.bot.send_message(text='Запись отменена надеемся увидеть вас позже!', chat_id=update.message.chat_id,
                                 reply_markup=markup)
    else:
        context.bot.send_message(
            text='Произошла ошибка, воспользуйтесь подсказкой\nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def sign_out(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].set_context(context.chat_data['user'])
    text = context.chat_data['keyboard'].create('sign_out')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)


def helpp(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    text = """Руководство для пользователей:
Это бот, который поможет Вам узнать информацию о нас, записаться и отменить запись на приём.
Пользуйтесь подсказками на клавиатуре и командами, описанными ниже. 

Технические команды:
    /Старт - запуск диалога с ботом, перезапуск системы(в случае ошибок)
    /Записаться - меню для записи на сеанс
    /Отменить запись - меню для отмены записи
    /Контакты - узнайте немного больше о нас: информация об организации
    /Личный кабинет - управляйте своими данными: телефоны, личные данные и т.д.
    /Помощь - типичная команда /help, вы уже её читаете
    /Статус - узнайте ваш id, дату регистрации и другую информацию
    /Оставить отзыв - оставьте отзыв о боте или об оказанной услуге
    /Сменить телефон - поменяйте контактный номер для записи, для связи с вами
    /Главное меню - возвращение в главное меню (вы уже тут)
    {} 
Команды регистрирования записей(Использование вне контекста может повлечь к ошибкам, советуем пользоваться только подсказками):
    /Следующая - следующая неделя дат для регистрации
    /Назад - вернуться на прошлую страницу
    /День недели <дата> - Доступное время для записи в этот день
    /В <промежуток времени> - Выберите промежуток для записи
    /Назад к неделе - вернуться на прошлую страницу
    /Назад к расписанию <дата> - вернуться на прошлую страницу

Приятного использования!
    """.format('/admin_panel - панель для администрирования, отдельное описание внутри!\n' if context.chat_data[
        'keyboard'].is_admin(update.message.chat_id) else '\n')
    context.bot.send_message(text=text, chat_id=update.message.chat_id)


def contacts(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    text = 'Немного о нас:\n'
    text += context.bot_data['info']['description'] + '\n\n'
    text += 'Наш адреc:\n'
    text += context.bot_data['info']['address'] + '\n\n'
    text += 'Наш номер телефона:\n'
    text += context.bot_data['info']['number'] + '\n\n'
    context.bot.send_message(text=text, chat_id=update.message.chat_id)


def account(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('account')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text='Добро пожаловать в личный кабинет! Узнайте статус или смените номер.',
                             chat_id=update.message.chat_id, reply_markup=markup)


def admin(update, context):
    try:
        context.chat_data['user'].create_info(update, BANNEDUSERS, SUPERUSERS, db_sess)
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].create_admin('start')
        reply_keyboard = context.chat_data['keyboard'].keyboard
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        context.bot.send_message(
            text='Добро пожаловать в админскую панель! Выберите действие, которое хотите сделать или введите /admin для ознакомления.',
            chat_id=update.message.chat_id,
            reply_markup=markup)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def admin_info(update, context):
    txt = """Руководство для администрирования:
Используйте это меню для контроля и модерации системы, будьте аккуратны со своими решениями!

Доступные команды:
    /admin - руководство для администрации(вы уже тут)
    /user_info <user_ID> - данные об определённом пользователе
    /user_info - информация обо всех пользователях
    /main_menu - возвращение в главное меню пользователя
    /ban_user <user_ID> - добавление пользователя в чёрный список, ограничение всех действий
    /unban_user <user_ID> - удаление пользователя из чёрного списка
    /set_description <text> - установка описания организации (раздел /contacts)
    /set_contact_number <number> - установка номера организации (раздел /contacts)
    /set_address <address> - установка адреса организации (раздел /contacts)
    /add_master <master_name> <master_calendarId> - добавление мастера в систему
    /del_master <master_id> - удаление мастера из системы
    /add_service <master_id> <service_name> <service_duration> - добавление услуги в систему 
    /del_service <master_id> <service_id> - удаление услуги из системы
    /makemigration - собирает версию конфигурации системы в виде файла .json
        /makemigration -f - позволяет загрузить миграцию в систему
        /makemigration -clear - очищает систему от версий 
    /applymigration <ID> - применяет версию к системе
    /instructions - получение инструкций по настройке системы
    /data_clear - очистка базы данных от записей, которые прошли по времени
        примечание:
            Очищает пространство на сервере, но мешает собирать статистику, чистка будет производиться автоматически раз в месяц(в ручную вводить не обязательно)
    /get_feedbacks - присылает все составленные отзывы с информацией о пользователе

Приятной модерации!
    """
    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            context.bot.send_message(
                text=txt,
                chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def human_read_format(size):
    if size < 1024:
        return str(size) + 'Б'
    elif 1024 <= size < 1024 * 1024:
        return str(round(size / 1024)) + 'КБ'
    elif 1024 * 1024 <= size < 1024 * 1024 * 1024:
        return str(round(size / 1024 ** 2)) + 'МБ'
    elif 1024 * 1024 * 1024 <= size < 1024 * 1024 * 1024 * 1024:
        return str(round(size / 1024 ** 3)) + 'ГБ'


def analize_files(name):
    size = 0
    if os.path.isfile(name):
        size += os.path.getsize(name)
    else:
        for elem in os.listdir(name):
            elem = os.path.join(name, elem)
            if os.path.isfile(elem):
                size += os.path.getsize(elem)
            elif os.path.isdir(elem):
                size += analize_files(elem)
    return size


def system(update, context):
    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            txt = 'Статус системы:\n\n'
            size = 0
            for el in os.listdir():
                size += analize_files(el)
            txt += 'Размер системы: {}\n'.format(human_read_format(size))
            txt += 'Размер мигрцаий: {}\n'.format(human_read_format(analize_files('migrations.json')))
            txt += '{} - количество пользователей\n'.format(len(context.bot_data['users']))
            txt += '{}/{} записей были сделаны ботом.'.format(context.bot_data['booked'], context.bot_data['all_books'])
            context.bot.send_message(text=txt, chat_id=update.message.chat_id)
        else:
            context.bot.send_message(text='Не достаточно привелегий.', chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def user_info(update, context):
    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            txt = ''
            try:
                user_id = int(context.args[0])
                if user_id not in context.bot_data['users'].keys():
                    context.bot.send_message(
                        text='Такого пользователя не сушествует',
                        chat_id=update.message.chat_id)
                user = context.bot_data['users'][user_id]
                txt = str(user)
            except (IndexError, ValueError):
                for id in context.bot_data['users'].keys():
                    user = str(context.bot_data['users'][id])
                    txt += str(user)
                    txt += '\n\n'
            context.bot.send_message(
                text=txt,
                chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def add_master(update, context):
    global master

    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):

            master_calendarId = context.args[0]
            master_name = ' '.join(context.args[1:])
            if master_name == '' or master_calendarId == '':
                raise ValueError
            mst = Master(master_name, master_calendarId, db_sess)
            master.append(mst)
            context.bot.send_message(
                text='Мастер успешно добавлен, не забудьте о его услугах. /add_service - для инструкций.',
                chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /add_master <master_calendarId> <master_name>\n/instructions - для получения полных инструкций',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Возможно, проблема в calendarId. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def del_master(update, context):
    global master

    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            id = int(context.args[0])
            mst = db_sess.query(MasterRes).filter(MasterRes.id == master[id].id).first()
            db_sess.delete(mst)
            db_sess.commit()
            del master[int(id)]
            context.bot.send_message(
                text='Мастер успешно удалён.',
                chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        ids = ''
        i = 0
        for mst in master:
            ids += '{} - {}\n'.format(i, mst.name)
            i += 1
        context.bot.send_message(
            text='Использование: /del_master <master_id>\nВыберите id доступного мастера:\n{}'.format(ids),
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Возможно, проблема в Id. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def add_service(update, context):
    global master

    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            id = int(context.args[0])
            duration = context.args[1]
            name = ' '.join(context.args[2:])
            if id == '' or duration == '' or name == '':
                raise ValueError
            master[id].add_service(Service(name, db_sess, master[id], duration), db_sess)
            context.bot.send_message(
                text='Услуга успешно добавлена.',
                chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        ids = ''
        i = 0
        for mst in master:
            ids += '{} - {}\n'.format(i, mst.name)
            i += 1
        context.bot.send_message(
            text='Использование: /add_service <master_id> <service_duration> <service_name>\nВыберите id доступного мастера:\n{}'.format(
                ids),
            chat_id=update.message.chat_id)
    except Exception as e:
        print(e)
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Возможно, проблема в Id. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def del_service(update, context):
    global master

    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            master_id = int(context.args[0])
            service_id = int(context.args[1])
            if master_id == '' or service_id == '':
                raise ValueError
            mst = master[master_id]
            service = mst.services[service_id]
            sv = db_sess.query(ServiceRes).filter(ServiceRes.id == service.id).first()
            db_sess.delete(sv)
            db_sess.commit()
            del mst.services[mst.services.index(service)]
            context.bot.send_message(
                text='Услуга успешно удалена.',
                chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        ids = ''
        j = 0
        for mst in master:
            ids += '{} - {}\n'.format(j, mst.name)
            if mst.services:
                i = 0
                for serv in mst.services:
                    ids += '   {} - {}\n'.format(str(i), serv.service_name)
                    i += 1
                j += 1
        context.bot.send_message(
            text='Использование: /del_service <master_id> <service_id>\nВыберите id доступной услуги и мастера:\n{}'.format(
                ids),
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Возможно, проблема в Id. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def add_superuser(update, context):
    global SUPERUSERS
    try:

        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            user_id = context.args[0]
            if int(user_id) not in SUPERUSERS:
                SUPERUSERS.append(int(user_id))
            context.bot.send_message(
                text='Суперпользователь успешно добавлен',
                chat_id=update.message.chat_id)
            context.bot.send_message(
                text='Поздравляем, Вы стали админом! Пропишите /start для добавления админской панели.',
                chat_id=int(user_id))
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /add_superuser <user_id>',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nПроверьте id.',
            chat_id=update.message.chat_id)


def del_superuser(update, context):
    global SUPERUSERS
    try:

        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            user_id = context.args[0]
            if int(user_id) in SUPERUSERS and int(user_id) != SUPERUSERS[0]:
                del SUPERUSERS[SUPERUSERS.index(int(user_id))]
                txt = 'Суперпользователь успешно удалён'
            else:
                txt = 'Такого пользователя не существует, проверьте id'
            context.bot.send_message(
                text=txt,
                chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /del_superuser <user_id>',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def set_timezone(update, context):
    try:
        timezone = context.args[0]
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            context.bot_data['tz'] = datetime.timezone(datetime.timedelta(hours=int(timezone)))
            context.bot_data['tz_int'] = int(timezone)
            context.bot_data['users'][update.message.chat_id].set_tz(context.bot_data['tz'], context.bot_data['tz_int'],
                                                                     db_sess)
            context.bot_data['users'][update.message.chat_id].create_info(update, BANNEDUSERS, SUPERUSERS, db_sess)
            context.chat_data['keyboard'].set_tz(context.bot_data['tz'], context.bot_data['tz_int'])
            context.bot.send_message(
                text='Часовой пояс успешно обновлён',
                chat_id=update.message.chat_id)

        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /set_timezone <timezone:hours>\ndefault: +03:00 UTC',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def ban_user(update, context):
    global SUPERUSERS, BANNEDUSERS
    try:

        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            user_id = context.args[0]
            if not user_id.isdigit():
                context.bot.send_message(
                    text='Такого id не существует.',
                    chat_id=update.message.chat_id)
            elif int(user_id) == SUPERUSERS[0]:
                raise AccessError
            elif int(user_id) not in list(map(lambda x: int(x), context.bot_data['users'].keys())):
                context.bot.send_message(
                    text='Такого id не существует.',
                    chat_id=update.message.chat_id)
            elif int(user_id) in BANNEDUSERS:
                context.bot.send_message(
                    text='Пользователь уже забанен.',
                    chat_id=update.message.chat_id)
            else:
                BANNEDUSERS.append(int(user_id))
                context.bot_data['users'][int(user_id)].is_banned = True
                context.bot.send_message(
                    text='Поздравляем с добавлением в чёрный список! Пропишите /start для перезапуска.',
                    chat_id=int(user_id))
                context.bot.send_message(
                    text='Пользователь добавлен в чёрный список',
                    chat_id=update.message.chat_id)

        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /ban_user <user_id>',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \n',
            chat_id=update.message.chat_id)


def unban_user(update, context):
    global SUPERUSERS, BANNEDUSERS
    try:

        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            user_id = context.args[0]
            if not user_id.isdigit():
                context.bot.send_message(
                    text='Такого id не существует.',
                    chat_id=update.message.chat_id)
            elif int(user_id) in BANNEDUSERS:
                del BANNEDUSERS[BANNEDUSERS.index(int(user_id))]
                txt = 'Пользователь успешно удалён из чёрного списка'
                context.bot.send_message(
                    text='С возвращением, пропишите /start для перезапуска.',
                    chat_id=int(user_id))
                context.bot_data['users'][int(user_id)].is_banned = False
            else:
                txt = 'Такого пользователя не существует, проверьте id'

            context.bot.send_message(
                text=txt,
                chat_id=update.message.chat_id)

        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /unban_user <user_id>',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def send_feedbacks(update, context):
    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            if context.bot_data['feedbacks']:
                text = 'Отзывы:\n\n'
                for key in context.bot_data['feedbacks']:
                    for post in context.bot_data['feedbacks'][key]:
                        text += post + '\n'
                    text += str(context.bot_data['users'][key]) + '\n\n'
            else:
                text = 'Отзывы отсутствуют'
            context.bot.send_message(text=text, chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def set_description(update, context):
    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            if context.args:
                mes = ' '.join(context.args)
            else:
                raise ValueError
            text = 'Описание успешно обновлено.'
            context.bot_data['info']['description'] = mes
            context.bot.send_message(text=text, chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /set_description <description>',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def set_number(update, context):
    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            mes = context.args[0]
            if correct_mobile(mes):
                context.bot_data['info']['number'] = mes
                text = 'Телефон успешно обновлён.'
                context.bot.send_message(text=text, chat_id=update.message.chat_id)
            else:
                context.bot.send_message(
                    text='Телефон не соответствует требованиям.',
                    chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /set_contact_number <number>',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def set_address(update, context):
    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            if context.args:
                mes = ' '.join(context.args)
            else:
                raise ValueError
            context.bot_data['info']['address'] = mes
            text = 'Адрес успешно обновлён.'
            context.bot.send_message(text=text, chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /set_address <address>',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


def change_phone(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['change_phone'] = True
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('sure')
    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton('/Ввести в ручную')], [
        KeyboardButton('/Отправить свой контакт\n(рекомендуем)',
                       request_contact=True)]],
                                 one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text='Выберите вариант ввода телефона.',
                             chat_id=update.message.chat_id, reply_markup=markup)


def data_clear(context, update=''):
    flag = False
    if update:
        variable = context
        context = update
        update = variable
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            flag = True
        else:
            context.bot.send_message(text='Нет доступа', chat_id=update.message.chat_id)
    if flag:
        txt = 'data_clear:\n'
        counter = 0
        valid = 0
        for id in context.bot_data['users'].keys():
            for event in context.bot_data['users'][id].events:
                valid += 1
                if event.end_time < datetime.datetime.strptime(
                        datetime.datetime.now(tz=context.bot_data['tz']).strftime('%Y-%m-%d %H:%M:%S'),
                        '%Y-%m-%d %H:%M:%S'):
                    counter += 1
                    del context.bot_data['users'][id].events[context.bot_data['users'][id].events.index(event)]
        txt += '{} posts has deleted.\n'.format(counter)
        txt += '{} posts has checked.\n'.format(valid)
        if update:
            context.bot.send_message(text=txt, chat_id=update.message.chat_id)
        else:
            print(txt)


def info(update, context):
    txt = str(context.chat_data['user'])
    context.bot.send_message(text=txt, chat_id=update.message.chat_id)


def back(update, context):
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].nextlevel -= 2
    context.chat_data['keyboard'].create('next')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text='Предлагаем выбрать из этих.', chat_id=update.message.chat_id,
                             reply_markup=markup)


def nex(update, context):
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('next')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text='Предлагаем выбрать из этих.', chat_id=update.message.chat_id,
                             reply_markup=markup)


def feedback(update, context):
    text = 'Напишите ваши впечатления, после отправки отзыв будет отмечен в нашей базе.'
    context.chat_data['feedback'] = True
    context.chat_data['sure'] = False
    context.chat_data['change_phone'] = False
    context.bot.send_message(text=text, chat_id=update.message.chat_id)


def instructions(update, context):
    global account_name

    text = """Для настройки нового календаря нужно выполнить несколько пунктов:

Пункт первый:
    Предоставление доступа к сервисному аккаунту.
    
    Настройки календаря > Доступ для отдельных пользователей > Добавить пользователя
    Адрес электронной почты сервисного аккаунта: {}
    Разрешения: Внесение изменений и предоставление доступа
    Это сервисный аккаунт, волноваться не о чём. Подробнее на фото.
    
Пункт второй:
    Получение id календаря, который нужно указать при добавлении мастера.
    
    Настройки календаря > Интеграция календаря > Идентификатор календаря
    Используйте этот id для добавления мастеров. На этом настройка завершена, смотрите фото.
    """.format(account_name)
    filename = ['images/Access.jpg', 'images/Integration.jpg']
    context.bot.send_message(text=text, chat_id=update.message.chat_id)
    context.bot.send_photo(
        update.message.chat_id,
        photo=open(filename[0], 'rb'),
        caption="Предоставление доступа. Визуальные инструкции."
    )
    context.bot.send_photo(
        update.message.chat_id,
        photo=open(filename[1], 'rb'),
        caption="Id календаря. Визуальные инструкции."
    )


def get_help(update, context):
    global phone, first_name, last_name

    context.bot.send_contact(update.message.chat_id, phone, first_name, last_name)


def create_work_week(update, context):
    global calendar

    try:
        if context.chat_data['keyboard'].is_admin(update.message.chat_id):
            start_date = datetime.datetime.strptime(context.args[0], '%d.%m.%Y')
            day = int(context.args[1])
            calendarId = context.args[2]
            for d in range(day):
                calendar.create_work_day(start_date + datetime.timedelta(hours=start_time),
                                         start_date + datetime.timedelta(hours=end_time), calendarId)
                start_date += datetime.timedelta(days=1)

            context.bot.send_message(
                text='Успешно создано.',
                chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /create_work_days <start_date> <days> <calendarId>\nФормат start_date: день.месяц.год\ndays - количество дней\n/instructions - для получения подробных инструкций',
            chat_id=update.message.chat_id)
    except Exception as e:
        print(e)
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start \nВы можете связаться с менеджером по команде /manager',
            chat_id=update.message.chat_id)


ch = EditCommandHandler()
ch.extra_handler(handler)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start, pass_chat_data=True))
ch.register("Старт", start)
ch.register("старт", start)
ch.register("Записаться", appointment)
ch.register("Сменить телефон", change_phone)
dp.add_handler(CommandHandler('appointment', appointment, pass_chat_data=True))
dp.add_handler(CommandHandler("today", registration, pass_chat_data=True))
ch.register("Сегодня", registration, have_args=True)
ch.register("Пн", registration, have_args=True)
dp.add_handler(CommandHandler("Mon", registration, pass_chat_data=True))
ch.register("Вт", registration, have_args=True)
dp.add_handler(CommandHandler("Tue", registration, pass_chat_data=True))
ch.register("Ср", registration, have_args=True)
dp.add_handler(CommandHandler("Wed", registration, pass_chat_data=True))
ch.register("Чт", registration, have_args=True)
dp.add_handler(CommandHandler("Thu", registration, pass_chat_data=True))
ch.register("Пт", registration, have_args=True)
dp.add_handler(CommandHandler("Fri", registration, pass_chat_data=True))
ch.register("Сб", registration, have_args=True)
dp.add_handler(CommandHandler("Sat", registration, pass_chat_data=True))
ch.register("Вс", registration, have_args=True)
dp.add_handler(CommandHandler("Sun", registration, pass_chat_data=True))
ch.register("В", time, have_args=True)
dp.add_handler(CommandHandler("B", time, pass_chat_data=True))
ch.register("Назад к неделе", back_week)
dp.add_handler(CommandHandler("back_week", back_week, pass_chat_data=True))
ch.register("Назад к расписанию", registration, have_args=True)
dp.add_handler(CommandHandler("back_time", registration, pass_chat_data=True))
ch.register("Ввести в ручную", self_contact)
dp.add_handler(CommandHandler("main_menu", start, pass_chat_data=True))
ch.register("Главное меню", start)
ch.register("Помощь", helpp)
ch.register("Следующая", nex)
ch.register("Назад", back)
ch.register("Статус", info)
ch.register("Оставить отзыв", feedback)
dp.add_handler(CommandHandler("set_description", set_description, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("save_config", save_config, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("update_config", load_config, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("import_config", import_config, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("set_contact_number", set_number, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("set_address", set_address, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("set_timezone", set_timezone, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("create_work_days", create_work_week, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("admin", admin_info, pass_chat_data=True))

dp.add_handler(CommandHandler("get_feedbacks", send_feedbacks, pass_chat_data=True))

dp.add_handler(CommandHandler("add_superuser", add_superuser, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("del_superuser", del_superuser, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("system", system, pass_chat_data=True))
dp.add_handler(CommandHandler("add_master", add_master, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("del_master", del_master, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("add_service", add_service, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("del_service", del_service, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("instructions", instructions, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("ban_user", ban_user, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("data_clear", data_clear, pass_chat_data=True))
dp.add_handler(CommandHandler("unban_user", unban_user, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("manager", get_help, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("user_info", user_info, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("help", helpp, pass_chat_data=True))
ch.register("Отменить запись", sign_out)
ch.register("Запись", variant, have_args=True)
dp.add_handler(CommandHandler("variant", variant, pass_chat_data=True))
dp.add_handler(CommandHandler("cancel", sign_out, pass_chat_data=True))
ch.register("Контакты", contacts)
dp.add_handler(CommandHandler("contacts", contacts, pass_chat_data=True))
ch.register("Личный кабинет", account)
dp.add_handler(CommandHandler("load_config", insrt, pass_chat_data=True))
dp.add_handler(CommandHandler("admin_panel", admin, pass_chat_data=True))
dp.add_handler(MessageHandler(Filters.document.file_extension("db"), load_cnf, pass_chat_data=True))
dp.add_handler(MessageHandler(Filters.contact, share_contact, pass_chat_data=True))
dp.add_handler(MessageHandler(Filters.text, ch, pass_chat_data=True, pass_job_queue=True))

updater.start_polling()
updater.idle()
