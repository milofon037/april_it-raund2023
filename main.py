from aiogram import executor
from creater_bot import dp


async def start_bot(_):
    print('Online')


async def finish(_):
    print('Offline')


from handlers import user_side

user_side.reg_user_handlers(dp)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=start_bot, on_shutdown=finish)
