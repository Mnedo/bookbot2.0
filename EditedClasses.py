class EditCommandHandler:
    """
    Создайте экземпляр класса
    example = EditCommandHandler()
    Используйте register, чтобы добавить команды
    example.register('старт', start, '!')
    Добавьте MessageHandler с текстовым фильтером и используйте команды на русском по полной
    updater.dispatcher.add_handler(MessageHandler(Filters.text, example))
    """

    def __init__(self):
        """
        Инициализация класса
        """
        self.commands = []
        self.func = False
        self.func_hnd = ''

    def extra_handler(self, func):
        self.func = True
        self.func_hnd = func

    def register(self, command_name, func_handler, command_smb='/', have_args=False):
        """
        :param command_name: имя команды для регистрирования
        :param func_handler: функция обработчик
        :param command_smb: знак для активации команды (по умолчанию /)
        :return: none
        """
        if command_smb not in '/!?#':
            raise ValueError('Команда не может начинаться с этого')
        self.commands.append([command_name, func_handler, command_smb, have_args])

    def handler(self, update, context):
        """
        Обработчик
        :param update: тех параметр telegram
        :param context: тех параметр telegram
        :return: none
        """
        message = update.message.text
        has_used = False
        for smb in self.commands:
            if str(message)[0] == smb[2]:
                if ' ' not in message:
                    if message.split()[0] == str(smb[2]) + str(smb[0]):
                        smb[1](update, context)
                        has_used = True
                        break
                elif str(message).count(' ') == 1:
                    if smb[3]:
                        if str(smb[2]) + str(smb[0]) == message.split()[0]:
                            smb[1](update, context)
                            has_used = True
                            break
                    else:
                        if ' '.join(message.split()[:2]) == str(smb[2]) + str(smb[0]):
                            smb[1](update, context)
                            has_used = True
                            break
                elif str(message).count(' ') == 2:
                    if smb[3]:
                        if str(smb[2]) + str(smb[0]) == ' '.join(message.split()[:2]):
                            smb[1](update, context)
                            has_used = True
                            break
                    else:
                        if ' '.join(message.split()[:3]) == str(smb[2]) + str(smb[0]):
                            smb[1](update, context)
                            has_used = True
                            break
                elif str(message).count(' ') == 3:
                    if smb[3]:
                        if str(smb[2]) + str(smb[0]) == ' '.join(message.split()[:3]):
                            smb[1](update, context)
                            has_used = True
                            break
                elif str(message).count(' ') == 5:
                    if smb[3]:
                        if str(smb[2]) + str(smb[0]) == message.split()[0]:
                            smb[1](update, context)
                            has_used = True
                            break
        if self.func and not has_used:
            self.func_hnd(update, context)

    def __call__(self, *args):
        """
        :param args: содержит объекты, которые передаются в обрабатывающую фугкцию
        :return: none
        """
        try:
            self.handler(args[0], args[1])
        except Exception as error:
            print(error)
            args[1].bot.send_message(
                text='Произошла ошибка, попробуйте ещё раз. Если ошибка повторится, введите /start .',
                chat_id=args[0].message.chat_id)
