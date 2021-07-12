import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import CommandHandler, Updater, MessageHandler, Filters
import datetime

from EditedClasses import EditCommandHandler
from lib import Buttons, AccessError
from GoogleCalendar import GoogleCalendar

TOKEN = "1765029934:AAG3PWNX_bBlUtllnaK6ZWKH9fMaEp8fKrs"
REQUEST_KWARGS = {
    'urllib3_proxy_kwargs': {
        'assert_hostname': 'False',
        'cert_reqs': 'CERT_NONE',
        'username': 'user',
        'password': 'password'}
}
updater = Updater(TOKEN, use_context=True,
                  request_kwargs=REQUEST_KWARGS)


class User:
    def __init__(self, user_id, chat_id):
        self.id = user_id
        self.chat = chat_id


calendar = GoogleCalendar()
SUPERUSERS = [921615186]
BANNEDUSERS = []



def admin(update, context):
    try:
        context.bot_data['users'][context.chat_data['user'].id]['info'] = get_info(update, context)
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
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
    /set_timezone <hours> - смена часового пользователя, будьте аккуратно - экспериментальная функция
        по умолчанию - UTC + 03:00
    /set_contact_number <number> - установка номера организации (раздел /contacts)
    /set_address <address> - установка адреса организации (раздел /contacts)
    /data_clear - очистка базы данных от записей, которые прошли по времени
        примечание:
            Очищает пространство на сервере, но мешает собирать статистику, чистка будет производиться автоматически раз в месяц(в ручную вводить не обязательно)
    /get_feedbacks - присылает все составленные отзывы с информацией о пользователе
    
Приятной модерации!
    """
    try:
        if context.chat_data['keyboard'].is_admin():
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
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
                user_reg = context.bot_data['users'][user_id]['events']
                user = context.bot_data['users'][user_id]['info']
                if user_reg:
                    txt += 'Пользователь:\n'
                    txt += user + '\n'
                    txt += 'Записи:\n'
                    for post in user_reg:
                        txt += str(post[0]).split()[0] + ' в ' + ':'.join(
                            str(post[0]).split()[1].split(':')[:2]) + ' - ' + ':'.join(
                            str(post[1]).split()[1].split(':')[:2])
                        txt += '\n'
                    txt += '\n\n'
                else:
                    txt += 'Пользователь:\n'
                    txt += user + '\n'
                    txt += 'Записи отсутствуют\n\n'
            except (IndexError, ValueError):
                for id in context.bot_data['users'].keys():
                    user_reg = context.bot_data['users'][id]['events']
                    user = str(context.bot_data['users'][id]['info'])
                    if user_reg:
                        txt += 'Пользователь:\n'
                        txt += user + '\n'
                        txt += 'Записи:\n'
                        for post in user_reg:
                            txt += str(post[0]).split()[0] + ' в ' + ':'.join(
                                str(post[0]).split()[1].split(':')[:2]) + ' - ' + ':'.join(
                                str(post[1]).split()[1].split(':')[:2])
                            txt += '\n'
                        txt += '\n\n'
                    else:
                        txt += 'Пользователь:\n'
                        txt += user + '\n'
                        txt += 'Записи отсутствуют\n\n'
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def del_superuser(update, context):
    global SUPERUSERS
    try:
        user_id = context.args[0]
        if context.chat_data['keyboard'].is_admin() and int(user_id) != SUPERUSERS[0]:
            if int(user_id) in SUPERUSERS:
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def ban_user(update, context):
    global SUPERUSERS, BANNEDUSERS
    try:
        user_id = context.args[0]
        if context.chat_data['keyboard'].is_admin() and int(user_id) != SUPERUSERS[0]:
            BANNEDUSERS.append(int(user_id))
            context.bot.send_message(
                text='Пользователь добавлен в чёрный список',
                chat_id=update.message.chat_id)
            context.bot.send_message(
                text='Поздравляем с добавлением в чёрный список! Пропишите /start для перезапуска.',
                chat_id=int(user_id))
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def unban_user(update, context):
    global SUPERUSERS, BANNEDUSERS
    try:
        user_id = context.args[0]
        if context.chat_data['keyboard'].is_admin():
            if int(user_id) in BANNEDUSERS:
                del BANNEDUSERS[BANNEDUSERS.index(int(user_id))]
                txt = 'Пользователь успешно удалён из чёрного списка'
            else:
                txt = 'Такого пользователя не существует, проверьте id'
            context.bot.send_message(
                text=txt,
                chat_id=update.message.chat_id)
            context.bot.send_message(
                text='С возвращением, пропишите /start для перезапуска.',
                chat_id=int(user_id))
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def set_timezone(update, context):
    global SUPERUSERS
    try:
        timezone = int(context.args[0])
        if context.chat_data['keyboard'].is_admin():
            ltzn = context.bot_data['tzn']
            context.bot_data['tz'] = datetime.timezone(datetime.timedelta(hours=timezone))
            context.bot_data['tzn'] = timezone
            context.chat_data['keyboard'].set_tz(datetime.timezone(datetime.timedelta(hours=timezone)), timezone)
            for id in context.bot_data['users']:
                context.bot_data['users'][id]['reg_time'] = context.bot_data['users'][id][
                                                                'reg_time'] - datetime.timedelta(
                    hours=ltzn) + datetime.timedelta(hours=timezone)
                for event in context.bot_data['users'][id]['events']:
                    event[0] = event[0] - datetime.timedelta(hours=ltzn) + datetime.timedelta(hours=timezone)
                    event[1] = event[1] - datetime.timedelta(hours=ltzn) + datetime.timedelta(hours=timezone)
                    event[2] = event[2] - datetime.timedelta(hours=ltzn) + datetime.timedelta(hours=timezone)
                context.bot_data['users'][id]['info'] = get_info(update, context)
            context.bot.send_message(
                text='Часовой пояс был успешно изменён. База данных обновлена. UTC+{}:00'.format(timezone),
                chat_id=update.message.chat_id)
        else:
            raise AccessError
    except AccessError:
        context.bot.send_message(
            text='Ошибка доступа. У вас недостаточно привелегий.',
            chat_id=update.message.chat_id)
    except (IndexError, ValueError):
        context.bot.send_message(
            text='Использование: /set_timezone <int: hours + UTC>\n default: UTC+03:00 MSK+00:00',
            chat_id=update.message.chat_id)
    except Exception:
        context.bot.send_message(
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def send_feedbacks(update, context):
    try:
        if context.chat_data['keyboard'].is_admin():
            if context.bot_data['feedbacks']:
                text = 'Отзывы:\n\n'
                for key in context.bot_data['feedbacks']:
                    for post in context.bot_data['feedbacks'][key]:
                        text += post + '\n'
                    text += context.bot_data['users'][key]['info'] + '\n\n'
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def set_description(update, context):
    try:
        if context.chat_data['keyboard'].is_admin():
            mes = context.args[0]
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def set_number(update, context):
    try:
        if context.chat_data['keyboard'].is_admin():
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
            chat_id=update.message.chat_id)


def set_address(update, context):
    try:
        if context.chat_data['keyboard'].is_admin():
            mes = context.args[0]
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
            text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start ',
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
    if update:
        variable = context
        context = update
        update = variable
    txt = 'data_clear:\n'
    counter = 0
    valid = 0
    for id in context.bot_data['users'].keys():
        for event in context.bot_data['users'][id]['events']:
            valid += 1
            if event[0] < datetime.datetime.today():
                counter += 1
                del context.bot_data['users'][id]['events'][context.bot_data['users'][id]['events'].index(event)]
    txt += '{} posts has deleted.\n'.format(counter)
    txt += '{} posts has checked.\n'.format(valid)
    if update:
        context.bot.send_message(text=txt, chat_id=update.message.chat_id)
    else:
        print(txt)


def start(update, context):
    global SUPERUSERS, calendar, BANNEDUSERS

    try:
        if 'Главное меню' not in update['message']['text'] and 'main_menu' not in update['message']['text']:
            if 'user' not in context.chat_data.keys():
                context.chat_data['user'] = User(update['message']['chat']['id'], update.message.chat_id)
            if context.chat_data['user'].id in BANNEDUSERS:
                raise AccessError(context, update.message.chat_id)
            if 'users' not in context.bot_data.keys():
                context.bot_data['tz'] = datetime.timezone(datetime.timedelta(hours=3))
                context.bot_data['tzn'] = 3
                context.job_queue.run_monthly(data_clear, when=datetime.time(5), day=15, context=context)
                context.bot_data['users'] = {context.chat_data['user'].id: {
                    'reg_time': datetime.datetime.strptime(
                        datetime.datetime.now(tz=context.bot_data['tz']).strftime('%H:%M %d.%m.%Y'),
                        '%H:%M %d.%m.%Y'),
                    'events': [],
                    'phone': 0,
                    'info': get_info(update, context)}}
            else:
                if context.chat_data['user'].id not in context.bot_data['users'].keys():
                    context.bot_data['users'][context.chat_data['user'].id] = {
                        'reg_time': datetime.datetime.strptime(
                            datetime.datetime.now(tz=context.bot_data['tz']).strftime('%H:%M %d.%m.%Y'),
                            '%H:%M %d.%m.%Y'),
                        'events': [],
                        'phone': 0,
                        'info': get_info(update, context)}
                else:
                    context.bot_data['users'][context.chat_data['user'].id]['info'] = get_info(update, context)
            if 'feedbacks' not in context.bot_data.keys():
                context.bot_data['feedbacks'] = {}
            if 'info' not in context.bot_data.keys():
                context.bot_data['info'] = {'description': 'Я очень известный кто-то приходите ко мне',
                                            'number': '80000000000', 'address': 'Москва, ул. Пушкина'}
            context.chat_data['keyboard'] = Buttons()
            context.chat_data['keyboard'].set_calendar(calendar)
            context.chat_data['keyboard'].set_tz(context.bot_data['tz'], context.bot_data['tzn'])
            if context.chat_data['user'].id in SUPERUSERS:
                context.chat_data['keyboard'].admin_panel()

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
            context.chat_data['feedback'] = False
            context.chat_data['phone'] = False
            context.chat_data['cancel'] = False
            context.chat_data['change_phone'] = False
        context.chat_data['keyboard'].reset()
        context.chat_data['keyboard'].create('start')
        reply_keyboard = context.chat_data['keyboard'].keyboard
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True,
                                     input_field_placeholder='Выберите действие из подсказок')
        context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)
    except AccessError:
        pass


def info(update, context):
    context.chat_data['change_phone'] = False
    context.bot.send_message(text=get_info(update, context), chat_id=update.message.chat_id,
                             parse_mode=telegram.ParseMode.MARKDOWN)


def get_info(update, context):
    global BANNEDUSERS

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
    if 'users' in context.bot_data.keys():
        if context.chat_data['user'].id in context.bot_data['users'].keys():
            phone = context.bot_data['users'][id]['phone']
            date = context.bot_data['users'][id]['reg_time'].strftime('%d.%m.%Y в %H:%M')
            date += ' UTC+{}:00'.format(str(context.bot_data['tzn']))
        else:
            phone = 0
            date = datetime.datetime.now(tz=context.bot_data['tz']).strftime('%d.%m.%Y в %H:%M')
            date += ' UTC+{}:00'.format(str(context.bot_data['tzn']))
    else:
        phone = 0
        date = datetime.datetime.now(tz=context.bot_data['tz']).strftime('%d.%m.%Y в %H:%M')
        date += ' UTC+{}:00'.format(str(context.bot_data['tzn']))
    txt = surname + ' ' + name + '\n'
    link = """{}""".format(str(id))
    txt += 'user_id - ' + '{}'.format(link) + (' - ' + nickname + '\n') if nickname else 'user_id - {}\n'.format(link)
    txt += ('phone: ' + str(phone) + '\n') if phone else 'phone number is not specified\n'
    txt += 'Дата регистрации:\n'
    txt += date + '\n'
    if 'keyboard' in context.chat_data.keys():
        if context.chat_data['keyboard'].is_admin():
            txt += 'role: admin\n'
        else:
            txt += 'role: user {}\n'.format('banned' if id in BANNEDUSERS else 'active')
    else:
        txt += 'role: user {}\n'.format('banned' if id in BANNEDUSERS else 'active')
    return txt


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


def registration(update, context):
    message = update.message.text
    weekday = message.split()[-1]
    context.chat_data['keyboard'].set_time(weekday)
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('registration')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text='Когда бы вы могли подойти?', chat_id=update.message.chat_id,
                             reply_markup=markup)


def appointment(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    context.chat_data['phone'] = False
    if 'Назад к неделе' not in update['message']['text']:
        text = 'Выберите день для записи, и я подскажу, что делать дальше.'
    else:
        text = 'Выберите другой день недели!'
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('appointment')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)


def time(update, context):
    message = update.message.text
    delta = message.split()[-1].split('-')
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].set_range(delta)
    context.chat_data['keyboard'].create('time')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
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
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text=text, chat_id=update.message.chat_id, reply_markup=markup)


def account(update, context):
    context.chat_data['feedback'] = False
    context.chat_data['sure'] = False
    context.chat_data['keyboard'].reset()
    context.chat_data['keyboard'].create('account')
    reply_keyboard = context.chat_data['keyboard'].keyboard
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
    context.bot.send_message(text='Добро пожаловать в личный кабинет! Узнайте статус или смените номер.',
                             chat_id=update.message.chat_id, reply_markup=markup)


def variant(update, context):
    if update['message']['text'].count(' ') == 5:
        dtm_start = datetime.datetime.strptime(
            ' '.join([update['message']['text'].split()[1], update['message']['text'].split()[3]]), '%d.%m.%Y %H:%M')
        dtm_end = datetime.datetime.strptime(
            ' '.join([update['message']['text'].split()[1], update['message']['text'].split()[5]]), '%d.%m.%Y %H:%M')
        context.chat_data['keyboard'].sign_out(dtm_start, dtm_end)
        reply_keyboard = [['/Контакты', '/Главное меню']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
        for el in context.bot_data['users'][update.message.chat_id]['events']:
            if el[0] == dtm_start and el[1] == dtm_end:
                del context.bot_data['users'][update.message.chat_id]['events'][
                    context.bot_data['users'][update.message.chat_id]['events'].index(el)]
        current_jobs = context.job_queue.get_jobs_by_name(str(update.message.chat_id) + str(dtm_start))
        for job in current_jobs:
            job.schedule_removal()
        context.bot.send_message(text='Запись отменена надеемся увидеть вас позже!', chat_id=update.message.chat_id,
                                 reply_markup=markup)
    else:
        context.bot.send_message(text='Произошла ошибка, воспользуйтесь подсказкой', chat_id=update.message.chat_id)


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


def feedback(update, context):
    text = 'Напишите ваши впечатления, после отпрваки отзыв будет отмечен в нашей базе.'
    context.chat_data['feedback'] = True
    context.chat_data['sure'] = False
    context.chat_data['change_phone'] = False
    context.bot.send_message(text=text, chat_id=update.message.chat_id)


def help(update, context):
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
        'keyboard'].is_admin() else '\n')
    context.bot.send_message(text=text, chat_id=update.message.chat_id)


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


def share_contact(update, context):
    context.bot_data['users'][context.chat_data['user'].id]['phone'] = update.message.contact.phone_number
    context.bot_data['users'][context.chat_data['user'].id]['info'] = get_info(update, context)
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


def book(update, context):
    message = update.message.text
    range = context.chat_data['keyboard'].get_range()
    if context.chat_data['sure']:
        context.chat_data['sure'] = False
        if message == 'Да':
            context.bot_data['users'][context.chat_data['user'].id]['events'].append(
                [datetime.datetime.strptime(str(context.chat_data['keyboard'].timedate).split()[0] + ' ' +
                                            context.chat_data['keyboard'].sure.split('-')[0], '%Y-%m-%d %H:%M'),
                 datetime.datetime.strptime(str(context.chat_data['keyboard'].timedate).split()[0] + ' ' +
                                            context.chat_data['keyboard'].sure.split('-')[1], '%Y-%m-%d %H:%M'),
                 datetime.datetime.strptime(datetime.datetime.now(tz=context.bot_data['tz']).strftime('%H:%M %d.%m.%Y'),
                                            '%H:%M %d.%m.%Y')])
            context.bot_data['users'][context.chat_data['user'].id]['info'] = get_info(update, context)
            chat_id = update.message.chat_id
            tmd = []
            for el in context.bot_data['users'][context.chat_data['user'].id]['events']:
                ddt = datetime.datetime.strptime(
                    str(datetime.datetime.now(tz=context.bot_data['tz']).isoformat().split('+')[0].split('.')[0]),
                    '%Y-%m-%dT%H:%M:%S')
                elm = datetime.datetime.strptime(str(el[2].isoformat().split('+')[0].split('.')[0]),
                                                 '%Y-%m-%dT%H:%M:%S')
                if ddt - elm < datetime.timedelta(hours=1):
                    tmd.append(el[0])
            if len(tmd) > 2:
                del context.bot_data['users'][context.chat_data['user'].id]['events'][-1]
                reply_keyboard = [['/Главное меню']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
                text = 'Вы записываетесь слишком часто за последний час. Повторите попытку позже или обратитесь на горячую линюю.'
                context.bot.send_message(text=text, chat_id=update.message.chat_id,
                                         reply_markup=markup)
            else:
                due = int((datetime.datetime.strptime((str(context.chat_data['keyboard'].timedate).split()[0] + ' ' + \
                                                       context.chat_data['keyboard'].sure.split('-')[0] + ':00'),
                                                      '%Y-%m-%d %H:%M:%S') - ddt - datetime.timedelta(
                    hours=1)).total_seconds())
                context.job_queue.run_once(
                    task,
                    due,
                    context=chat_id,
                    name=str(chat_id) + str(
                        datetime.datetime.strptime(str(context.chat_data['keyboard'].timedate).split()[0] + ' ' +
                                                   context.chat_data['keyboard'].sure.split('-')[0], '%Y-%m-%d %H:%M'))
                )
                time = str(context.chat_data['keyboard'].timedate).split()[0] + 'T' + \
                       context.chat_data['keyboard'].sure.split('-')[0] + ':00+{}:00'.format(
                    str(context.bot_data['tzn']) if context.bot_data['tzn'] > 9 else '0' + str(context.bot_data['tzn']))
                timeend = str(context.chat_data['keyboard'].timedate).split()[0] + 'T' + \
                          context.chat_data['keyboard'].sure.split('-')[1] + ':00+{}:00'.format(
                    str(context.bot_data['tzn']) if context.bot_data['tzn'] > 9 else '0' + str(context.bot_data['tzn']))
                calendar.update_event(time, timeend, '\n'.join(get_info(update, context).split('\n')[:5]))
                reply_keyboard = [['/Главное меню']]
                markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
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
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.bot.send_message(text='В какое время Вас ждать?', chat_id=update.message.chat_id,
                                     reply_markup=markup)
    elif context.chat_data['feedback']:
        if context.chat_data['user'].id not in context.bot_data['feedbacks'].keys():
            context.bot_data['feedbacks'][context.chat_data['user'].id] = [message]
        else:
            context.bot_data['feedbacks'][context.chat_data['user'].id].append(message)
        context.chat_data['feedback'] = False
        context.bot.send_message(text='Спасибо за отзыв!', chat_id=update.message.chat_id)
    elif '-' in message or context.chat_data['after_phone']:
        if message.count(':') == 2:
            if int(message.split(':')[0]) in range:
                context.chat_data['keyboard'].set_sure(message)
                context.chat_data['keyboard'].reset()
                if context.bot_data['users'][context.chat_data['user'].id]['phone']:
                    context.chat_data['keyboard'].create('sure')
                    reply_keyboard = context.chat_data['keyboard'].keyboard
                    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
                    context.chat_data['sure'] = True
                    context.chat_data['feedback'] = False
                    context.chat_data['phone'] = False
                    context.chat_data['cancel'] = False
                    context.bot.send_message(text='Уверены, что хотите записаться?', chat_id=update.message.chat_id,
                                             reply_markup=markup)
                else:
                    context.chat_data['sure'] = False
                    context.chat_data['phone'] = True
                    context.chat_data['feedback'] = False
                    context.chat_data['cancel'] = False
                    context.chat_data['keyboard'].reset()
                    markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton('/Ввести в ручную')], [
                        KeyboardButton('/Отправить свой контакт\n(рекомендуем)',
                                       request_contact=True)]],
                                                 one_time_keyboard=False, resize_keyboard=True)
                    context.bot.send_message(text='Выберите вариант ввода телефона.',
                                             chat_id=update.message.chat_id, reply_markup=markup)
            else:
                context.bot.send_message(text='Кажется, я Вас не понимаю.', chat_id=update.message.chat_id)
        else:
            context.bot.send_message(text='Кажется, я Вас не понимаю.', chat_id=update.message.chat_id)
    elif context.chat_data['phone']:
        context.chat_data['keyboard'].reset()
        context.chat_data['phone'] = False
        if correct_mobile(message):
            context.chat_data['after_phone'] = True
            context.chat_data['cancel'] = False
            context.chat_data['keyboard'].create('sure')
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.chat_data['sure'] = True
            context.chat_data['feedback'] = False
            context.chat_data['phone'] = False
            context.bot_data['users'][context.chat_data['user'].id]['phone'] = message
            context.bot_data['users'][context.chat_data['user'].id]['info'] = get_info(update, context)
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
        if message == 'Да':
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
        if message == 'Да':
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
        if correct_mobile(message):
            reply_keyboard = context.chat_data['keyboard'].keyboard
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)
            context.chat_data['feedback'] = False
            context.bot_data['users'][context.chat_data['user'].id]['phone'] = message
            context.bot_data['users'][context.chat_data['user'].id]['info'] = get_info(update, context)
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
    else:
        context.bot.send_message(text='Кажется, я Вас не понимаю.', chat_id=update.message.chat_id)


ch = EditCommandHandler()
ch.extra_handler(book)
dp = updater.dispatcher

##### example.register('старт', start, '!')
dp.add_handler(CommandHandler("set_timezone", set_timezone, pass_chat_data=True))
ch.register("Статус", info)

ch.register("Сменить телефон", change_phone)
dp.add_handler(CommandHandler("start", start, pass_chat_data=True))
ch.register("Старт", start)
ch.register("старт", start)
ch.register("Ввести в ручную", self_contact)
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
ch.register("Личный кабинет", account)
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
dp.add_handler(CommandHandler("cancel", sign_out, pass_chat_data=True))
ch.register("Контакты", contacts)
dp.add_handler(CommandHandler("contacts", contacts, pass_chat_data=True))
ch.register("Оставить отзыв", feedback)
dp.add_handler(CommandHandler("feedback", feedback, pass_chat_data=True))
ch.register("Запись", variant, have_args=True)
dp.add_handler(CommandHandler("variant", variant, pass_chat_data=True))
dp.add_handler(CommandHandler("admin_panel", admin, pass_chat_data=True))

dp.add_handler(CommandHandler("set_description", set_description, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("set_contact_number", set_number, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("set_address", set_address, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("admin", admin_info, pass_chat_data=True))

dp.add_handler(CommandHandler("get_feedbacks", send_feedbacks, pass_chat_data=True))

dp.add_handler(CommandHandler("add_superuser", add_superuser, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("del_superuser", del_superuser, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("ban_user", ban_user, pass_chat_data=True, pass_args=True))
dp.add_handler(CommandHandler("data_clear", data_clear, pass_chat_data=True))
dp.add_handler(CommandHandler("unban_user", unban_user, pass_chat_data=True, pass_args=True))

dp.add_handler(CommandHandler("user_info", user_info, pass_chat_data=True, pass_args=True))
dp.add_handler(MessageHandler(Filters.contact, share_contact, pass_chat_data=True))
dp.add_handler(MessageHandler(Filters.text, ch, pass_chat_data=True, pass_job_queue=True))
# dp.add_handler(MessageHandler(Filters.text, book,
#                            pass_job_queue=True,
#                             pass_chat_data=True))

updater.start_polling()
updater.idle()
