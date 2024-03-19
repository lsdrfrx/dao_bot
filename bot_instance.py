from aiogram import Bot


def create_bot_instance(token: str) -> Bot:
    return Bot(
        token=token,
        parse_mode="HTML",
    )
