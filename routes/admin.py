import json

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, StatesGroupMeta
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)

from database import DB

admin_router = Router()


class AdminStates(StatesGroup):
    menu = State()

    # Загрузка фото
    load_photo = State()
    correct_answer = State()
    add_excludes = State()
    finish_load = State()

    # Добавление промокода
    add_promocode = State()
    promocode_count = State()


@admin_router.message(Command("admin"))
async def admin_handler(message: Message, state: FSMContext):
    await message.answer("Авторизация прошла успешно")
    await state.set_state(AdminStates.menu)
    await menu_handler(message, state)


# Загрузка фото
@admin_router.message(AdminStates.menu, F.text == "Загрузить фото")
async def load_photo(message: Message, state: FSMContext):
    await message.answer(
        "Загрузите необходимое фото",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Отмена")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    await state.set_state(AdminStates.load_photo)


@admin_router.message(
    StateFilter(AdminStates.load_photo),
    StateFilter(AdminStates.add_promocode),
    F.text == "Отмена",
)
async def return_to_menu(message: Message, state: FSMContext):
    await state.set_state(AdminStates.menu)
    await menu_handler(message, state)


@admin_router.message(AdminStates.load_photo, F.photo)
async def download_photo(message: Message, state: FSMContext):
    await state.update_data(
        photo=message.photo[-1],
    )
    await message.answer(
        "Жив человек или мёртв:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Жив"), KeyboardButton(text="Мёртв")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )

    await state.set_state(AdminStates.correct_answer)


@admin_router.message(AdminStates.correct_answer)
async def set_correct_answer(message: Message, state: FSMContext):
    await state.update_data(answer=message.text)
    await state.set_state(AdminStates.add_excludes)
    await add_excludes(message, state)


@admin_router.message(AdminStates.add_excludes)
async def add_excludes(message: Message, state: FSMContext):
    await message.answer(
        "Перечислите ID пользователей, которым нельзя отправлять это фото:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Без исключений")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    await state.set_state(AdminStates.finish_load)


@admin_router.message(AdminStates.finish_load)
async def finish_load(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    photo = data["photo"]
    answer = data["answer"]

    await bot.download(
        photo,
        destination=f"/tmp/dao/{photo.file_id}.jpg",
    )
    with open("/tmp/dao/images.json", "r") as f:
        data = json.load(f)

    data["photos"].append(
        {
            "image_path": f"/tmp/dao/{photo.file_id}.jpg",
            "answer": answer,
            "excludes": message.text.split("\n")
            if message.text != "Без исключений"
            else [],
        }
    )

    with open("/tmp/dao/images.json", "w") as f:
        f.write(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            )
        )

    await message.answer("Фото успешно загружено!")
    await state.set_state(AdminStates.menu)
    await menu_handler(message, state)


@admin_router.message(AdminStates.menu, F.text == "Просмотр участников")
async def list_participants(message: Message, state: FSMContext, db: DB):
    users = db.get_users()
    for user in users:
        await message.answer(
            f"Пользователь {user[1]}:\n{'Тест не пройден' if user[2] is None else f'Правильных ответов: {user[3]}'}",
        )
    await menu_handler(message, state)


@admin_router.message(AdminStates.menu, F.text == "Добавить промокод")
async def add_promocode(message: Message, state: FSMContext):
    await message.answer(
        "Введите промокод:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Отмена")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    await state.set_state(AdminStates.add_promocode)


@admin_router.message(AdminStates.add_promocode)
async def enter_count(message: Message, state: FSMContext):
    await state.update_data(promocode=message.text)
    await message.answer("Введите количество промокодов:")
    await state.set_state(AdminStates.promocode_count)


@admin_router.message(AdminStates.promocode_count)
async def save_promocode(message: Message, state: FSMContext, db: DB):
    data = await state.get_data()
    promocode = data["promocode"]
    try:
        count = int(message.text)
    except TypeError:
        await message.answer("Введено неверное количество.")
        await state.set_state(AdminStates.menu)
        await add_promocode(message, state)

    db.add_promocode(promocode, count)
    await message.answer("Промокод удачно создан!")
    await state.set_state(AdminStates.menu)
    await menu_handler(message, state)


@admin_router.message(AdminStates.menu, F.text == "Выход")
async def exit_handler(message: Message, state: FSMContext):
    await message.answer("Вы успешно покинули админ-панель.")
    await state.clear()


@admin_router.message(AdminStates.menu)
async def menu_handler(message: Message, state: FSMContext):
    await message.answer(
        "Вы находитесь в главном меню админ-панели",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Загрузить фото"),
                    KeyboardButton(text="Просмотр фото"),
                ],
                [KeyboardButton(text="Просмотр участников")],
                [
                    KeyboardButton(text="Добавить промокод"),
                    KeyboardButton(text="Просмотр промокодов"),
                ],
                [KeyboardButton(text="Выход")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
