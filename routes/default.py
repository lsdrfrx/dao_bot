from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)

from database import DB

from .game import GameStates, preparation

default_router = Router()


class RulesAccept(StatesGroup):
    accepting = State()


@default_router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, db: DB):
    promo_available = db.get_promocode_count() > 0
    await message.answer(
        f"""Приветствуем!

Данный бот предназначен для входного тестирования Игры Магов 2024 от Школы Осознанного Дао.
Для прохождения тестирования нажмите кнопку Старт.

Обращаем ваше внимание, тестирование возможно пройти только один раз.
Вам будет предложено 10 фото людей для диагностики на предмет жив-мёртв. 
На диагностику одного фото отведено 5 минут. 
Минимальное количество правильных ответов для прохождения 7 баллов.

{'Доступно для розыгрыша: ... билетов.' if promo_available else 'К сожалению, билеты для бесплатного участия закончились, но вы все равно можете пройти тестирование.'}""",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Начать")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    await state.set_state(RulesAccept.accepting)


@default_router.message(RulesAccept.accepting, F.text == "Начать")
async def accept_handler(message: Message, state: FSMContext, db: DB):
    if db.user_exists(message.from_user.username):
        await message.answer("Вы уже проходили тестирование, продолжение невозможно")
        await state.clear()
    else:
        await message.answer("Приступим.", reply_markup=ReplyKeyboardRemove())
        db.add_user(message.from_user.username)
        await state.set_state(GameStates.preparation)
        await preparation(message, state, db)


@default_router.message(RulesAccept.accepting)
async def invalid_handler(message: Message, state: FSMContext):
    pass
