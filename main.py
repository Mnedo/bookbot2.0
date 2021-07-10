import json
import requests
import random
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, Updater, ConversationHandler, MessageHandler, Filters
import datetime

from EditedClasses import EditCommandHandler
from lib import Buttons
from GoogleCalendar import GoogleCalendar

REQUEST_KWARGS = {
    'urllib3_proxy_kwargs': {
        'assert_hostname': 'False',
        'cert_reqs': 'CERT_NONE',
        'username': 'user',
        'password': 'password'}
}
updater = Updater("1765029934:AAG3PWNX_bBlUtllnaK6ZWKH9fMaEp8fKrs", use_context=True,
                  request_kwargs=REQUEST_KWARGS)


class User:
    def __init__(self, user_id, chat_id):
        self.id = user_id
        self.chat = chat_id


calendar = GoogleCalendar()
SUPERUSERS = [921615186]


def admin(update, context):
    try:
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].create_admin('start')
        reply_keyboard = context.chat_data['keyboard'].keyboard
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=80)
        context.bot.send_message(
            text='Добро пожаловать в админскую панель! Выберите действие, которое хотите сделать или введите /admin для ознакомления.',
            chat_id=update.message.chat_id,
            reply_markup=markup)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
            chat_id=update.message.chat_id)


def admin_info(update, context):
    txt = ''
    txt += '/admin - команда, информирующая о возможностях бота\n'
    txt += '/add_superuser - команда, которая расширяет список пользователей, имеюших доступ к админской панели\n' \
           'примечание: /add_superuser <user_id>\nполучить id при помощи команды /info\n'
    txt += '/del_superuser - команда удаляет пользователя из админской панели\n' \
           'примечание: /del_superuser <user_id>\nполучить id при помощи команды /info\n'
    txt += '/user_info - команда даёт информацию обо всех зарегестрированых пользователях\n' \
           'примечание: /user_info <user_id>\n'
    txt += '/send_feedbacks - команда показывает список отзывов об организации, которые оставили пользователи\n'
    txt += '/send_contact_number - установка номера для личной связи с Вами\n' \
           'примечание: /send_contact_number <number>\n'
    txt += '/set_description - установка описания для раздела /contacts\n' \
           'примечание: /set_description <description>\n'
    txt += '/set_address - адресс организации для раздела /contacts\n' \
           'примечание: /set_address <address>\n'
    try:
        if context.chat_data['keyboard'].is_admin():
            context.bot.send_message(
                text=txt,
                chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
            chat_id=update.message.chat_id)


def user_info(update, context):
    try:
        if context.chat_data['keyboard'].is_admin():
            txt = ''
            try:
                user_id = int(context.args[0])
                if user_id not in context.bot_data['users'].keys():
                    context.bot.send_message(
                        text='Такого пользователя не сушествует',
                        chat_id=update.message.chat_id)
                user_reg = context.bot_data['users'][user_id]
                user = context.bot_data['users_info'][user_id][0]
                if user_reg:
                    txt += 'Пользователь:\n'
                    txt += '\n'.join([' '.join(user.split()[:2]), ' '.join(user.split()[2:])]) + '\n\n'
                    txt += 'Записи:\n'
                    for post in user_reg:
                        txt += str(post[1]).split()[0] + ' в ' + ':'.join(
                            str(post[1]).split()[1].split(':')[:2]) + ' - ' + ':'.join(
                            str(post[2]).split()[1].split(':')[
                            :2])
                        txt += '\n'
                    txt += '\n\n'
                else:
                    txt += 'Пользователь:\n'
                    txt += '\n'.join([' '.join(user.split()[:2]), ' '.join(user.split()[2:])]) + '\n\n'
                    txt += 'Записи отсутствуют\n\n'
            except (IndexError, ValueError):
                for id in context.bot_data['users'].keys():
                    user_reg = context.bot_data['users'][id]
                    user = str(context.bot_data['users_info'][id][0])
                    if user_reg:
                        txt += 'Пользователь:\n'
                        txt += '\n'.join([' '.join(user.split()[:2]), ' '.join(user.split()[2:])]) + '\n\n'
                        txt += 'Записи:\n'
                        for post in user_reg:
                            txt += str(post[1]).split()[0] + ' в ' + ':'.join(
                                str(post[1]).split()[1].split(':')[:2]) + ' - ' + ':'.join(
                                str(post[2]).split()[1].split(':')[
                                :2])
                            txt += '\n'
                        txt += '\n\n'
                    else:
                        txt += 'Пользователь:\n'
                        txt += '\n'.join([' '.join(user.split()[:2]), ' '.join(user.split()[2:])]) + '\n\n'
                        txt += 'Записи отсутствуют\n\n'
            context.bot.send_message(
                text=txt,
                chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
            chat_id=update.message.chat_id)


def add_superuser(update, context):
    global SUPERUSERS
    try:
        user_id = context.args[0]
        if context.chat_data['keyboard'].is_admin():
            SUPERUSERS.append(int(user_id))
            context.bot.send_message(
                text='Суперпользователь успешно добавлен',
                chat_id=update.message.chat_id)
            if int(user_id) in context.bot_data['users_info'].keys():
                context.bot.send_message(
                    text='Поздравляем, Вы стали админом! Пропишите /start для добавления админской панели.',
                    chat_id=context.bot_data['users_info'][int(user_id)][1])
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /add_superuser <user_id>',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
            chat_id=update.message.chat_id)


def del_superuser(update, context):
    global SUPERUSERS
    try:
        user_id = context.args[0]
        if context.chat_data['keyboard'].is_admin():
            if int(user_id) in SUPERUSERS:
                del SUPERUSERS[SUPERUSERS.index(int(user_id))]
                txt = 'Суперпользователь успешно удалён'
            else:
                txt = 'Такого пользователя не существует, проверьте id'
            context.bot.send_message(
                text=txt,
                chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /del_superuser <user_id>',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
            chat_id=update.message.chat_id)


def send_feedbacks(update, context):
    try:
        if context.chat_data['keyboard'].is_admin():
            if context.bot_data['feedbacks']:
                text = 'Отзывы:\n\n'
                for key in context.bot_data['feedbacks']:
                    for post in context.bot_data['feedbacks'][key]:
                        text += post + '\n'
                    text += context.bot_data['users_info'][key][0] + '\n\n'
            else:
                text = 'Отзывы отсутствуют'
            context.bot.send_message(text=text, chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
            chat_id=update.message.chat_id)


def set_description(update, context):
    try:
        if context.chat_data['keyboard'].is_admin():
            mes = ' '.join(update.message.text.split()[1:])
            text = 'Описание успешно обновлено.'
            context.bot_data['info']['description'] = mes
            context.bot.send_message(text=text, chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
            chat_id=update.message.chat_id)


def set_number(update, context):
    try:
        if context.chat_data['keyboard'].is_admin():
            mes = ' '.join(update.message.text.split()[1:])
            context.bot_data['info']['number'] = mes
            text = 'Телефон успешно обновлён.'
            context.bot.send_message(text=text, chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
            chat_id=update.message.chat_id)


def set_address(update, context):
    try:
        if context.chat_data['keyboard'].is_admin():
            mes = ' '.join(update.message.text.split()[1:])
            context.bot_data['info']['address'] = mes
            text = 'Адрес успешно обновлён.'
            context.bot.send_message(text=text, chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
            chat_id=update.message.chat_id)


def start(update, context):
    global SUPERUSERS, calendar
    if 'Главное меню' not in update['message']['text']:
        if 'user' not in context.chat_data.keys():
            context.chat_data['user'] = User(update['message']['chat']['id'], update.message.chat_id)
        if 'users' not in context.bot_data.keys():
            context.bot_data['users'] = {context.chat_data['user'].id: []}
        else:
            if context.chat_data['user'].id not in context.bot_data['users'].keys():
                context.bot_data['users'][context.chat_data['user'].id] = []
        if 'users_info' not in context.bot_data.keys():
            context.bot_data['users_info'] = {context.chat_data['user'].id: [get_info(update), update.message.chat_id]}
        else:
            if context.chat_data['user'].id not in context.bot_data['users_info'].keys():
                context.bot_data['users_info'][context.chat_data['user'].id] = [get_info(update),
                                                                                update.message.chat_id]
        if 'feedbacks' not in context.bot_data.keys():
            context.bot_data['feedbacks'] = {}
        if 'info' not in context.bot_data.keys():
            context.bot_data['info'] = {'description': 'Я очень известный кто-то приходите ко мне',
                                        'number': '80000000000', 'address': 'Москва, ул. Пушкина'}
        context.chat_data['keyboard'] = Buttons()
        if context.chat_data['user'].id in SUPERUSERS:
            context.chat_data['keyboard'].admin_panel()
        context.chat_data['keyboard'].set_calendar(calendar)
        context.chat_data['sure'] = False
        context.chat_data['feedback'] = False
        text = 'Привет! Это бот, который поможет Вам записаться на приём к мастеру.\n' \
               'Выберите действие, и я Вам помогу!\n\n' \
               'Обращайтесь к подсказкам на клавиатуре, они Вам помогут. '
    else:
        text = 'Что-то ещё? Выберите подсказку /Контакты, чтобы узнать о нас больше!'
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('start')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=20)
    context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)


def info(update, context):
    txt = 'role: user'
    if context.chat_data['keyboard'].is_admin():
        txt = ' role: admin'
    context.bot.send_message(text=get_info(update) + txt, chat_id=update.message.chat_id)


def get_info(update):
    id = update['message']['chat']['id']
    try:
        name = update['message']['chat']['first_name']
        if not name:
            name = ''
    except KeyError:
        name = ''
    try:
        surname = update['message']['chat']['last_name']
        if not surname:
            surname = ''
    except KeyError:
        surname = ''
    try:
        nickname = update['message']['chat']['username']
        if not nickname:
            nickname = ''
    except KeyError:
        nickname = ''
    time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    return surname + ' ' + name + ' (user_id' + str(id) + ' - ' + nickname + ') - ' + ' '.join(str(time).split())


def back(update, context):
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].nextlevel -= 2
    context.chat_data['keyboard'].create('next')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=20)
    context.bot.send_message(text='Предлагаем выбрать из этих.', chat_id=update.message.chat_id,
                             reply_markup=markup)


def nex(update, context):
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('next')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=20)
    context.bot.send_message(text='Предлагаем выбрать из этих.', chat_id=update.message.chat_id,
                             reply_markup=markup)


def registration(update, context):
    message = update.message.text
    weekday = message.split()[-1]
    context.chat_data['keyboard'].set_time(weekday)
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('registration')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=20)
    context.bot.send_message(text='Когда бы вы могли подойти?', chat_id=update.message.chat_id,
                             reply_markup=markup)


def appointment(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    if 'Назад к неделе' not in update['message']['text']:
        text = 'Выберите день для записи, и я подскажу, что делать дальше.'
    else:
        text = 'Выберите другой день недели!'
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('appointment')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=20)
    context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)


def time(update, context):
    message = update.message.text
    delta = message.split()[-1].split('-')
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].set_range(delta)
    context.chat_data['keyboard'].create('time')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=80)
    context.bot.send_message(text='В какое время Вас ждать?', chat_id=update.message.chat_id,
                             reply_markup=markup)


def task(context):
    job = context.job
    date = ':'.join(''.join(job.name.split(str(job.context))).split(':')[:2])
    context.bot.send_message(job.context, text='Напоминаю, что мы ждем вас {} на приёме!'.format(date))


def sign_out(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].set_context(context.bot_data['users'][context.chat_data['user'].id])
    text = context.chat_data['keyboard'].create('sign_out')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=20)
    context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)


def variant(update, context):
    if update['message']['text'].count(' ') == 5:
        dtm_start = datetime.datetime.strptime(
            ' '.join([update['message']['text'].split()[1], update['message']['text'].split()[3]]), '%Y-%m-%d %H:%M')
        dtm_end = datetime.datetime.strptime(
            ' '.join([update['message']['text'].split()[1], update['message']['text'].split()[5]]), '%Y-%m-%d %H:%M')
        context.chat_data['keyboard'].sign_out(dtm_start, dtm_end)
        reply_keyboard = [['/Главное меню', '/Контакты']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=80)
        for el in context.bot_data['users'][update.message.chat_id]:
            if el[1] == dtm_start and el[2] == dtm_end:
                del context.bot_data['users'][update.message.chat_id][
                    context.bot_data['users'][update.message.chat_id].index(el)]
        current_jobs = context.job_queue.get_jobs_by_name(str(update.message.chat_id)+str(dtm_start))
        for job in current_jobs:
            job.schedule_removal()
        context.bot.send_message(text='Запись отменена надеемся увидеть вас позже!', chat_id=update.message.chat_id,
                                 reply_markup=markup)
    else:
        context.bot.send_message(text='Произошла ошибка, воспользуйтесь подсказкой', chat_id=update.message.chat_id)


def contacts(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    text = 'Немного о нас\n'
    text += context.bot_data['info']['description'] + '\n\n'
    text += 'Наш адреc:\n'
    text += context.bot_data['info']['address'] + '\n\n'
    text += 'Наш номер телефона:\n'
    text += context.bot_data['info']['number'] + '\n\n'
    context.bot.send_message(text=text, chat_id=update.message.chat_id)


def feedback(update, context):
    text = 'Напишите ваши впечатления, после отпрваки отзыв будет отмечен в нашей базе.'
    context.chat_data['feedback'] = True
    context.chat_data['sure'] = False
    context.bot.send_message(text=text, chat_id=update.message.chat_id)


def help(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    text = 'Руководство для пользователей\n\n'
    text += '/Записаться(/appointment) - команда открывает меню для записи на приём. Вы сможете выбрать удобное время и день недели\n'
    text += '/Отменить запись(/sign_out) - команда, которая позволяет отменить запись по какой либо причине\n'
    text += '/Контакты(/contacts) - страничка с информацией об организации\n'
    text += '/Оставить отзыв(/feedback) - позволяет оставить отзыв об оказанной услуге\n'
    text += '/Помощь(/help) - небольшое описание всех команд\n'
    if context.chat_data['keyboard'].is_admin():
        text += '/admin_panel - команда для открытия меню админа\n'
    text += 'В случае, если бот не смог помочь, Вы можете обратиться на прямую.\n'
    text += 'Наш телефон находиться в разделе /contacts .'
    context.bot.send_message(text=text, chat_id=update.message.chat_id)


def book(update, context):
    message = update.message.text
    range = context.chat_data['keyboard'].get_range()
    if context.chat_data['sure']:
        context.chat_data['sure'] = False
        if message == 'Да':
            context.bot_data['users'][context.chat_data['user'].id].append(
                [str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')),
                 datetime.datetime.strptime(str(context.chat_data['keyboard'].timedate).split()[0] + ' ' +
                                            context.chat_data['keyboard'].sure.split('-')[0], '%Y-%m-%d %H:%M'),
                 datetime.datetime.strptime(str(context.chat_data['keyboard'].timedate).split()[0] + ' ' +
                                            context.chat_data['keyboard'].sure.split('-')[1], '%Y-%m-%d %H:%M'),
                 get_info(update)])
            chat_id = update.message.chat_id
            tmd = []
            for el in context.bot_data['users'][context.chat_data['user'].id]:
                if datetime.datetime.today() - datetime.datetime.strptime(el[0],
                                                                          '%d.%m.%Y %H:%M:%S') < datetime.timedelta(
                    hours=1):
                    tmd.append(datetime.datetime.strptime(el[0], '%d.%m.%Y %H:%M:%S'))
            if len(tmd) > 2:
                del context.bot_data['users'][context.chat_data['user'].id][-1]
                reply_keyboard = [['/Главное меню']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=80)
                text = 'Вы записываетесь слишком часто за последний час. Повторите попытку позже или обратитесь на горячую линюю.'
                context.bot.send_message(text=text, chat_id=update.message.chat_id,
                                         reply_markup=markup)
            else:
                due = int((datetime.datetime.strptime((str(context.chat_data['keyboard'].timedate).split()[0] + ' ' + \
                                                       context.chat_data['keyboard'].sure.split('-')[0] + ':00'),
                                                      '%Y-%m-%d %H:%M:%S') - datetime.datetime.today() - datetime.timedelta(
                    hours=1)).total_seconds())
                context.job_queue.run_once(
                    task,
                    due,
                    context=chat_id,
                    name=str(chat_id) + str(datetime.datetime.strptime(str(context.chat_data['keyboard'].timedate).split()[0] + ' ' +
                                            context.chat_data['keyboard'].sure.split('-')[0], '%Y-%m-%d %H:%M'))
                )
                ###
                print(due)
                due = 900
                context.job_queue.run_once(
                    task,
                    due,
                    context=chat_id,
                    name=str(chat_id) + str(datetime.datetime.strptime(str(context.chat_data['keyboard'].timedate).split()[0] + ' ' +
                                            context.chat_data['keyboard'].sure.split('-')[0], '%Y-%m-%d %H:%M'))
                )
                ###
                time = str(context.chat_data['keyboard'].timedate).split()[0] + 'T' + \
                       context.chat_data['keyboard'].sure.split('-')[0] + ':00+03:00'
                timeend = str(context.chat_data['keyboard'].timedate).split()[0] + 'T' + \
                          context.chat_data['keyboard'].sure.split('-')[1] + ':00+03:00'
                calendar.update_event(time, timeend, get_info(update))
                reply_keyboard = [['/Главное меню']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=80)
                text = 'Мы будем вас ждать {}!'.format(
                    str(context.chat_data['keyboard'].timedate.strftime('%d.%m.%Y')) + ' в ' + str(
                        context.chat_data['keyboard'].sure))
                context.chat_data['keyboard'].reset()
                context.bot.send_message(text=text, chat_id=update.message.chat_id,
                                         reply_markup=markup)
        else:
            context.chat_data['keyboard'].reset()
            context.chat_data['keyboard'].create('time')
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=80)
            context.bot.send_message(text='В какое время Вас ждать?', chat_id=update.message.chat_id,
                                     reply_markup=markup)
    elif context.chat_data['feedback']:
        if context.chat_data['user'].id not in context.bot_data['feedbacks'].keys():
            context.bot_data['feedbacks'][context.chat_data['user'].id] = [message]
        else:
            context.bot_data['feedbacks'][context.chat_data['user'].id].append(message)
        context.chat_data['feedback'] = False
        context.bot.send_message(text='Спасибо за отзыв!', chat_id=update.message.chat_id)
    elif '-' in message:
        if message.count(':') == 2:
            if int(message.split(':')[0]) in range:
                context.chat_data['keyboard'].set_sure(message)
                context.chat_data['keyboard'].reset()
                context.chat_data['keyboard'].create('sure')
                reply_keyboard = context.chat_data['keyboard'].keyboard
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=100)
                context.chat_data['sure'] = True
                context.chat_data['feedback'] = False
                context.bot.send_message(text='Уверены, что хотите записаться?', chat_id=update.message.chat_id,
                                         reply_markup=markup)
            else:
                context.bot.send_message(text='Кажется, я Вас не понимаю.', chat_id=update.message.chat_id)
        else:
            context.bot.send_message(text='Кажется, я Вас не понимаю.', chat_id=update.message.chat_id)
    else:
        context.bot.send_message(text='Кажется, я Вас не понимаю.', chat_id=update.message.chat_id)


ch = EditCommandHandler()
ch.extra_handler(book)
dp = updater.dispatcher

##### example.register('старт', start, '!')

dp.add_handler(CommandHandler("start", start, pass_chat_data=True))
ch.register("Старт", start)
dp.add_handler(CommandHandler("main_menu", start, pass_chat_data=True))
ch.register("Главное меню", start)
dp.add_handler(CommandHandler("appointment", appointment, pass_chat_data=True))
ch.register("Записаться", appointment)
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
ch.register("Назад к неделе", appointment)
dp.add_handler(CommandHandler("back_week", appointment, pass_chat_data=True))
ch.register("Назад к расписанию", registration, have_args=True)
dp.add_handler(CommandHandler("back_time", registration, pass_chat_data=True))
ch.register("В", time, have_args=True)
dp.add_handler(CommandHandler("B", time, pass_chat_data=True))
dp.add_handler(CommandHandler("info", info, pass_chat_data=True))
ch.register("Следующая", nex)
dp.add_handler(CommandHandler("next", nex, pass_chat_data=True))
ch.register("Назад", back)
dp.add_handler(CommandHandler("back", back, pass_chat_data=True))
ch.register("Помощь", help)
dp.add_handler(CommandHandler("help", help, pass_chat_data=True))
ch.register("Отменить запись", sign_out)
dp.add_handler(CommandHandler("sign_out", sign_out, pass_chat_data=True))
ch.register("Контакты", contacts)
dp.add_handler(CommandHandler("contacts", contacts, pass_chat_data=True))
ch.register("Оставить отзыв", feedback)
dp.add_handler(CommandHandler("feedback", feedback, pass_chat_data=True))
ch.register("Запись", variant, have_args=True)
dp.add_handler(CommandHandler("variant", variant, pass_chat_data=True))
dp.add_handler(CommandHandler("admin_panel", admin, pass_chat_data=True))

dp.add_handler(CommandHandler("set_description", set_description, pass_chat_data=True))

dp.add_handler(CommandHandler("set_contact_number", set_number, pass_chat_data=True))

dp.add_handler(CommandHandler("set_address", set_address, pass_chat_data=True))

dp.add_handler(CommandHandler("admin", admin_info, pass_chat_data=True))

dp.add_handler(CommandHandler("send_feedbacks", send_feedbacks, pass_chat_data=True))

dp.add_handler(CommandHandler("add_superuser", add_superuser, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("del_superuser", del_superuser, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("user_info", user_info, pass_chat_data=True, pass_args=True))

dp.add_handler(MessageHandler(Filters.text, ch, pass_chat_data=True, pass_job_queue=True))
# dp.add_handler(MessageHandler(Filters.text, book,
#                            pass_job_queue=True,
#                             pass_chat_data=True))

updater.start_polling()
updater.idle()
