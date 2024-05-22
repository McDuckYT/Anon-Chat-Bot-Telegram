import telebot
from telebot import types
import random
import string

bot = telebot.TeleBot("token from botfather")
chats = []
user_chat_mapping = {}
admin_id = id_of_administrator  
group_chat_id = id_of_group  # the private group, where the nicknames of people are shown
channel_id = id_of_channel # the channel where the messages will sent
admin_chat_name = "К администратору"

def generate_chat_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Chat:
    def __init__(self, code, creator_id, name, is_anonymous):
        self.code = code
        self.participants = [creator_id]
        self.name = name
        self.is_anonymous = is_anonymous


admin_chat_exists = False
for chat in chats:
    if chat.name == admin_chat_name:
        admin_chat_exists = True
        break

if not admin_chat_exists:
    admin_chat_code = generate_chat_code()
    admin_chat = Chat(admin_chat_code, admin_id, admin_chat_name, True)
    chats.append(admin_chat)
    user_chat_mapping[admin_id] = admin_chat


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.from_user.id

    bot.send_message(chat_id, f'Привет {message.from_user.first_name}, следи за новостями в @\n/help - информация о боте.')

    # Создание и отправка клавиатуры
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(types.KeyboardButton('/chats'), types.KeyboardButton('/create'))
    markup.row(types.KeyboardButton('/leave'))

    bot.send_message(chat_id, 'Выберите действие:', reply_markup=markup)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, 'Привет! Этот бот предоставляет уникальный опыт чата. Создавайте анонимные или обычные чаты, общайтесь, делясь сообщениями, голосовыми и изображениями. Подпишитесь на канал @, чтобы использовать все функции бота. Приятного общения!')

@bot.message_handler(commands=['create'])
def create_chat(message):
    chat_id = message.from_user.id

    # Проверка подписки на канал (если пользователь не админ)
    if chat_id != admin_id:
        try:
            member = bot.get_chat_member(channel_id, chat_id)
            if member.status != 'member':
                bot.send_message(chat_id, 'Для использования этой команды вы должны быть подписаны на канал!')
                return
        except Exception as e:
            print(e)
            bot.send_message(chat_id, 'Произошла ошибка при проверке подписки. Попробуйте позже.')
            return

    # Код создания чата остается без изменений
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Анонимный чат', callback_data='create_anonymous'))
    markup.add(types.InlineKeyboardButton('Обычный чат', callback_data='create_regular'))
    bot.send_message(chat_id, 'Выберите тип чата:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('create_'))
def callback_create_chat(call):
    chat_id = call.from_user.id
    is_anonymous = call.data.endswith('anonymous')

    markup = types.ForceReply(selective=False)
    bot.send_message(chat_id, 'Введите название чата:', reply_markup=markup)
    bot.register_next_step_handler(call.message, process_chat_name, is_anonymous)

def process_chat_name(message, is_anonymous):
    chat_id = message.from_user.id
    chat_name = message.text.strip()

    if not chat_name:
        bot.send_message(chat_id, 'Название чата не может быть пустым. Пожалуйста, введите действительное название.')
        return

    if any(existing_chat.name.lower() == chat_name.lower() for existing_chat in chats):
        bot.send_message(chat_id, 'Чат с таким названием уже существует. Попробуйте снова /create')
        return

    chat_code = generate_chat_code()
    new_chat = Chat(chat_code, chat_id, chat_name, is_anonymous)
    chats.append(new_chat)
    user_chat_mapping[chat_id] = new_chat
    bot.send_message(chat_id, f'Вы создали {"анонимный" if is_anonymous else "обычный"} чат "{chat_name}"\n\nВы присоединились "{chat_name}"')
    bot.send_message(group_chat_id, f'Пользователь {message.from_user.username} создал чат "{chat_name}"')

    # Отправка клавиатуры после создания чата
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(types.KeyboardButton('/chats'), types.KeyboardButton('/create'))
    markup.row(types.KeyboardButton('/leave'))

    bot.send_message(chat_id, 'Выберите действие:', reply_markup=markup)



@bot.message_handler(commands=['chats'])
def list_chats(message):
    chat_id = message.from_user.id

    if not chats:
        bot.send_message(chat_id, 'Нет активных чатов.\nСтань первым /create\nПопробуй повторить позже /chats')
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Анонимный чат', callback_data='list_anonymous'))
    markup.add(types.InlineKeyboardButton('Обычный чат', callback_data='list_regular'))
    markup.add(types.InlineKeyboardButton('Все чаты', callback_data='list_all'))
    bot.send_message(chat_id, 'Выберите тип чата для поиска:', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('list_'))
def callback_list_chats(call):
    chat_id = call.from_user.id
    chat_type = call.data.split('_')[1]

    if chat_type == 'all':
        is_anonymous = None
        available_chats = chats
    else:
        is_anonymous = chat_type == 'anonymous'
        available_chats = [chat for chat in chats if chat.is_anonymous == is_anonymous]

    if not available_chats:
        bot.send_message(chat_id, f'Нет доступных {"анонимных" if is_anonymous else "обычных"} чатов.')
        return

    markup = types.InlineKeyboardMarkup()
    for chat in available_chats:
        button_text = f'Чат "{chat.name}"'
        callback_data_join = f'join_{chat.code}'
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data_join))

    bot.send_message(chat_id, f'Доступные {"анонимные" if is_anonymous else "обычные"} чаты:', reply_markup=markup)


@bot.message_handler(commands=['leave'])
def leave_chat_command(message):
    chat_id = message.from_user.id

    if chat_id in user_chat_mapping:
        current_chat = user_chat_mapping[chat_id]

        markup = types.InlineKeyboardMarkup()
        button_text = 'Покинуть чат'
        callback_data = f'leave_{current_chat.code}'
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))

        bot.send_message(chat_id, f'Вы уверены, что хотите покинуть чат "{current_chat.name}"?',
                         reply_markup=markup)
    else:
        bot.send_message(chat_id, 'Вы не участвуете в каком-либо чате. Нет чата для покидания.')


@bot.message_handler(commands=['list'])
def list_all_chats(message):
    user_id = message.from_user.id

    if user_id == admin_id:
        if not chats:
            bot.send_message(admin_id, 'Нет активных чатов.')
            return

        for chat in chats:
            if chat.participants:
                chat_info = f'{chat.name}:\n'
                for user_id in chat.participants:
                    user_info = get_user_info(user_id)
                    chat_info += f'{user_info}\n'
                bot.send_message(user_id, chat_info)
            else:
                bot.send_message(user_id, f'В чате "{chat.name}" нет участников.')
    else:
        bot.send_message(user_id, 'У вас нет прав для выполнения этой команды.')

def get_user_info(user_id):
    user = bot.get_chat_member(group_chat_id, user_id).user
    if user.username:
        return f'@{user.username}, {user.first_name} {user.last_name}, {user_id}'
    else:
        return f'{user.first_name} {user.last_name}, {user_id}'


@bot.callback_query_handler(func=lambda call: call.data.startswith('list_'))
def list_chat_participants(call):
    user_id = call.from_user.id
    selected_chat_code = call.data.split('_')[1]

    for chat in chats:
        if selected_chat_code == chat.code:
            if chat.participants:
                chat_info = f'{chat.name}:\n'
                for user in chat.participants:
                    user_info = f'@{user.username}' if user.username else f'{user.first_name} {user.last_name}'
                    chat_info += f'{user_info}, {user.id}.\n'
                bot.send_message(user_id, chat_info)
            else:
                bot.send_message(user_id, f'В чате "{chat.name}" нет участников.')
            return

    bot.send_message(user_id, 'Чат не найден.')




@bot.callback_query_handler(func=lambda call: call.data.startswith('leave_'))
def callback_leave_chat(call):
    chat_id = call.from_user.id
    selected_chat_code = call.data.split('_')[1]

    for chat in chats:
        if selected_chat_code == chat.code:
            if chat_id in chat.participants:
                participant_id = chat_id

                chat.participants.remove(chat_id)
                del user_chat_mapping[chat_id]

                for remaining_id in chat.participants:
                    if chat.is_anonymous:
                        bot.send_message(remaining_id, f'Участник покинул чат "{chat.name}".')
                    else:
                        bot.send_message(remaining_id, f'{call.from_user.first_name} покинул чат "{chat.name}".')

                bot.send_message(chat_id, f'Вы покинули чат "{chat.name}".')

                return

    bot.send_message(chat_id, 'Чат не найден. Возможно, он был удален или вы уже покинули чат.')



@bot.message_handler(commands=['join'])
def join_chat_command(message):
    chat_id = message.from_user.id

    # Проверка, не является ли участник уже участником другого чата
    if chat_id in user_chat_mapping:
        bot.send_message(chat_id, 'Вы уже участвуете в чате. Нельзя присоединяться к другим чатам одновременно.\n/leave')
        return

    markup = types.InlineKeyboardMarkup()
    for chat in chats:
        button_text = f'Присоединиться к чату "{chat.name}"'
        callback_data = f'join_{chat.code}'
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))

    bot.send_message(chat_id, 'Выберите чат для присоединения:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('join_'))
def callback_join_chat(call):
    chat_id = call.message.chat.id
    selected_chat_code = call.data.split('_')[1]

    # Проверка, не является ли участник уже участником другого чата
    if chat_id in user_chat_mapping:
        bot.send_message(chat_id, 'Вы уже участвуете в чате. Нельзя присоединяться к другим чатам одновременно.\n/leave')
        return

    for chat in chats:
        if selected_chat_code == chat.code:
            chat.participants.append(chat_id)
            user_chat_mapping[chat_id] = chat
            participants_count = len(chat.participants)
            bot.send_message(chat_id, f'Вы присоединились к чату "{chat.name}"!\n\n'
                                       f'Теперь в чате {participants_count} участников.\n/leave - чтобы выйти с чата')
            for participant_id in chat.participants:
                if participant_id != chat_id:
                    bot.send_message(participant_id, f'Новый участник присоединился к чату "{chat.name}". '
                                                     f'Теперь в чате {participants_count} участников.')
            return

    bot.send_message(chat_id, 'Чат с указанным кодом не найден.')




@bot.message_handler(commands=['delete'])
def delete_chat_command(message):
    user_id = message.from_user.id

    if user_id == admin_id:
        if chats:
            markup = types.InlineKeyboardMarkup()
            for chat in chats:
                button_text = f'Удалить "{chat.name}"'
                callback_data = f'delete_{chat.code}'
                markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))

            bot.send_message(user_id, 'Выберите чат для удаления:', reply_markup=markup)
        else:
            bot.send_message(user_id, 'Нет активных чатов.')
    else:
        bot.send_message(user_id, 'У вас нет прав для выполнения этой команды.')


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def callback_delete_chat(call):
    user_id = call.from_user.id
    selected_chat_code = call.data.split('_')[1]

    if user_id == admin_id:
        for chat in chats:
            if selected_chat_code == chat.code:
                for participant_id in chat.participants:
                    if participant_id != admin_id:  # Убеждаемся, что админ не удаляет сам себя
                        del user_chat_mapping[participant_id]

                bot.send_message(admin_id, f'Чат "{chat.name}" успешно удален.')
                chats.remove(chat)
                return

        bot.send_message(admin_id, 'Чат не найден.')
    else:
        bot.send_message(user_id, 'У вас нет прав для выполнения этой команды.')



@bot.message_handler(func=lambda message: True, content_types=['text', 'voice', 'video', 'photo', 'audio', 'sticker', 'gif'])
def chat_handler(message):
    chat_id = message.from_user.id

    if chat_id in user_chat_mapping:
        current_chat = user_chat_mapping[chat_id]

        for participant_id in current_chat.participants:
            if participant_id != chat_id:
                if current_chat.is_anonymous:
                    # Добавьте обработку разных типов сообщений здесь
                    if message.content_type == 'text':
                        bot.send_message(participant_id, f'Аноним ({current_chat.name}): {message.text}')
                    elif message.content_type == 'voice':
                        bot.send_voice(participant_id, message.voice.file_id)
                    elif message.content_type == 'video':
                        bot.send_video(participant_id, message.video.file_id)
                    elif message.content_type == 'photo':
                        # Используйте bot.send_photo для обработки фотографий
                        bot.send_photo(participant_id, message.photo[-1].file_id)
                    elif message.content_type == 'audio':
                        bot.send_audio(participant_id, message.audio.file_id)
                    elif message.content_type == 'sticker':
                        bot.send_sticker(participant_id, message.sticker.file_id)
                    # Добавьте обработку других типов сообщений, если необходимо
                else:
                    # Аналогично, добавьте обработку разных типов сообщений для неанонимных чатов
                    if message.content_type == 'text':
                        bot.send_message(participant_id, f'{message.from_user.first_name}: {message.text}')
                    elif message.content_type == 'voice':
                        bot.send_voice(participant_id, message.voice.file_id)
                    elif message.content_type == 'video':
                        bot.send_video(participant_id, message.video.file_id)
                    elif message.content_type == 'photo':
                        # Используйте bot.send_photo для обработки фотографий
                        bot.send_photo(participant_id, message.photo[-1].file_id)
                    elif message.content_type == 'audio':
                        bot.send_audio(participant_id, message.audio.file_id)
                    elif message.content_type == 'sticker':
                        bot.send_sticker(participant_id, message.sticker.file_id)
                    # Добавьте обработку других типов сообщений, если необходимо



bot.infinity_polling()
