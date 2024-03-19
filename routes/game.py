import asyncio
import json
import os
import random
from threading import Timer

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, StatesGroupMeta
from aiogram.types import (FSInputFile, KeyboardButton, Message,
                           ReplyKeyboardMarkup, ReplyKeyboardRemove)

from database import DB

game_router = Router()


class GameStates(StatesGroup):
    preparation = State()
    game = State()
    finish = State()


@game_router.message(GameStates.preparation)
async def preparation(message: Message, state: FSMContext, db: DB):
    with open("/tmp/dao/images.json", "r") as f:
        data = json.load(f)

    items = random.choices(data["photos"], k=3)
    await state.update_data(
        photos=items,
        answer=None,
        correct=0,
        timer=None,
    )
    await state.set_state(GameStates.game)
    await game_loop(message, state, db)


@game_router.message(GameStates.game, F.text)
async def game_loop(message: Message, state: FSMContext, db: DB):
    data = await state.get_data()

    if data.get("timer", False):
        data["timer"].cancel()

    if data.get("answer", False):
        if data["answer"] == message.text:
            await state.update_data(correct=data["correct"] + 1)

    if len(data["photos"]) == 0:
        await state.set_state(GameStates.finish)
        await finish_game(message, state, db)
        return

    photo = data["photos"][0]

    image_path = photo["image_path"]
    answer = photo["answer"]

    photo = FSInputFile(image_path)

    await message.answer_photo(
        photo,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Жив"),
                    KeyboardButton(text="Пропустить"),
                    KeyboardButton(text="Мёртв"),
                ],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )

    loop = asyncio.get_event_loop()

    def wrapper(message, state, db, loop):
        asyncio.set_event_loop(loop)
        loop.create_task(timeout(message, state, db))

    timer = Timer(
        300.0,
        wrapper,
        args=[message, state, db, loop],
    )

    timer.start()
    data["photos"].pop(0)
    await state.update_data(
        answer=answer,
        timer=timer,
        photos=data["photos"],
    )


@game_router.message(GameStates.game)
async def timeout(message: Message, state: FSMContext, db: DB):
    await message.answer("Время на ответ истекло.")
    await state.update_data(answer=None)
    await game_loop(message, state, db)


@game_router.message(GameStates.finish)
async def finish_game(message: Message, state: FSMContext, db: DB):
    data = await state.get_data()
    correct = data["correct"]
    if correct >= 7:
        promocode = db.issue_promocode()
        if promocode is not None:
            await message.answer(
                f"""Поздравляем!

Вы набрали {correct} верных ответов из 10!
Ваш промокод на бесплатное участие в Игре Магов {promocode}
Просим обратиться к секретарю Школы для добавления в чат мероприятия @sup_iz_chaosa
Ответы на фото будут высланы автоматически после ...марта."""
            )
        else:
            await message.answer(
                f"""Поздравляем!

Вы набрали {correct} верных ответов из 10!
Просим обратиться к секретарю Школы для добавления в чат мероприятия @sup_iz_chaosa
Ответы на фото будут высланы автоматически после ...марта."""
            )
    else:
        await message.answer(
            f"""Вы набрали {correct} баллов из 10.
К сожалению, этого количества баллов недостаточно для бесплатного участия.

Приглашаем на Игру Магов, где вы сможете повысить свой уровень экстрасенсорных способностей и научиться разным техникам диагностики по темам жив/мёртв, профессии, связи, территории, карты Зенера, а также принять участие в розыгрыше призов среди лучших диагностов!

Подать заявку на участие можно через секретаря школы @sup_iz_chaosa"""
        )

    await state.clear()
