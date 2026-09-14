import datetime
import telebot
from telebot import types
from config import TOKEN, ADMIN_USER_IDS
import utils

bot = telebot.TeleBot(TOKEN)
user_data = {}
admin_selected_table = {}

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS


def require_admin(message) -> bool:
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этому разделу.")
        return False
    return True

# Главное меню

@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Записаться в груминг студию")
    if is_admin(message.from_user.id):
        markup.add("📃 Просмотреть Базу данных")
    bot.send_message(chat_id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📝 Записаться в груминг студию")
def zapis_start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    vidy = utils.get_vidy()
    if not vidy:
        bot.send_message(chat_id, "Ошибка: не удалось загрузить виды животных.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for _, name in vidy:
        markup.add(name)
    bot.send_message(chat_id, "Выберите вид животного:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_vid)


def handle_vid(message):
    chat_id = message.chat.id
    user_data[chat_id]['vid'] = message.text
    porody = utils.get_porody_by_vid(message.text)
    if not porody:
        bot.send_message(chat_id, "Ошибка: не удалось загрузить породы.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for _, name in porody:
        markup.add(name)
    bot.send_message(chat_id, "Выберите породу:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_poroda)


def handle_poroda(message):
    chat_id = message.chat.id
    user_data[chat_id]['poroda'] = message.text
    bot.send_message(chat_id, "Введите имя питомца:")
    bot.register_next_step_handler(message, handle_name)


def handle_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text
    bot.send_message(chat_id, "Введите дату рождения питомца (в формате ГГГГ-ММ-ДД):")
    bot.register_next_step_handler(message, handle_birthday)


def handle_birthday(message):
    chat_id = message.chat.id
    try:
        datetime.datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Введите в формате ГГГГ-ММ-ДД, например 2022-05-01.")
        bot.register_next_step_handler(message, handle_birthday)
        return
    user_data[chat_id]['birthday'] = message.text.strip()
    bot.send_message(chat_id, "Введите имя владельца:")
    bot.register_next_step_handler(message, handle_client_name)


def handle_client_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['client_imya'] = message.text
    bot.send_message(chat_id, "Введите фамилию владельца:")
    bot.register_next_step_handler(message, handle_client_familiya)


def handle_client_familiya(message):
    chat_id = message.chat.id
    user_data[chat_id]['client_familiya'] = message.text
    bot.send_message(chat_id, "Введите телефон владельца:")
    bot.register_next_step_handler(message, handle_client_phone)


def handle_client_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]['client_phone'] = message.text
    bot.send_message(chat_id, "Введите email владельца (или '-' если нет):")
    bot.register_next_step_handler(message, handle_client_email)


def handle_client_email(message):
    chat_id = message.chat.id
    user_data[chat_id]['client_email'] = message.text
    bot.send_message(chat_id, "Введите адрес владельца (или '-' если нет):")
    bot.register_next_step_handler(message, handle_client_address)


def handle_client_address(message):
    chat_id = message.chat.id
    user_data[chat_id]['client_address'] = message.text
    uslugi = utils.get_uslugi()
    if not uslugi:
        bot.send_message(chat_id, "Ошибка: не удалось загрузить услуги.")
        return
    markup = types.InlineKeyboardMarkup()
    for id_uslugi, name, price in uslugi:
        markup.add(types.InlineKeyboardButton(f"{name} ({price}₽)", callback_data=f"usluga_{id_uslugi}"))
    markup.add(types.InlineKeyboardButton("Готово", callback_data="uslugi_done"))
    user_data[chat_id]['uslugi'] = []
    bot.send_message(chat_id, "Выберите услугу (можно несколько):", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("usluga_"))
def select_usluga(call):
    chat_id = call.message.chat.id
    id_uslugi = int(call.data.split("_")[1])
    if id_uslugi not in user_data[chat_id]['uslugi']:
        user_data[chat_id]['uslugi'].append(id_uslugi)
    bot.answer_callback_query(call.id, "Услуга добавлена")


@bot.callback_query_handler(func=lambda call: call.data == "uslugi_done")
def uslugi_done(call):
    chat_id = call.message.chat.id
    if not user_data.get(chat_id, {}).get('uslugi'):
        bot.answer_callback_query(call.id, "Выберите хотя бы одну услугу")
        return
    dop = utils.get_dop_materialy()
    markup = types.InlineKeyboardMarkup()
    if dop:
        for id_dop, name, price in dop:
            markup.add(types.InlineKeyboardButton(f"{name} ({price}₽)", callback_data=f"dopmat_{id_dop}"))
    markup.add(types.InlineKeyboardButton("Пропустить", callback_data="dop_skip"))
    markup.add(types.InlineKeyboardButton("Готово", callback_data="dop_done"))
    user_data[chat_id]['dop_materialy'] = []
    bot.send_message(chat_id, "Выберите доп. материалы (если нужно):", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("dopmat_"))
def select_dop(call):
    chat_id = call.message.chat.id
    try:
        id_dop = int(call.data.split("_")[1])
        if id_dop not in user_data[chat_id]['dop_materialy']:
            user_data[chat_id]['dop_materialy'].append(id_dop)
        bot.answer_callback_query(call.id, "Добавлено")
    except ValueError:
        bot.answer_callback_query(call.id, "Ошибка обработки")


def show_date_selection(chat_id, message_for_next_step):
    free_dates = utils.generate_free_dates()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for date in free_dates:
        markup.add(date)
    bot.send_message(chat_id, "Выберите дату для записи:", reply_markup=markup)
    bot.register_next_step_handler(message_for_next_step, handle_selected_date)


@bot.callback_query_handler(func=lambda call: call.data == "dop_skip")
def dop_skip(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id, "Пропущено")
    show_date_selection(chat_id, call.message)


@bot.callback_query_handler(func=lambda call: call.data == "dop_done")
def dop_done(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id, "Материалы выбраны")
    show_date_selection(chat_id, call.message)


def handle_selected_date(message):
    chat_id = message.chat.id
    selected_date = message.text.strip()

    try:
        selected_date_obj = datetime.datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        bot.send_message(chat_id, "Неверный формат даты. Пожалуйста, выберите дату из предложенного списка.")
        return

    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['date'] = selected_date

    all_datetimes = utils.get_occupied_datetimes()
    occupied_times = [dt.time().strftime("%H:%M") for dt in all_datetimes if dt.date() == selected_date_obj]
    all_possible_times = [f"{hour:02d}:00" for hour in range(10, 20)]
    free_times = [t for t in all_possible_times if t not in occupied_times]

    if not free_times:
        bot.send_message(chat_id, "На выбранную дату нет доступных времён. Пожалуйста, выберите другую дату.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for t in free_times:
        markup.add(t)
    bot.send_message(chat_id, f"Вы выбрали дату {selected_date}. Теперь выберите время:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_time_selection)


def handle_time_selection(message):
    chat_id = message.chat.id
    selected_time = message.text.strip()

    try:
        datetime.datetime.strptime(selected_time, "%H:%M")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")
        return

    user_data[chat_id]['time'] = selected_time

    bot.send_message(chat_id, "Записываем в базу данных...")
    try:
        result = utils.save_full_zapis(user_data[chat_id])
        if result:
            bot.send_message(chat_id, result)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("⬅️ Назад в меню")
            bot.send_message(chat_id, "Вы можете вернуться в главное меню:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Произошла ошибка при записи.")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {e}")
    finally:
        user_data.pop(chat_id, None)


@bot.message_handler(func=lambda message: message.text == "⬅️ Назад в меню")
def back_to_main(message):
    start_handler(message)


# АДМИНСКИЙ РАЗДЕЛ

@bot.message_handler(func=lambda message: message.text == "📃 Просмотреть Базу данных")
def db_menu(message):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👁 Просмотр таблиц", "➕ Добавить данные")
    markup.add("🗑 Удалить данные", "✏️ Редактировать данные")
    markup.add("⬅️ Назад в меню")
    bot.send_message(chat_id, "Выберите действие с базой данных:", reply_markup=markup)


def _table_picker_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for table in utils.get_table_names():
        markup.add(table)
    markup.add("⬅️ Назад в меню")
    return markup


@bot.message_handler(func=lambda message: message.text == "👁 Просмотр таблиц")
def view_tables(message):
    if not require_admin(message):
        return
    bot.send_message(message.chat.id, "Выберите таблицу для просмотра:", reply_markup=_table_picker_markup())
    bot.register_next_step_handler(message, handle_table_view)


def handle_table_view(message):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    table = message.text
    if table == "⬅️ Назад в меню":
        return db_menu(message)
    if table not in utils.ALLOWED_TABLES:
        bot.send_message(chat_id, "Таблица не найдена. Попробуйте ещё раз.")
        return
    try:
        columns, rows = utils.get_table_data(table)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при чтении таблицы: {e}")
        return
    if not rows:
        bot.send_message(chat_id, f"Нет данных в таблице {table}.")
        return
    response = f"<b>Содержимое таблицы {table}:</b>\n"
    for row in rows:
        response += str(row) + "\n"
    bot.send_message(chat_id, response[:4000], parse_mode='HTML')


@bot.message_handler(func=lambda message: message.text == "➕ Добавить данные")
def add_data_handler(message):
    if not require_admin(message):
        return
    bot.send_message(message.chat.id, "Выберите таблицу для добавления данных:", reply_markup=_table_picker_markup())
    bot.register_next_step_handler(message, add_data_table_selected)


def add_data_table_selected(message):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    table = message.text
    if table == "⬅️ Назад в меню":
        return db_menu(message)
    if table not in utils.ALLOWED_TABLES:
        bot.send_message(chat_id, "Таблица не найдена. Попробуйте ещё раз.")
        return
    admin_selected_table[chat_id] = table
    columns = utils.get_table_columns(table)
    bot.send_message(
        chat_id,
        f"Введите значения для столбцов через запятую, в этом порядке:\n{', '.join(columns)}",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(message, process_add_data)


def process_add_data(message):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    table = admin_selected_table.get(chat_id)
    columns = utils.get_table_columns(table)
    values = [v.strip() for v in message.text.split(',')]
    if len(values) != len(columns):
        bot.send_message(chat_id, f"Нужно ровно {len(columns)} значений через запятую. Начните заново через меню.")
        return
    data = dict(zip(columns, values))
    try:
        utils.add_data_to_table(table, data)
        bot.send_message(chat_id, "Данные успешно добавлены.")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при добавлении: {e}")


@bot.message_handler(func=lambda message: message.text == "🗑 Удалить данные")
def delete_data_handler(message):
    if not require_admin(message):
        return
    bot.send_message(message.chat.id, "Выберите таблицу для удаления данных:", reply_markup=_table_picker_markup())
    bot.register_next_step_handler(message, delete_data_table_selected)


def delete_data_table_selected(message):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    table = message.text
    if table == "⬅️ Назад в меню":
        return db_menu(message)
    if table not in utils.ALLOWED_TABLES:
        bot.send_message(chat_id, "Таблица не найдена. Попробуйте ещё раз.")
        return
    admin_selected_table[chat_id] = table
    bot.send_message(chat_id, "Введите ID (значение первичного ключа) записи для удаления:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_delete_data)


def process_delete_data(message):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    table = admin_selected_table.get(chat_id)
    row_id = message.text.strip()
    try:
        utils.delete_data_from_table(table, row_id)
        bot.send_message(chat_id, "Запись успешно удалена.")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при удалении: {e}")


@bot.message_handler(func=lambda message: message.text == "✏️ Редактировать данные")
def edit_data_handler(message):
    if not require_admin(message):
        return
    bot.send_message(message.chat.id, "Выберите таблицу для редактирования данных:", reply_markup=_table_picker_markup())
    bot.register_next_step_handler(message, edit_data_table_selected)


def edit_data_table_selected(message):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    table = message.text
    if table == "⬅️ Назад в меню":
        return db_menu(message)
    if table not in utils.ALLOWED_TABLES:
        bot.send_message(chat_id, "Таблица не найдена. Попробуйте ещё раз.")
        return
    admin_selected_table[chat_id] = table
    bot.send_message(chat_id, "Введите ID (значение первичного ключа) записи для редактирования:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, edit_data_record_selected)


def edit_data_record_selected(message):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    table = admin_selected_table.get(chat_id)
    record_id = message.text.strip()
    columns = utils.get_table_columns(table)[1:]  # без первого столбца (ID)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for col in columns:
        markup.add(col)
    markup.add("⬅️ Назад в меню")
    bot.send_message(chat_id, "Выберите поле для редактирования:", reply_markup=markup)
    bot.register_next_step_handler(message, edit_data_field_selected, record_id=record_id)


def edit_data_field_selected(message, record_id):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    field = message.text
    if field == "⬅️ Назад в меню":
        return db_menu(message)
    bot.send_message(chat_id, f"Введите новое значение для поля {field}:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, edit_data_value_entered, record_id=record_id, field=field)


def edit_data_value_entered(message, record_id, field):
    if not require_admin(message):
        return
    chat_id = message.chat.id
    table = admin_selected_table.get(chat_id)
    new_value = message.text.strip()
    try:
        utils.update_table_data(table, record_id, {field: new_value})
        bot.send_message(chat_id, "Данные успешно обновлены.")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка при обновлении: {e}")


if __name__ == '__main__':
    print("Бот запущен")
    bot.polling(none_stop=True)
