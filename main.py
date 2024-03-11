import asyncio
import logging
import datetime
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import StatesGroup, State

from config import ETHERSCAN_API_KEY, ADMIN_CHAT_ID, CHANNEL_ID, TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


class MyState(StatesGroup):
    M1 = State()


@dp.message_handler(commands=['interval'])
async def interval_command(message: types.Message):
    await message.answer("Введите новый интервал в секундах, к примеру час - 3600 секунд, минута - 60 секунд. "
                         "\nНапишите просто цифру")
    await MyState.M1.set()


@dp.message_handler(state=MyState.M1)
async def get_interval(message: types.Message, state: FSMContext):
    answer = message.text
    global INTERVAL
    INTERVAL = int(answer)
    await message.answer(f"Новый интервал - {INTERVAL} секунд")
    await state.finish()


async def on_start(_):
    chat_id = _.from_user.id
    photo = open('original.jpg', 'rb')
    await bot.send_photo(chat_id, photo, caption='⛽Привествую!⛽')
    await bot.send_message(chat_id, text="Бот создан для проверки газа!\n /gas")


async def on_gas_command(message: types.Message):
    url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data['status'] == '1':
        safe_low = data['result']['SafeGasPrice']
        fast = data['result']['FastGasPrice']
        await message.answer(text=f"💎Ethereum💎\n⛽️Gas: {safe_low} - {fast} Gwei⛽️", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Не удалось получить данные о газовых ценах.")


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await on_start(message)


@dp.message_handler(commands=['gas'])
async def gas_command(message: types.Message):
    await on_gas_command(message)


async def send_message_to_admin_on_startup():
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text="GasTracker on da way")


async def schedule_gas_price():
    while True:
        now = datetime.datetime.now().time()
        if datetime.time(10, 00) <= now <= datetime.time(23, 59):
            await check_high_gas()
        await asyncio.sleep(INTERVAL)


async def check_high_gas():
    url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    video = open('cat.mp4', 'rb')
    if data['status'] == '1':
        safe_low = data['result']['SafeGasPrice']
        fast = data['result']['FastGasPrice']
        if int(safe_low) > 39:
            await bot.send_animation(CHANNEL_ID, video, caption=f"❌Stop Work❌\n⛽️Gas: {safe_low} Gwei⛽️")
        elif int(safe_low) < 20:
             await bot.send_message(chat_id=CHANNEL_ID, text=f"💎Wokr💎\n⛽️Gas: {safe_low} - {fast} Gwei⛽️")
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=f"💎Ethereum💎\n⛽️Gas: {safe_low} - {fast} Gwei⛽️")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(send_message_to_admin_on_startup())
    loop.create_task(schedule_gas_price())
    executor.start_polling(dp, skip_updates=True)
