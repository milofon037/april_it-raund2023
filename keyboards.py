from aiogram import types


start_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
start_menu.add(types.KeyboardButton(text='Добавить новое серверное оборудование'))
start_menu.add(types.KeyboardButton(text='Мой список оборудования'))
start_menu.add(types.KeyboardButton(text='Отмена'))


my_servers = types.InlineKeyboardMarkup(row_width=1)

