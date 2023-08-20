import sqlite3 as sql
from aiogram import types


def start_sql():
    global base, cur
    base = sql.connect('user_base.db')
    cur = base.cursor()
    if base:
        print('Yeeeeeee connected')
    base.commit()


async def add_user(m: types.Message):
    global base, cur
    base.execute('CREATE TABLE IF NOT EXISTS {}(model, by, prod_year, input, electricity, itog_cost)'.format(m.from_user.username))
    base.commit()


async def add_info(m: types.Message, state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO {} VALUES(?, ?, ?, ?, ?, ?)'.format(m.from_user.username), tuple(data.values()))
        base.commit()


def sql_read(username):
    return cur.execute('SELECT * FROM {}'.format(username)).fetchall()


async def sql_clear(username):
    cur.execute('DELETE FROM {}'.format(username))
    base.commit()
