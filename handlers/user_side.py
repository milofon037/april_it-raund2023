from creater_bot import bot
from aiogram import types, Dispatcher
from keyboards import start_menu
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from data_base import sqlite_db
from random import randint


START = '''Наш бот предоставляет Вам возможность быстро <b>рассчитать стоимость эксплуатации серверного оборудования и выбрать самый подходящий вариант!</b>
В меню вы можете добавить в свой собственный список серверное оборудование (<i>при добавлении сразу будет выведена стоимость эксплуатации на разные сроки</i>)
Также, открывая там же свой список оборудования, Вы сможете изучить варианты ещё раз и увидеть наиболее экономичный из них(<u>если их более одного</u>)!'''


class FSMNewServer(StatesGroup):
    model = State()
    by = State()
    production_year = State()
    electr_in = State()
    electr_tarif = State()


def chislo(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


# @dp.callback_query_handler(lambda c: c.data and c.data.startswith('server_'))
async def servers(c: types.CallbackQuery):
    number = int(c.data.split('_')[1]) - 1
    if number < 0:
        server = sorted(sqlite_db.sql_read(c.from_user.username), key=lambda x: x[5])[0]
    else:
        server = sqlite_db.sql_read(c.from_user.username)[number]
    await bot.send_message(c.from_user.id,
                           text=f'<b>Модель оборудования:</b> {server[0]}\n'
                                f'<b>Производитель:</b> {server[1]}\n'
                                f'<b>Год выпуска:</b> {server[2]}\n'
                                f'<b>Потребление электроэнергии:</b> {server[3]} кВт\n'
                                f'<b>Стоимость электроэнергии для расчётов:</b> {server[4]} руб/кВт⋅ч\n'
                                f'<b>Стоимость эксплуатации в сутки:</b> {server[5]} руб.',
                           parse_mode="HTML")
    await c.answer()


# @dp.message_handler(commands='start')
async def start(m: types.Message):
    date = int(m.date.hour)
    if date in range(5, 13):
        hello = 'Доброе утро!'
    elif date in range(13, 18):
        hello = 'Добрый день!'
    elif date in range(18, 23):
        hello = 'Добрый вечер!'
    else:
        hello = 'Доброй ночи!'
    await sqlite_db.add_user(m)
    n = str(randint(1, 3))
    with open('photos/server' + n + '.jpg', 'rb') as photo:
        await bot.send_photo(chat_id=m.chat.id, photo=photo, caption=hello + ' ' + START, reply_markup=start_menu,
                             parse_mode="HTML")


# @dp.message_handler(lambda m: m.text == 'Отмена')
async def close(m: types.Message):
    remove = types.ReplyKeyboardRemove()
    await m.answer('Отменено', reply_markup=remove)


# @dp.message_handler(lambda m: m.text == 'Добавить новое серверное оборудование', state=None)
async def add_new(m: types.Message):
    await FSMNewServer.model.set()
    await m.answer('Чтобы добавить в свой список новый сервер, введите ряд запрашиваемых данных:\n\n'
                   '(<b>для выхода из режима заполнения введите</b> /cancel)',
                   parse_mode="HTML")
    await m.answer('Введите модель серверного оборудования...')


# @dp.message_handler(state="*", commands='cancel')
async def cancel_fsm(m: types.Message, state: FSMContext):
    cur_state = await state.get_state()
    if cur_state is None:
        return
    await state.finish()
    await m.answer('Ваше действие было отменено.')


# @dp.message_handler(state=FSMNewServer.model)
async def set_model(m: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['model'] = m.text
    await FSMNewServer.next()
    await m.answer('Введите производителя...')


# @dp.message_handler(state=FSMNewServer.by)
async def set_by(m: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['by'] = m.text
    await FSMNewServer.next()
    await m.answer('Введите год выпуска...')


# @dp.message_handler(state=FSMNewServer.production_year)
async def set_prod_year(m: types.Message, state: FSMContext):
    if m.text.isdigit():
        async with state.proxy() as data:
            data['prod_year'] = m.text
        await FSMNewServer.next()
        await m.answer('Введите потребление оборудованием электроэнергии...\n\n'
                       '(<b>в кВт, <u>только число(если дробное, то в формате 11.037)</u></b>)',
                       parse_mode="HTML")
    else:
        await m.reply('Что-то не так! Попробуйте снова...')
        await FSMNewServer.production_year.set()


# @dp.message_handler(state=FSMNewServer.electr_in)
async def set_cost(m: types.Message, state: FSMContext):
    if chislo(m.text):
        async with state.proxy() as data:
            data['input'] = float(m.text)
        await FSMNewServer.next()
        await m.answer('Введите стоимость электроэнергии или "НЕТ"'
                       '<i>(тогда рассчет будет вестись по средней стоимости: 3 руб/кВт⋅ч)</i>...\n\n'
                       '(<b>в руб/кВт⋅ч, <u>только число(если дробное, то в формате 11.037)</u></b>)',
                       parse_mode="HTML")
    else:
        await m.reply('Что-то не так! Попробуйте снова...')
        await FSMNewServer.electr_in.set()


# @dp.message_handler(state=FSMNewServer.electr_tarif)
async def set_electr(m: types.Message, state: FSMContext):
    if chislo(m.text) or m.text.lower() == 'нет':
        async with state.proxy() as data:
            data['electricity'] = 3.0 if m.text.lower() == 'нет' else float(m.text)
            data['itog_cost'] = round(data['input'] * 24 * data['electricity'], 2)
        await sqlite_db.add_info(m, state)
        await m.answer('Готово!')
        await m.answer(f'''<b>Стоимость в сутки:</b> {data["itog_cost"]} рублей;
<b>В месяц:</b> {round(data["itog_cost"] * 30, 2)} рублей;
<b>В год:</b> {round(data["itog_cost"] * 365, 2)} рублей.''', reply_markup=start_menu, parse_mode="HTML")
        await state.finish()
    else:
        await m.reply('Что-то не так! Попробуйте снова...')
        await FSMNewServer.electr_tarif.set()


# @dp.message_handler(lambda m: m.text == 'Мой список оборудования')
async def spisok_servers(m: types.Message):
    spisok = sqlite_db.sql_read(m.from_user.username)
    if spisok:
        spisok_kb = types.InlineKeyboardMarkup(row_width=2)
        for i in range(len(spisok)):
            spisok_kb.insert(types.InlineKeyboardButton(text='Сервер' + str(i + 1), callback_data='server_' + str(i + 1)))
        if len(spisok) > 1:
            spisok_kb.add(types.InlineKeyboardButton(text='Наиболее экономичное оборудование', callback_data='server_0'))
        spisok_kb.add(types.InlineKeyboardButton(text='Очистить список', callback_data='clear'))
        await m.answer('Ваш список серверного оборудования:', reply_markup=spisok_kb)
    else:
        await m.answer('Ваш список серверного оборудования пуст!')


# @dp.callback_query_handler(lambda c: c.data == 'clear')
async def delete_spisok(c: types.CallbackQuery):
    await sqlite_db.sql_clear(c.from_user.username)
    await c.answer('Ваш список был удалён!', show_alert=True)


# @dp.message_handler()
async def other(m: types.Message):
    await m.answer('Запрос не ясен, попробуйте снова.')


def reg_user_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands='start')
    dp.register_message_handler(close, lambda m: m.text == 'Отмена')
    dp.register_message_handler(add_new, lambda m: m.text == 'Добавить новое серверное оборудование', state=None)
    dp.register_message_handler(cancel_fsm, state="*", commands='cancel')
    dp.register_message_handler(set_model, state=FSMNewServer.model)
    dp.register_message_handler(set_by, state=FSMNewServer.by)
    dp.register_message_handler(set_prod_year, state=FSMNewServer.production_year)
    dp.register_message_handler(set_cost, state=FSMNewServer.electr_in)
    dp.register_message_handler(set_electr, state=FSMNewServer.electr_tarif)
    dp.register_message_handler(spisok_servers, lambda m: m.text == 'Мой список оборудования')
    dp.register_callback_query_handler(servers, lambda c: c.data and c.data.startswith('server_'))
    dp.register_callback_query_handler(delete_spisok, lambda c: c.data == 'clear')
    dp.register_message_handler(other)
